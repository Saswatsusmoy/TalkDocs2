from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
from crawler import WebCrawler
from vector_store import VectorStore
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
crawler = WebCrawler()
vector_store = VectorStore()

class CrawlRequest(BaseModel):
    url: str
    max_depth: Optional[int] = 3
    max_pages: Optional[int] = 100
    delay: Optional[float] = 1.0

class CrawlResponse(BaseModel):
    success: bool
    message: str
    pages_crawled: int
    total_content_length: int

@app.get("/")
async def root():
    return {"message": "TalkDocs2 Backend API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/crawl", response_model=CrawlResponse)
async def crawl_website(request: CrawlRequest):
    """
    Crawl a website using DFS and store content in vector database
    """
    try:
        logger.info(f"Starting crawl for URL: {request.url}")
        
        # Validate URL
        if not request.url.startswith(('http://', 'https://')):
            request.url = 'https://' + request.url
        
        # Start crawling
        crawl_results = await crawler.crawl_domain(
            start_url=request.url,
            max_depth=request.max_depth,
            max_pages=request.max_pages,
            delay=request.delay
        )
        
        # Store in vector database
        if crawl_results['pages']:
            await vector_store.store_documents(crawl_results['pages'])
            logger.info(f"Stored {len(crawl_results['pages'])} pages in vector database")
        
        return CrawlResponse(
            success=True,
            message=f"Successfully crawled {len(crawl_results['pages'])} pages",
            pages_crawled=len(crawl_results['pages']),
            total_content_length=sum(len(page.get('content', '')) for page in crawl_results['pages'])
        )
        
    except Exception as e:
        logger.error(f"Crawl failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Crawling failed: {str(e)}")

@app.get("/search")
async def search_documents(query: str, limit: int = 10):
    """
    Search documents in the vector database
    """
    try:
        results = await vector_store.search(query, limit=limit)
        return {
            "query": query,
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
