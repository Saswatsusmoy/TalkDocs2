import google.generativeai as genai
import logging
from typing import List, Dict, Any, Optional
from vector_store import VectorStore
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class RAGChatService:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.genai_client = None
        self.model = None
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize Google Generative AI client"""
        try:
            # Get API key from environment
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                logger.error("GEMINI_API_KEY not found in environment variables")
                raise ValueError("GEMINI_API_KEY is required")
            
            # Configure the client
            genai.configure(api_key=api_key)
            
            # Initialize the model
            self.model = genai.GenerativeModel('models/gemma-3-12b-it')
            
            logger.info("Google Generative AI initialized successfully with Gemma-3-12B-IT model")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI: {str(e)}")
            raise
    
    async def generate_response(self, user_message: str, conversation_history: Optional[List[Dict[str, str]]] = None, max_context_docs: int = 5) -> Dict[str, Any]:
        """
        Generate a response using RAG (Retrieval-Augmented Generation)
        
        Args:
            user_message: The user's message
            conversation_history: Previous conversation messages
            max_context_docs: Maximum number of relevant documents to retrieve
            
        Returns:
            Dict containing the response and metadata
        """
        try:
            # Step 1: Retrieve relevant documents from vector store using active source
            logger.info(f"Searching for relevant documents for query: {user_message}")
            relevant_docs = await self.vector_store.search(user_message, limit=max_context_docs)
            
            # Step 2: Prepare context from retrieved documents
            context = self._prepare_context(relevant_docs)
            
            # Step 3: Prepare conversation history
            chat_history = self._prepare_chat_history(conversation_history)
            
            # Step 4: Create the prompt with context
            prompt = self._create_rag_prompt(user_message, context, chat_history)
            
            # Step 5: Generate response using Gemini
            logger.info("Generating response with Gemini AI")
            response = self.model.generate_content(prompt)
            
            # Step 6: Format and return response
            return {
                'response': response.text,
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
        """Prepare context string from relevant documents"""
        if not relevant_docs:
            return "No relevant documents found in the knowledge base."
        
        context_parts = []
        for i, doc in enumerate(relevant_docs, 1):
            content = doc['content'][:1000]  # Limit content length
            metadata = doc['metadata']
            title = metadata.get('title', 'Untitled')
            url = metadata.get('url', '')
            similarity = doc.get('similarity_score', 0)
            
            context_parts.append(f"""
Document {i} (Similarity: {similarity:.2f}):
Title: {title}
URL: {url}
Content: {content}
---""")
        
        return "\n".join(context_parts)
    
    def _prepare_chat_history(self, conversation_history: Optional[List[Dict[str, str]]]) -> str:
        """Prepare conversation history for context"""
        if not conversation_history:
            return ""
        
        history_parts = []
        # Keep last 10 messages for better context (5 exchanges)
        for msg in conversation_history[-10:]:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            # Truncate very long messages to avoid context overflow
            if len(content) > 500:
                content = content[:500] + "..."
            history_parts.append(f"**{role.title()}:** {content}")
        
        return "## Previous Conversation Context:\n" + "\n".join(history_parts) + "\n\n"
    
    def _create_rag_prompt(self, user_message: str, context: str, chat_history: str) -> str:
        """Create the RAG prompt for Gemini AI with enhanced formatting instructions"""
        return f"""You are a helpful AI assistant that answers questions based on the provided documentation context and conversation history. 

Instructions:
1. Answer the user's question using the information provided in the context and previous conversation
2. Reference previous conversation when relevant to provide continuity and context
3. If the context doesn't contain enough information to answer the question, say so clearly
4. Be concise but comprehensive in your responses
5. Cite specific documents or sections when relevant
6. Maintain a helpful and professional tone
7. If asked about something not in the context, politely explain that you can only answer based on the available documentation
8. Build upon previous questions and answers to provide more detailed or related information when appropriate

CONVERSATION CONTEXT:
- Use the previous conversation history to understand the context and flow of the discussion
- Reference previous topics or questions when relevant
- Provide follow-up information or clarification based on earlier exchanges
- Maintain conversational continuity while staying focused on the current question

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
- Always format URLs as clickable links: [text](url)

{chat_history}## Documentation Context:
{context}

## Current Question:
{user_message}

Answer:"""
    
    async def get_chat_stats(self) -> Dict[str, Any]:
        """Get statistics about the chat service"""
        try:
            vector_stats = await self.vector_store.get_stats()
            return {
                'vector_store_stats': vector_stats,
                'model_name': 'models/gemma-3-12b-it',
                'service_status': 'active'
            }
        except Exception as e:
            logger.error(f"Failed to get chat stats: {str(e)}")
            return {
                'vector_store_stats': {'total_documents': 0},
                'model_name': 'models/gemma-3-12b-it',
                'service_status': 'error',
                'error': str(e)
            }
