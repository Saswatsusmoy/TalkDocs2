import chromadb
from chromadb.config import Settings
from fastembed import TextEmbedding
import logging
import uuid
from typing import List, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor
import os
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, collection_name: str = "talkdocs_collection", persist_directory: str = "./data/chroma_db"):
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.documents_directory = "./data/documents"
        self.client = None
        self.collection = None
        self.embedding_model = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.current_source_id = None
        
        # Create directories if they don't exist
        os.makedirs(self.persist_directory, exist_ok=True)
        os.makedirs(self.documents_directory, exist_ok=True)
    
    def _generate_source_id(self, url: str) -> str:
        """Generate a unique source ID from URL"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        # Create a clean source ID from domain
        source_id = domain.replace('.', '_').replace('-', '_')
        return f"source_{source_id}"
    
    def _get_collection_name(self, source_id: str) -> str:
        """Get collection name for a specific source"""
        return f"{self.collection_name}_{source_id}"
    
    async def set_active_source(self, source_id: str):
        """Set the active source for search operations"""
        self.current_source_id = source_id
        collection_name = self._get_collection_name(source_id)
        
        try:
            if not self.client:
                await self.initialize()
            
            # Get or create collection for this source
            try:
                self.collection = self.client.get_collection(name=collection_name)
                logger.info(f"Switched to source collection: {collection_name}")
            except Exception:
                # Collection doesn't exist, create it
                self.collection = self.client.create_collection(
                    name=collection_name,
                    metadata={
                        "description": f"TalkDocs2 collection for source: {source_id}",
                        "source_id": source_id,
                        "created_at": datetime.now().isoformat()
                    }
                )
                logger.info(f"Created new source collection: {collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to set active source {source_id}: {str(e)}")
            raise
    
    async def get_available_sources(self) -> List[Dict[str, Any]]:
        """Get list of all available sources"""
        try:
            if not self.client:
                await self.initialize()
            
            collections = self.client.list_collections()
            sources = []
            
            for collection in collections:
                if collection.name.startswith(self.collection_name + "_source_"):
                    # Extract source ID from collection name
                    source_id = collection.name.replace(f"{self.collection_name}_", "")
                    metadata = collection.metadata or {}
                    
                    # Get document count
                    try:
                        doc_count = collection.count()
                    except:
                        doc_count = 0
                    
                    sources.append({
                        "source_id": source_id,
                        "collection_name": collection.name,
                        "document_count": doc_count,
                        "created_at": metadata.get("created_at"),
                        "description": metadata.get("description", "")
                    })
            
            return sources
            
        except Exception as e:
            logger.error(f"Failed to get available sources: {str(e)}")
            return []
        
    async def initialize(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Initialize ChromaDB client with persistent storage
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
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
    
    async def store_documents(self, pages: List[Dict[str, Any]], source_url: str = None):
        """Store documents in the vector database and save raw documents locally"""
        try:
            # Generate source ID from the first page URL or provided source_url
            if source_url:
                source_id = self._generate_source_id(source_url)
            elif pages and pages[0].get('url'):
                source_id = self._generate_source_id(pages[0]['url'])
            else:
                raise ValueError("No source URL provided for document storage")
            
            # Set active source and get/create collection
            await self.set_active_source(source_id)
            
            documents = []
            metadatas = []
            ids = []
            stored_docs = []
            
            for page in pages:
                # Prepare document content
                content = page.get('content', '')
                if not content.strip():
                    continue
                
                # Create document ID
                doc_id = str(uuid.uuid4())
                
                # Prepare metadata with source information
                metadata = {
                    'url': page.get('url', ''),
                    'title': page.get('title', ''),
                    'meta_description': page.get('meta_description', ''),
                    'timestamp': page.get('timestamp', 0),
                    'content_length': len(content),
                    'doc_id': doc_id,
                    'crawled_at': datetime.now().isoformat(),
                    'source_id': source_id,
                    'source_url': source_url or pages[0].get('url', '')
                }
                
                # Save raw document to local storage with source organization
                await self._save_document_locally(doc_id, page, metadata, source_id)
                
                documents.append(content)
                metadatas.append(metadata)
                ids.append(doc_id)
                stored_docs.append({
                    'id': doc_id,
                    'url': page.get('url', ''),
                    'title': page.get('title', ''),
                    'content_length': len(content),
                    'source_id': source_id
                })
            
            if not documents:
                logger.warning("No valid documents to store")
                return
            
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(documents)} documents in source {source_id}...")
            embeddings = await self._get_embeddings(documents)
            
            # Store in ChromaDB
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
            
            # Update document index with source information
            await self._update_document_index(stored_docs, source_id)
            
            logger.info(f"Successfully stored {len(documents)} documents in source {source_id}")
            
        except Exception as e:
            logger.error(f"Failed to store documents: {str(e)}")
            raise
    
    async def search(self, query: str, limit: int = 10, source_id: str = None) -> List[Dict[str, Any]]:
        """Search for similar documents in the current or specified source"""
        try:
            # If source_id is provided, switch to that source
            if source_id and source_id != self.current_source_id:
                await self.set_active_source(source_id)
            elif not self.collection:
                # If no active source, initialize with default
                await self.initialize()
            
            if not self.collection:
                logger.warning("No active collection for search")
                return []
            
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
            
            logger.info(f"Found {len(formatted_results)} results for query '{query}' in source {self.current_source_id}")
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
    
    async def _save_document_locally(self, doc_id: str, page: Dict[str, Any], metadata: Dict[str, Any], source_id: str):
        """Save raw document to local storage with source organization"""
        try:
            document_data = {
                'id': doc_id,
                'url': page.get('url', ''),
                'title': page.get('title', ''),
                'content': page.get('content', ''),
                'meta_description': page.get('meta_description', ''),
                'timestamp': page.get('timestamp', 0),
                'metadata': metadata,
                'source_id': source_id
            }
            
            # Create source-specific directory
            source_dir = os.path.join(self.documents_directory, source_id)
            os.makedirs(source_dir, exist_ok=True)
            
            # Save individual document file in source directory
            doc_file_path = os.path.join(source_dir, f"{doc_id}.json")
            with open(doc_file_path, 'w', encoding='utf-8') as f:
                json.dump(document_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Saved document {doc_id} to {doc_file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save document {doc_id} locally: {str(e)}")
    
    async def _update_document_index(self, stored_docs: List[Dict[str, Any]], source_id: str):
        """Update the document index with newly stored documents for a specific source"""
        try:
            # Create source-specific index file
            index_file = os.path.join(self.documents_directory, f"{source_id}_index.json")
            
            # Load existing index or create new one
            if os.path.exists(index_file):
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
            else:
                index_data = {
                    'source_id': source_id,
                    'created_at': datetime.now().isoformat(),
                    'last_updated': datetime.now().isoformat(),
                    'documents': []
                }
            
            # Add new documents to index
            index_data['documents'].extend(stored_docs)
            index_data['last_updated'] = datetime.now().isoformat()
            index_data['total_documents'] = len(index_data['documents'])
            
            # Save updated index
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Updated document index for source {source_id} with {len(stored_docs)} new documents")
            
        except Exception as e:
            logger.error(f"Failed to update document index for source {source_id}: {str(e)}")
    
    async def get_document_by_id(self, doc_id: str) -> Dict[str, Any]:
        """Retrieve a document by its ID from local storage"""
        try:
            doc_file_path = os.path.join(self.documents_directory, f"{doc_id}.json")
            
            if not os.path.exists(doc_file_path):
                raise FileNotFoundError(f"Document {doc_id} not found")
            
            with open(doc_file_path, 'r', encoding='utf-8') as f:
                document_data = json.load(f)
            
            return document_data
            
        except Exception as e:
            logger.error(f"Failed to retrieve document {doc_id}: {str(e)}")
            raise
    
    async def get_all_documents_metadata(self) -> Dict[str, Any]:
        """Get metadata for all stored documents"""
        try:
            index_file = os.path.join(self.documents_directory, "document_index.json")
            
            if not os.path.exists(index_file):
                return {
                    'created_at': None,
                    'last_updated': None,
                    'total_documents': 0,
                    'documents': []
                }
            
            with open(index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            return index_data
            
        except Exception as e:
            logger.error(f"Failed to get documents metadata: {str(e)}")
            return {
                'created_at': None,
                'last_updated': None,
                'total_documents': 0,
                'documents': [],
                'error': str(e)
            }
    
    async def check_urls_exist(self, urls: List[str]) -> Dict[str, Dict[str, Any]]:
        """Check which URLs already exist in the database"""
        try:
            index_data = await self.get_all_documents_metadata()
            existing_docs = index_data.get('documents', [])
            
            # Create a mapping of URL to document info
            url_to_doc = {}
            for doc in existing_docs:
                if 'url' in doc:
                    url_to_doc[doc['url']] = doc
            
            # Check which URLs exist
            result = {}
            for url in urls:
                if url in url_to_doc:
                    result[url] = {
                        'exists': True,
                        'document_id': url_to_doc[url].get('id'),
                        'title': url_to_doc[url].get('title'),
                        'content_length': url_to_doc[url].get('content_length'),
                        'crawled_at': url_to_doc[url].get('crawled_at')
                    }
                else:
                    result[url] = {'exists': False}
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to check URLs: {str(e)}")
            return {url: {'exists': False, 'error': str(e)} for url in urls}
    
    async def get_existing_documents_for_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Get existing documents for URLs that are already stored"""
        try:
            url_check = await self.check_urls_exist(urls)
            existing_docs = []
            
            for url, info in url_check.items():
                if info.get('exists') and 'document_id' in info:
                    try:
                        doc = await self.get_document_by_id(info['document_id'])
                        existing_docs.append(doc)
                    except Exception as e:
                        logger.warning(f"Failed to load existing document {info['document_id']}: {str(e)}")
            
            return existing_docs
            
        except Exception as e:
            logger.error(f"Failed to get existing documents: {str(e)}")
            return []
    
    async def create_backup(self, backup_name: str = None) -> str:
        """Create a backup of all documents and vector database"""
        try:
            if not backup_name:
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            backup_dir = os.path.join(self.documents_directory, "backups", backup_name)
            os.makedirs(backup_dir, exist_ok=True)
            
            # Copy document index
            index_file = os.path.join(self.documents_directory, "document_index.json")
            if os.path.exists(index_file):
                import shutil
                shutil.copy2(index_file, backup_dir)
            
            # Copy individual document files
            docs_backup_dir = os.path.join(backup_dir, "documents")
            os.makedirs(docs_backup_dir, exist_ok=True)
            
            for filename in os.listdir(self.documents_directory):
                if filename.endswith('.json') and filename != 'document_index.json':
                    shutil.copy2(
                        os.path.join(self.documents_directory, filename),
                        docs_backup_dir
                    )
            
            # Note: ChromaDB persistence is handled automatically
            logger.info(f"Created backup: {backup_name}")
            return backup_dir
            
        except Exception as e:
            logger.error(f"Failed to create backup: {str(e)}")
            raise
    
    def __del__(self):
        """Cleanup executor on destruction"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
