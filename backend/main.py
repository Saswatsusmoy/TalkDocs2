from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
from crawler import WebCrawler
from vector_store import VectorStore
from rag_chat import RAGChatService
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TalkDocs2 Backend", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
vector_store = VectorStore()
crawler = WebCrawler(
    vector_store=vector_store,
    persistence_workers=3,  # Parallel document storage
    max_concurrent_requests=10,  # Concurrent HTTP requests
    parse_workers=4  # Thread pool for HTML parsing
)
rag_chat = None  # Will be initialized after vector_store

class CrawlRequest(BaseModel):
    url: str
    max_depth: Optional[int] = 3
    max_pages: Optional[int] = 1000
    delay: Optional[float] = 0.3

class CrawlResponse(BaseModel):
    success: bool
    message: str
    new_pages_crawled: int
    existing_documents_retrieved: int
    total_content_length: int
    skipped_duplicates: int

class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    response: str
    context_documents: int
    sources: List[Dict[str, Any]]
    success: bool
    error: Optional[str] = None

class UrlCheckRequest(BaseModel):
    urls: List[str]

class UrlCheckResponse(BaseModel):
    url_status: Dict[str, Dict[str, Any]]
    total_urls: int
    existing_urls: int
    new_urls: int

class SourceResponse(BaseModel):
    source_id: str
    collection_name: str
    document_count: int
    created_at: str
    description: str

class SetSourceRequest(BaseModel):
    source_id: str

class SetProviderRequest(BaseModel):
    provider: str  # 'lm_studio' or 'gemini'

@app.on_event("startup")
async def startup_event():
    """Initialize the RAG chat service on startup"""
    global rag_chat
    try:
        await vector_store.initialize()
        rag_chat = RAGChatService(vector_store)
        logger.info("RAG Chat Service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG Chat Service: {str(e)}")

@app.get("/")
async def root():
    return {"message": "TalkDocs2 Backend API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/crawl", response_model=CrawlResponse)
async def crawl_website(request: CrawlRequest):
    """
    Crawl a website using DFS with duplicate checking and store content in vector database
    """
    try:
        logger.info(f"Starting crawl for URL: {request.url}")
        
        # Validate URL
        if not request.url.startswith(('http://', 'https://')):
            request.url = 'https://' + request.url
        
        # Start crawling with duplicate check
        crawl_results = await crawler.crawl_domain_with_duplicate_check(
            start_url=request.url,
            max_depth=request.max_depth,
            max_pages=request.max_pages,
            delay=request.delay
        )
        
        new_pages = crawl_results.get('new_pages', [])
        existing_documents = crawl_results.get('existing_documents', [])
        
        # Calculate total content length (new + existing)
        new_content_length = sum(len(page.get('content', '')) for page in new_pages)
        existing_content_length = sum(len(doc.get('content', '')) for doc in existing_documents)
        total_content_length = new_content_length + existing_content_length
        
        skipped_duplicates = crawl_results.get('retrieved_existing_documents', 0)
        
        return CrawlResponse(
            success=True,
            message=f"Crawl completed: {len(new_pages)} new pages crawled, {len(existing_documents)} existing documents retrieved",
            new_pages_crawled=len(new_pages),
            existing_documents_retrieved=len(existing_documents),
            total_content_length=total_content_length,
            skipped_duplicates=skipped_duplicates
        )
        
    except Exception as e:
        logger.error(f"Crawl failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Crawling failed: {str(e)}")

@app.post("/check-urls", response_model=UrlCheckResponse)
async def check_urls(request: UrlCheckRequest):
    """
    Check which URLs already exist in the database
    """
    try:
        url_status = await vector_store.check_urls_exist(request.urls)
        
        existing_count = sum(1 for status in url_status.values() if status.get('exists', False))
        new_count = len(request.urls) - existing_count
        
        return UrlCheckResponse(
            url_status=url_status,
            total_urls=len(request.urls),
            existing_urls=existing_count,
            new_urls=new_count
        )
    except Exception as e:
        logger.error(f"URL check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"URL check failed: {str(e)}")

@app.get("/sources", response_model=List[SourceResponse])
async def get_available_sources():
    """
    Get list of all available document sources
    """
    try:
        sources = await vector_store.get_available_sources()
        return sources
    except Exception as e:
        logger.error(f"Failed to get sources: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get sources: {str(e)}")

@app.post("/sources/active")
async def set_active_source(request: SetSourceRequest):
    """
    Set the active source for chat and search operations
    """
    try:
        await vector_store.set_active_source(request.source_id)
        return {
            "message": f"Active source set to: {request.source_id}",
            "source_id": request.source_id
        }
    except Exception as e:
        logger.error(f"Failed to set active source: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to set active source: {str(e)}")

@app.delete("/sources/{source_id}")
async def delete_source(source_id: str):
    """
    Delete a documentation source and its stored data
    """
    try:
        await vector_store.delete_source(source_id)
        return {
            "message": f"Source {source_id} deleted successfully",
            "source_id": source_id
        }
    except Exception as e:
        logger.error(f"Failed to delete source {source_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete source: {str(e)}")

@app.get("/sources/active")
async def get_active_source():
    """
    Get the currently active source
    """
    try:
        return {
            "source_id": vector_store.current_source_id,
            "message": f"Active source: {vector_store.current_source_id or 'None'}"
        }
    except Exception as e:
        logger.error(f"Failed to get active source: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get active source: {str(e)}")

@app.get("/model/provider")
async def get_model_provider():
    """
    Get the currently active model provider
    """
    try:
        if not rag_chat:
            raise HTTPException(status_code=503, detail="RAG Chat Service not initialized")
        return {
            "provider": rag_chat.provider,
            "model_name": rag_chat.model_name,
            "model_type": "Gemini API" if rag_chat.provider == "gemini" else "LM Studio (Local)",
            "base_url": rag_chat.base_url if rag_chat.provider == "lm_studio" else None
        }
    except Exception as e:
        logger.error(f"Failed to get model provider: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get model provider: {str(e)}")

@app.post("/model/provider")
async def set_model_provider(request: SetProviderRequest):
    """
    Set the model provider (lm_studio or gemini)
    """
    try:
        if not rag_chat:
            raise HTTPException(status_code=503, detail="RAG Chat Service not initialized")
        
        if request.provider not in ['lm_studio', 'gemini']:
            raise HTTPException(status_code=400, detail="Provider must be 'lm_studio' or 'gemini'")
        
        rag_chat.set_provider(request.provider)
        return {
            "message": f"Model provider set to: {request.provider}",
            "provider": rag_chat.provider,
            "model_name": rag_chat.model_name,
            "model_type": "Gemini API" if rag_chat.provider == "gemini" else "LM Studio (Local)"
        }
    except ValueError as e:
        logger.error(f"Failed to set model provider: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to set model provider: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to set model provider: {str(e)}")

@app.get("/search")
async def search_documents(query: str, limit: int = 10, source_id: Optional[str] = None):
    """
    Search documents in the vector database
    """
    try:
        results = await vector_store.search(query, limit=limit, source_id=source_id)
        return {
            "query": query,
            "source_id": source_id or vector_store.current_source_id,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.delete("/clear-database")
async def clear_database():
    """
    Clear all documents from the vector database
    """
    try:
        await vector_store.clear_all()
        return {"message": "Database cleared successfully"}
    except Exception as e:
        logger.error(f"Clear database failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear database: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat_with_rag(request: ChatRequest):
    """
    Chat with the RAG-powered AI assistant
    """
    try:
        if not rag_chat:
            raise HTTPException(status_code=503, detail="RAG Chat Service not initialized")
        
        logger.info(f"Processing chat request: {request.message[:100]}...")
        
        # Convert ChatMessage objects to dict format expected by RAG service
        conversation_history = []
        if request.conversation_history:
            for msg in request.conversation_history:
                conversation_history.append({
                    'role': msg.role,
                    'content': msg.content
                })
            logger.info(f"Using {len(conversation_history)} previous messages for context")
        
        # Generate response using RAG with re-ranking
        result = await rag_chat.generate_response(
            user_message=request.message,
            conversation_history=conversation_history,
            max_context_docs=10
        )
        
        return ChatResponse(
            response=result['response'],
            context_documents=result['context_documents'],
            sources=result['sources'],
            success=result['success'],
            error=result.get('error')
        )
        
    except Exception as e:
        logger.error(f"Chat request failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat request failed: {str(e)}")

@app.get("/chat/stats")
async def get_chat_stats():
    """
    Get statistics about the chat service and vector database
    """
    try:
        if not rag_chat:
            raise HTTPException(status_code=503, detail="RAG Chat Service not initialized")
        
        stats = await rag_chat.get_chat_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get chat stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get chat stats: {str(e)}")

@app.get("/documents")
async def get_all_documents():
    """
    Get metadata for all stored documents
    """
    try:
        documents_metadata = await vector_store.get_all_documents_metadata()
        return documents_metadata
    except Exception as e:
        logger.error(f"Failed to get documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get documents: {str(e)}")

@app.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    """
    Get a specific document by ID
    """
    try:
        document = await vector_store.get_document_by_id(doc_id)
        return document
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
    except Exception as e:
        logger.error(f"Failed to get document {doc_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")

@app.post("/backup")
async def create_backup(backup_name: Optional[str] = None):
    """
    Create a backup of all documents and vector database
    """
    try:
        backup_path = await vector_store.create_backup(backup_name)
        return {
            "message": "Backup created successfully",
            "backup_path": backup_path,
            "backup_name": backup_name or "auto_generated"
        }
    except Exception as e:
        logger.error(f"Failed to create backup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create backup: {str(e)}")

@app.get("/storage/info")
async def get_storage_info():
    """
    Get information about storage directories and usage
    """
    try:
        import os
        import shutil
        
        # Get directory sizes
        def get_dir_size(path):
            total = 0
            try:
                for entry in os.scandir(path):
                    if entry.is_file():
                        total += entry.stat().st_size
                    elif entry.is_dir():
                        total += get_dir_size(entry.path)
            except (OSError, FileNotFoundError):
                pass
            return total
        
        # Calculate sizes
        chroma_size = get_dir_size("./data/chroma_db")
        documents_size = get_dir_size("./data/documents")
        
        # Get file counts
        def count_files(path, extension=None):
            count = 0
            try:
                for entry in os.scandir(path):
                    if entry.is_file():
                        if extension is None or entry.name.endswith(extension):
                            count += 1
                    elif entry.is_dir():
                        count += count_files(entry.path, extension)
            except (OSError, FileNotFoundError):
                pass
            return count
        
        chroma_files = count_files("./data/chroma_db")
        document_files = count_files("./data/documents", ".json")
        
        return {
            "storage_info": {
                "chroma_db": {
                    "path": "./data/chroma_db",
                    "size_bytes": chroma_size,
                    "size_mb": round(chroma_size / (1024 * 1024), 2),
                    "file_count": chroma_files
                },
                "documents": {
                    "path": "./data/documents",
                    "size_bytes": documents_size,
                    "size_mb": round(documents_size / (1024 * 1024), 2),
                    "file_count": document_files
                },
                "total_size_mb": round((chroma_size + documents_size) / (1024 * 1024), 2)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get storage info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get storage info: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
