import google.generativeai as genai
import json
import os
from typing import List, Dict, Optional
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DocumentChatbot:
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemma-3-12b-it"):
        """
        Initialize the chatbot with Google Generative AI
        
        Args:
            api_key: Google AI API key (if not provided, will look for GOOGLE_API_KEY env var)
            model_name: Model to use (default: gemma-2b-it)
        """
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("Google API key is required. Set GOOGLE_API_KEY environment variable or pass api_key parameter.")
        
        # Configure Google Generative AI
        genai.configure(api_key=self.api_key)
        
        # Initialize the model
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        
        # Store document data
        self.documents = []
        self.context = ""
        
    def load_documents_from_json(self, json_file_path: str) -> bool:
        """
        Load documents from a JSON file created by the web crawler
        
        Args:
            json_file_path: Path to the JSON file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.documents = data.get('pages', [])
            
            # Create context from all documents
            self.context = self._create_context_from_documents()
            
            return True
            
        except Exception as e:
            return False
    
    def load_documents_from_data(self, data: Dict) -> bool:
        """
        Load documents directly from data dictionary
        
        Args:
            data: Dictionary containing crawled data with 'pages' key
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.documents = data.get('pages', [])
            
            # Create context from all documents
            self.context = self._create_context_from_documents()
            
            return True
            
        except Exception as e:
            return False
    
    def _create_context_from_documents(self) -> str:
        """
        Create a comprehensive context string from all loaded documents
        
        Returns:
            str: Formatted context string
        """
        if not self.documents:
            return ""
        
        context_parts = []
        context_parts.append("DOCUMENT CONTEXT:")
        context_parts.append("=" * 50)
        
        for i, doc in enumerate(self.documents, 1):
            context_parts.append(f"\nDOCUMENT {i}:")
            context_parts.append(f"URL: {doc.get('url', 'N/A')}")
            context_parts.append(f"Title: {doc.get('title', 'N/A')}")
            context_parts.append(f"Content: {doc.get('content', 'N/A')}")
            context_parts.append("-" * 30)
        
        return "\n".join(context_parts)
    
    def _find_relevant_documents(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Find the most relevant documents for a given query using simple keyword matching
        
        Args:
            query: User's question
            top_k: Number of top relevant documents to return
            
        Returns:
            List[Dict]: List of relevant documents
        """
        if not self.documents:
            return []
        
        # Simple relevance scoring based on keyword matching
        query_words = set(re.findall(r'\w+', query.lower()))
        
        scored_docs = []
        for doc in self.documents:
            content_words = set(re.findall(r'\w+', doc.get('content', '').lower()))
            title_words = set(re.findall(r'\w+', doc.get('title', '').lower()))
            
            # Calculate relevance score
            content_matches = len(query_words.intersection(content_words))
            title_matches = len(query_words.intersection(title_words)) * 2  # Title matches worth more
            
            score = content_matches + title_matches
            scored_docs.append((score, doc))
        
        # Sort by score and return top_k
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scored_docs[:top_k] if score > 0]
    
    def _create_prompt_with_context(self, query: str, relevant_docs: List[Dict]) -> str:
        """
        Create a prompt that includes relevant context for the query
        
        Args:
            query: User's question
            relevant_docs: List of relevant documents
            
        Returns:
            str: Formatted prompt with context
        """
        if not relevant_docs:
            return f"Question: {query}\n\nNote: No relevant documents found in the crawled data."
        
        prompt_parts = []
        prompt_parts.append("You are a specialized AI assistant for developers and coders who need help understanding code documentation, APIs, frameworks, and technical documentation from websites.")
        prompt_parts.append("")
        prompt_parts.append("YOUR ROLE:")
        prompt_parts.append("- Help developers quickly understand code documentation without manually traversing websites")
        prompt_parts.append("- Explain APIs, functions, classes, methods, and their usage")
        prompt_parts.append("- Provide code examples and implementation guidance")
        prompt_parts.append("- Help with troubleshooting and debugging based on documentation")
        prompt_parts.append("- Explain configuration options, parameters, and settings")
        prompt_parts.append("- Assist with integration and setup instructions")
        prompt_parts.append("")
        prompt_parts.append("RESPONSE GUIDELINES:")
        prompt_parts.append("- Provide clear, concise explanations suitable for developers")
        prompt_parts.append("- Include relevant code examples when available in the documentation")
        prompt_parts.append("- Highlight important parameters, return values, and usage notes")
        prompt_parts.append("- Mention any prerequisites, dependencies, or setup requirements")
        prompt_parts.append("- If discussing APIs, explain the purpose, parameters, and return values")
        prompt_parts.append("- For configuration, explain what each option does and when to use it")
        prompt_parts.append("- If the information is not available in the documents, clearly state this")
        prompt_parts.append("")
        prompt_parts.append("Please answer the user's question using only the information from the documents below.")
        prompt_parts.append("At the end of your response, include a 'Sources:' section listing the document titles and URLs you referenced.")
        prompt_parts.append("")
        prompt_parts.append("RELEVANT DOCUMENTS:")
        prompt_parts.append("=" * 40)
        
        for i, doc in enumerate(relevant_docs, 1):
            prompt_parts.append(f"\nDocument {i}:")
            prompt_parts.append(f"Title: {doc.get('title', 'N/A')}")
            prompt_parts.append(f"URL: {doc.get('url', 'N/A')}")
            prompt_parts.append(f"Content: {doc.get('content', 'N/A')}")
            prompt_parts.append("-" * 30)
        
        prompt_parts.append(f"\nQuestion: {query}")
        prompt_parts.append("\nAnswer:")
        
        return "\n".join(prompt_parts)
    
    def chat(self, message: str, use_rag: bool = True) -> str:
        """
        Chat with the user using RAG (Retrieval-Augmented Generation)
        
        Args:
            message: User's message/question
            use_rag: Whether to use RAG (True) or just the base model (False)
            
        Returns:
            str: Bot's response
        """
        try:
            if use_rag and self.documents:
                # Use RAG: find relevant documents and create context-aware prompt
                relevant_docs = self._find_relevant_documents(message)
                prompt = self._create_prompt_with_context(message, relevant_docs)
            else:
                # Use base model without RAG
                prompt = f"Question: {message}\n\nAnswer:"
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            if response.text:
                return response.text.strip()
            else:
                return "I apologize, but I couldn't generate a response. Please try again."
                
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def get_document_summary(self) -> str:
        """
        Get a summary of the loaded documents
        
        Returns:
            str: Summary of loaded documents
        """
        if not self.documents:
            return "No documents loaded."
        
        summary_parts = []
        summary_parts.append(f"Loaded {len(self.documents)} documents:")
        
        for i, doc in enumerate(self.documents, 1):
            title = doc.get('title', 'No Title')
            url = doc.get('url', 'No URL')
            content_length = len(doc.get('content', ''))
            
            summary_parts.append(f"{i}. {title}")
            summary_parts.append(f"   URL: {url}")
            summary_parts.append(f"   Content length: {content_length} characters")
        
        return "\n".join(summary_parts)
    
    def clear_documents(self):
        """Clear all loaded documents"""
        self.documents = []
        self.context = ""

# Example usage
if __name__ == "__main__":
    # Initialize chatbot (you'll need to set GOOGLE_API_KEY environment variable)
    try:
        chatbot = DocumentChatbot()
        
        # Load documents
        if chatbot.load_documents_from_json('crawled_data.json'):
            # Test chat
            response = chatbot.chat("What is the main topic of these documents?")
        else:
            pass
            
    except ValueError as e:
        pass
