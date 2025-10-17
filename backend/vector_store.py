import chromadb
from chromadb.config import Settings
from fastembed import TextEmbedding
import logging
import uuid
from typing import List, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, collection_name: str = "talkdocs_collection"):
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.embedding_model = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        
    async def initialize(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Initialize ChromaDB client
            self.client = chromadb.Client(Settings(
                persist_directory="./chroma_db",
                anonymized_telemetry=False
            ))
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                logger.info(f"Connected to existing collection: {self.collection_name}")
            except Exception:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "TalkDocs2 documentation collection"}
                )
                logger.info(f"Created new collection: {self.collection_name}")
            
            # Initialize lightweight embedding model (CPU-only, no torch)
            self.embedding_model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
            logger.info("Vector store initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {str(e)}")
            raise
    
    async def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts using fastembed"""
        try:
            # fastembed returns a generator of numpy arrays
            loop = asyncio.get_event_loop()
            def _embed_batch(input_texts):
                return list(self.embedding_model.embed(input_texts))
            embeddings = await loop.run_in_executor(self.executor, _embed_batch, texts)
            # Ensure plain python lists for Chroma
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {str(e)}")
            raise
    
    async def store_documents(self, pages: List[Dict[str, Any]]):
        """Store documents in the vector database"""
        if not self.collection:
            await self.initialize()
        
        try:
            documents = []
            metadatas = []
            ids = []
            
            for page in pages:
                # Prepare document content
                content = page.get('content', '')
                if not content.strip():
                    continue
                
                # Create document ID
                doc_id = str(uuid.uuid4())
                
                # Prepare metadata
                metadata = {
                    'url': page.get('url', ''),
                    'title': page.get('title', ''),
                    'meta_description': page.get('meta_description', ''),
                    'timestamp': page.get('timestamp', 0),
                    'content_length': len(content)
                }
                
                documents.append(content)
                metadatas.append(metadata)
                ids.append(doc_id)
            
            if not documents:
                logger.warning("No valid documents to store")
                return
            
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(documents)} documents...")
            embeddings = await self._get_embeddings(documents)
            
            # Store in ChromaDB
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
            
            logger.info(f"Successfully stored {len(documents)} documents in vector database")
            
        except Exception as e:
            logger.error(f"Failed to store documents: {str(e)}")
            raise
    
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        if not self.collection:
            await self.initialize()
        
        try:
            # Generate query embedding
            query_embedding = await self._get_embeddings([query])
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=limit,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    formatted_results.append({
                        'content': doc,
                        'metadata': metadata,
                        'similarity_score': 1 - distance,  # Convert distance to similarity
                        'rank': i + 1
                    })
            
            logger.info(f"Found {len(formatted_results)} results for query: {query}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise
    
    async def clear_all(self):
        """Clear all documents from the collection"""
        if not self.collection:
            await self.initialize()
        
        try:
            # Delete the collection and recreate it
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "TalkDocs2 documentation collection"}
            )
            logger.info("Vector database cleared successfully")
            
        except Exception as e:
            logger.error(f"Failed to clear database: {str(e)}")
            raise
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        if not self.collection:
            await self.initialize()
        
        try:
            count = self.collection.count()
            return {
                'total_documents': count,
                'collection_name': self.collection_name
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {str(e)}")
            return {'total_documents': 0, 'collection_name': self.collection_name}
    
    def __del__(self):
        """Cleanup executor on destruction"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
