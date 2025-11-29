import openai
import logging
from typing import List, Dict, Any, Optional, Literal
from vector_store import VectorStore
import os
import re
import warnings
from contextlib import redirect_stderr
from io import StringIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Suppress Google Generative AI warnings before importing
os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GLOG_minloglevel'] = '2'
os.environ['ABSL_MIN_LOG_LEVEL'] = '2'

# Suppress tokenizers parallelism warnings
# Set before importing sentence-transformers to avoid forking warnings
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

# Suppress warnings
warnings.filterwarnings('ignore')

# Import google.generativeai
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Supported model providers
ModelProvider = Literal['lm_studio', 'gemini']

# Try to import cross-encoder for neural reranking
try:
    from sentence_transformers import CrossEncoder
    CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CROSS_ENCODER_AVAILABLE = False
    logger.warning("sentence-transformers not available. Falling back to rule-based reranking.")

class RAGChatService:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.client = None
        self.gemini_model = None
        self.model_name = None
        self.base_url = None
        self.provider: ModelProvider = os.getenv('MODEL_PROVIDER', 'lm_studio').lower()  # 'lm_studio' or 'gemini'
        self.generation_config = None
        self.cross_encoder = None
        self.use_neural_reranker = os.getenv('USE_NEURAL_RERANKER', 'true').lower() == 'true'
        
        # Rolling window configuration for conversation history
        self.max_history_messages = int(os.getenv('MAX_HISTORY_MESSAGES', '20'))  # Max number of messages to keep
        self.max_history_chars = int(os.getenv('MAX_HISTORY_CHARS', '8000'))  # Max characters in history
        self.max_message_chars = int(os.getenv('MAX_MESSAGE_CHARS', '2000'))  # Max chars per message
        
        # Context window limits for documents
        self.max_context_chars = int(os.getenv('MAX_CONTEXT_CHARS', '12000'))  # Max characters in document context
        self.max_doc_chars = int(os.getenv('MAX_DOC_CHARS', '2000'))  # Max chars per document (already used)
        
        self._initialize_provider()
        self._initialize_reranker()
    
    def _initialize_provider(self):
        """Initialize the selected model provider"""
        if self.provider == 'gemini':
            self._initialize_gemini()
        else:
            self._initialize_lm_studio()
    
    def _initialize_lm_studio(self):
        """Initialize LM Studio local model client"""
        try:
            # Get LM Studio server URL from environment (default: http://localhost:1234/v1)
            base_url = os.getenv('LM_STUDIO_BASE_URL', 'http://localhost:1234/v1')
            # Ensure base_url ends with /v1 for OpenAI-compatible API
            if not base_url.endswith('/v1'):
                if base_url.endswith('/'):
                    base_url = base_url + 'v1'
                else:
                    base_url = base_url + '/v1'
            self.base_url = base_url
            model_name = os.getenv('LM_STUDIO_MODEL', 'local-model')
            
            # LM Studio doesn't require an API key, but we can use a dummy one
            api_key = os.getenv('LM_STUDIO_API_KEY', 'lm-studio')
            
            # Initialize OpenAI client pointing to LM Studio
            self.client = openai.OpenAI(
                base_url=self.base_url,
                api_key=api_key
            )
            self.model_name = model_name
            self.gemini_model = None  # Clear Gemini model
            
            # Initialize generation config with increased token generation
            self.generation_config = {
                'max_tokens': 8192,  # Increased from default for more comprehensive responses
                'temperature': 0.7,
                'top_p': 0.95,
                'frequency_penalty': 0.0,
                'presence_penalty': 0.0
            }
            
            logger.info(f"LM Studio client initialized successfully (base_url: {self.base_url}, model: {self.model_name}, max_tokens: 8192)")
            
        except Exception as e:
            logger.error(f"Failed to initialize LM Studio client: {str(e)}")
            raise
    
    def _initialize_gemini(self):
        """Initialize Google Generative AI client"""
        try:
            # Get API key from environment
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                logger.error("GEMINI_API_KEY not found in environment variables")
                raise ValueError("GEMINI_API_KEY is required for Gemini provider")
            
            # Configure the client with stderr suppression
            with redirect_stderr(StringIO()):
                genai.configure(api_key=api_key)
            
            # Get model name from environment or use default
            model_name = os.getenv('GEMINI_MODEL', 'models/gemini-flash-lite-latest')
            
            # Initialize generation config with increased token limits
            # Get max_output_tokens from environment or use default (32768 for larger context)
            max_output_tokens = int(os.getenv('GEMINI_MAX_OUTPUT_TOKENS', '32768'))
            generation_config_dict = {
                'max_output_tokens': max_output_tokens,
                'temperature': 0.7,
                'top_p': 0.95,
                'top_k': 40
            }
            
            # Initialize the model with stderr suppression
            with redirect_stderr(StringIO()):
                self.gemini_model = genai.GenerativeModel(
                    model_name,
                    generation_config=generation_config_dict
                )
            self.model_name = model_name
            self.client = None  # Clear OpenAI client
            self.base_url = None
            
            # Store config for reference
            self.generation_config = generation_config_dict
            
            logger.info(f"Google Generative AI initialized successfully (model: {model_name}, max_output_tokens: {max_output_tokens})")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI: {str(e)}")
            raise
    
    def set_provider(self, provider: ModelProvider):
        """Switch between model providers"""
        if provider not in ['lm_studio', 'gemini']:
            raise ValueError(f"Invalid provider: {provider}. Must be 'lm_studio' or 'gemini'")
        
        if self.provider == provider:
            logger.info(f"Provider already set to {provider}")
            return
        
        logger.info(f"Switching model provider from {self.provider} to {provider}")
        self.provider = provider
        self._initialize_provider()
    
    def _initialize_reranker(self):
        """Initialize the neural reranker model"""
        if not self.use_neural_reranker or not CROSS_ENCODER_AVAILABLE:
            logger.info("Using rule-based reranking (neural reranker disabled or unavailable)")
            return
        
        try:
            # Use a lightweight but effective cross-encoder model for reranking
            reranker_model = os.getenv('RERANKER_MODEL', 'cross-encoder/ms-marco-MiniLM-L-6-v2')
            logger.info(f"Initializing neural reranker with model: {reranker_model}")
            self.cross_encoder = CrossEncoder(reranker_model, max_length=512)
            logger.info("Neural reranker initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize neural reranker: {str(e)}. Falling back to rule-based reranking.")
            self.cross_encoder = None
            self.use_neural_reranker = False
    
    def _rerank_documents(self, documents: List[Dict[str, Any]], query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Re-rank documents using neural cross-encoder model (if available) or rule-based scoring
        
        Args:
            documents: List of retrieved documents
            query: User query for keyword matching
            top_k: Number of top documents to return
            
        Returns:
            Re-ranked list of top_k documents
        """
        if not documents:
            return []
        
        # Use neural reranker if available
        if self.cross_encoder and self.use_neural_reranker:
            return self._rerank_with_neural_model(documents, query, top_k)
        else:
            return self._rerank_with_rules(documents, query, top_k)
    
    def _rerank_with_neural_model(self, documents: List[Dict[str, Any]], query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Re-rank documents using neural cross-encoder model"""
        try:
            # Prepare query-document pairs for the cross-encoder
            pairs = []
            for doc in documents:
                # Combine title and content for better context
                metadata = doc.get('metadata', {})
                title = metadata.get('title', '')
                content = doc.get('content', '')
                
                # Smart truncation: prioritize beginning and keep title
                # Cross-encoder max_length is 512 tokens, so we limit to ~400 chars to be safe
                max_content_length = 400
                if len(content) > max_content_length:
                    # Take first part which often contains the most relevant info
                    content = content[:max_content_length] + "..."
                
                # Combine title and content, with title getting priority
                if title:
                    doc_text = f"{title}\n{content}".strip()
                else:
                    doc_text = content.strip()
                
                pairs.append([query, doc_text])
            
            # Get scores from cross-encoder (batch prediction for efficiency)
            scores = self.cross_encoder.predict(pairs)
            
            # Handle both single score and array of scores
            if not isinstance(scores, (list, tuple)):
                scores = [scores] if len(documents) == 1 else scores.tolist()
            
            # Combine scores with documents and sort
            scored_docs = list(zip(scores, documents))
            scored_docs.sort(key=lambda x: x[0], reverse=True)
            
            # Select top_k documents
            reranked = [doc for _, doc in scored_docs[:top_k]]
            
            logger.info(f"Neural re-ranked {len(documents)} documents, selected top {len(reranked)} with scores: {[f'{s:.3f}' for s, _ in scored_docs[:top_k]]}")
            
            return reranked
            
        except Exception as e:
            logger.warning(f"Neural reranking failed: {str(e)}. Falling back to rule-based reranking.")
            return self._rerank_with_rules(documents, query, top_k)
    
    def _rerank_with_rules(self, documents: List[Dict[str, Any]], query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Re-rank documents using rule-based scoring (fallback method)"""
        # Extract keywords from query (simple approach: split and filter)
        query_lower = query.lower()
        query_words = set(re.findall(r'\b\w+\b', query_lower))
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'what', 'which', 'who', 'whom', 'how', 'when', 'where', 'why'}
        query_keywords = query_words - stop_words
        
        scored_docs = []
        for doc in documents:
            score = 0.0
            
            # Factor 1: Similarity score (weight: 0.5)
            similarity = doc.get('similarity_score', 0.0)
            score += similarity * 0.5
            
            # Factor 2: Keyword matching in title (weight: 0.3)
            metadata = doc.get('metadata', {})
            title = metadata.get('title', '').lower()
            title_matches = sum(1 for keyword in query_keywords if keyword in title)
            if query_keywords:
                title_score = title_matches / len(query_keywords)
                score += title_score * 0.3
            
            # Factor 3: Keyword matching in content (weight: 0.15)
            content = doc.get('content', '').lower()
            content_matches = sum(1 for keyword in query_keywords if keyword in content)
            if query_keywords:
                content_score = min(content_matches / len(query_keywords), 1.0)
                score += content_score * 0.15
            
            # Factor 4: Content length (prefer documents with more content, weight: 0.05)
            content_length = len(doc.get('content', ''))
            # Normalize: prefer documents with 500-5000 chars
            if 500 <= content_length <= 5000:
                length_score = 1.0
            elif content_length < 500:
                length_score = content_length / 500
            else:
                length_score = max(0.5, 1.0 - (content_length - 5000) / 10000)
            score += length_score * 0.05
            
            scored_docs.append((score, doc))
        
        # Sort by score (descending) and return top_k
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        reranked = [doc for _, doc in scored_docs[:top_k]]
        
        logger.info(f"Rule-based re-ranked {len(documents)} documents, selected top {len(reranked)} with scores: {[f'{s:.3f}' for s, _ in scored_docs[:top_k]]}")
        
        return reranked
    
    def _generate_with_lm_studio(self, system_prompt: str, full_prompt: str) -> str:
        """Generate response using LM Studio"""
        if not self.client:
            raise ValueError("LM Studio client not initialized")
        
        # Prepare messages for OpenAI API format
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt}
        ]
        
        logger.info(f"Generating response with LM Studio model: {self.model_name} (max_tokens: 8192)")
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                **self.generation_config
            )
        except Exception as api_error:
            logger.error(f"LM Studio API call failed: {str(api_error)}")
            raise
        
        # Extract response text with proper error handling
        if not response:
            logger.error("Response is None from LM Studio")
            raise ValueError("Response is None from LM Studio")
        
        # Try to extract response text safely
        try:
            # Standard OpenAI API format
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                if choice and hasattr(choice, 'message'):
                    message = choice.message
                    if message:
                        response_text = getattr(message, 'content', None) or getattr(message, 'text', None)
                        if response_text:
                            logger.debug("Successfully extracted response using standard format")
                            return response_text
                        else:
                            logger.warning(f"Response content is None. Message attributes: {dir(message)}")
                            raise ValueError("Response content is None")
                    else:
                        raise ValueError("Message is None in response")
                else:
                    raise ValueError("Choice or message missing in response")
            else:
                # Try dict-like access
                if isinstance(response, dict):
                    choices = response.get('choices', [])
                    if choices and len(choices) > 0:
                        message = choices[0].get('message', {})
                        response_text = message.get('content') or message.get('text')
                        if response_text:
                            logger.debug("Successfully extracted response using dict format")
                            return response_text
                        else:
                            raise ValueError("Response content is None (dict format)")
                    else:
                        raise ValueError("No choices in response (dict format)")
                else:
                    logger.error(f"Unexpected response type: {type(response)}, attributes: {dir(response)}")
                    raise ValueError(f"Unexpected response format: {type(response)}")
        except (AttributeError, IndexError, KeyError, TypeError) as e:
            logger.error(f"Error extracting response: {str(e)}, Response type: {type(response)}")
            if hasattr(response, '__dict__'):
                logger.error(f"Response __dict__: {response.__dict__}")
            raise ValueError(f"Failed to extract response text: {str(e)}")
    
    def _generate_with_gemini(self, full_prompt: str) -> str:
        """Generate response using Gemini API"""
        if not self.gemini_model:
            raise ValueError("Gemini model not initialized")
        
        max_tokens = self.generation_config.get('max_output_tokens', 32768)
        logger.info(f"Generating response with Gemini model: {self.model_name} (max_output_tokens: {max_tokens}, prompt_length: {len(full_prompt)} chars)")
        try:
            # Suppress stderr warnings during API call
            with redirect_stderr(StringIO()):
                # Explicitly pass generation config to ensure it's used
                response = self.gemini_model.generate_content(
                    full_prompt,
                    generation_config=self.generation_config
                )
            if not response or not hasattr(response, 'text'):
                raise ValueError("Invalid response from Gemini API")
            return response.text
        except Exception as api_error:
            logger.error(f"Gemini API call failed: {str(api_error)}")
            raise
    
    async def generate_response(self, user_message: str, conversation_history: Optional[List[Dict[str, str]]] = None, max_context_docs: int = 10) -> Dict[str, Any]:
        """
        Generate a response using RAG (Retrieval-Augmented Generation) with re-ranking
        
        Args:
            user_message: The user's message
            conversation_history: Previous conversation messages
            max_context_docs: Maximum number of relevant documents to use after re-ranking (default: 10)
            
        Returns:
            Dict containing the response and metadata
        """
        try:
            # Step 1: Retrieve more documents initially for re-ranking
            initial_limit = max_context_docs * 3  # Retrieve 3x more for better re-ranking
            logger.info(f"Searching for relevant documents for query: {user_message} (retrieving {initial_limit} for re-ranking)")
            retrieved_docs = await self.vector_store.search(user_message, limit=initial_limit)
            
            # Step 2: Re-rank documents to select the best context
            relevant_docs = self._rerank_documents(retrieved_docs, user_message, top_k=max_context_docs)
            
            # Step 3: Prepare context from re-ranked documents
            context = self._prepare_context(relevant_docs)
            
            # Step 3: Prepare conversation history
            chat_history = self._prepare_chat_history(conversation_history)
            
            # Step 4: Create the prompt with context
            system_prompt = self._create_system_prompt()
            full_prompt = self._create_rag_prompt(user_message, context, chat_history)
            
            # Step 5: Generate response using the selected provider
            if self.provider == 'gemini':
                response_text = self._generate_with_gemini(full_prompt)
            else:
                response_text = self._generate_with_lm_studio(system_prompt, full_prompt)
            
            # Step 8: Format and return response
            return {
                'response': response_text,
                'context_documents': len(relevant_docs),
                'sources': [doc['metadata'] for doc in relevant_docs],
                'relevant_docs': relevant_docs,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Failed to generate response: {str(e)}")
            return {
                'response': f"I apologize, but I encountered an error while processing your request: {str(e)}",
                'context_documents': 0,
                'sources': [],
                'relevant_docs': [],
                'success': False,
                'error': str(e)
            }
    
    def _prepare_context(self, relevant_docs: List[Dict[str, Any]]) -> str:
        """Prepare context string from relevant documents with rolling window"""
        if not relevant_docs:
            return "No relevant documents found in the knowledge base."
        
        context_parts = []
        total_chars = 0
        
        # Process documents in order of relevance, applying rolling window
        for i, doc in enumerate(relevant_docs, 1):
            content = doc['content'][:self.max_doc_chars]  # Limit per document
            metadata = doc['metadata']
            title = metadata.get('title', 'Untitled')
            url = metadata.get('url', '')
            similarity = doc.get('similarity_score', 0)
            
            # Format document entry
            doc_entry = f"""
Document {i} (Similarity: {similarity:.2f}):
Title: {title}
URL: {url}
Content: {content}
---"""
            
            doc_chars = len(doc_entry)
            
            # Check if adding this document would exceed the context limit
            if total_chars + doc_chars > self.max_context_chars:
                # Truncate this document to fit within remaining space
                remaining_chars = max(0, self.max_context_chars - total_chars - 200)  # Reserve 200 for formatting
                if remaining_chars > 100:  # Only add if we have meaningful space
                    truncated_content = content[:remaining_chars] + "..."
                    doc_entry = f"""
Document {i} (Similarity: {similarity:.2f}):
Title: {title}
URL: {url}
Content: {truncated_content}
---"""
                    context_parts.append(doc_entry)
                    logger.info(f"Context window: Truncated document {i} to fit within {self.max_context_chars} char limit")
                break  # Stop adding documents
            
            context_parts.append(doc_entry)
            total_chars += doc_chars
        
        if not context_parts:
            return "No relevant documents found in the knowledge base."
        
        result = "\n".join(context_parts)
        logger.debug(f"Context prepared: {len(context_parts)} documents, {len(result)} total characters")
        return result
    
    def _apply_rolling_window(self, conversation_history: Optional[List[Dict[str, str]]]) -> List[Dict[str, str]]:
        """
        Apply rolling window to conversation history to prevent memory overflow.
        Keeps the most recent messages within character and message count limits.
        """
        if not conversation_history:
            return []
        
        # Start with the most recent messages (keep last N messages)
        windowed_history = conversation_history[-self.max_history_messages:]
        
        # Apply character limit per message
        truncated_history = []
        for msg in windowed_history:
            content = msg.get('content', '')
            if len(content) > self.max_message_chars:
                content = content[:self.max_message_chars] + "..."
            truncated_history.append({
                'role': msg.get('role', 'user'),
                'content': content
            })
        
        # Apply total character limit by removing oldest messages
        total_chars = sum(len(msg.get('content', '')) for msg in truncated_history)
        
        if total_chars > self.max_history_chars:
            # Remove oldest messages until we're under the limit
            final_history = []
            current_chars = 0
            
            # Process from newest to oldest, keeping as many as possible
            for msg in reversed(truncated_history):
                msg_chars = len(msg.get('content', ''))
                if current_chars + msg_chars <= self.max_history_chars:
                    final_history.insert(0, msg)  # Insert at beginning to maintain order
                    current_chars += msg_chars
                else:
                    # Can't fit this message, stop
                    break
            
            logger.info(f"Rolling window: {len(conversation_history)} -> {len(final_history)} messages, "
                       f"{total_chars} -> {current_chars} chars")
            return final_history
        
        return truncated_history
    
    def _prepare_chat_history(self, conversation_history: Optional[List[Dict[str, str]]]) -> str:
        """Prepare conversation history for context with rolling window"""
        if not conversation_history:
            return ""
        
        # Apply rolling window to prevent memory overflow
        windowed_history = self._apply_rolling_window(conversation_history)
        
        if not windowed_history:
            return ""
        
        history_parts = []
        for msg in windowed_history:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            history_parts.append(f"**{role.title()}:** {content}")
        
        return "## Previous Conversation Context:\n" + "\n".join(history_parts) + "\n\n"
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt with instructions for the AI assistant"""
        return """You are a helpful AI assistant that answers questions based on the provided documentation context and conversation history. 

Instructions:
1. Answer the user's question using the information provided in the context and previous conversation
2. Reference previous conversation when relevant to provide continuity and context
3. If the context doesn't contain enough information to answer the question, say so clearly
4. Be concise but comprehensive in your responses
5. Cite specific documents or sections when relevant
6. Maintain a helpful and professional tone
7. If asked about something not in the context, politely explain that you can only answer based on the available documentation
8. Build upon previous questions and answers to provide more detailed or related information when appropriate

FORMATTING GUIDELINES:
- Use proper markdown formatting for better readability
- Use **bold** for important concepts and key terms
- Use *italics* for emphasis
- Use `code blocks` for code snippets, commands, and technical terms
- Use ```language blocks for multi-line code examples
- Use > blockquotes for important notes or warnings
- Use bullet points (- or *) for lists
- Use numbered lists (1., 2., 3.) for step-by-step instructions
- Use ### for section headers when organizing complex information
- Use tables when presenting structured data
- Always format URLs as clickable links: [text](url)"""
    
    def _create_rag_prompt(self, user_message: str, context: str, chat_history: str) -> str:
        """Create the RAG prompt with context and conversation history"""
        return f"""{chat_history}## Documentation Context:
{context}

## Current Question:
{user_message}

Please provide a comprehensive answer based on the documentation context above."""
    
    async def get_chat_stats(self) -> Dict[str, Any]:
        """Get statistics about the chat service"""
        try:
            vector_stats = await self.vector_store.get_stats()
            model_type = 'Gemini API' if self.provider == 'gemini' else 'LM Studio (Local)'
            return {
                'vector_store_stats': vector_stats,
                'model_name': self.model_name or 'local-model',
                'model_type': model_type,
                'provider': self.provider,
                'base_url': self.base_url if self.provider == 'lm_studio' else None,
                'service_status': 'active'
            }
        except Exception as e:
            logger.error(f"Failed to get chat stats: {str(e)}")
            return {
                'vector_store_stats': {'total_documents': 0},
                'model_name': self.model_name or 'local-model',
                'model_type': 'Unknown',
                'provider': self.provider,
                'service_status': 'error',
                'error': str(e)
            }
