# TalkDocs2 Backend

A robust web crawler and vector database backend for TalkDocs2, featuring DFS (Depth-First Search) crawling and ChromaDB integration.

## Features

- **DFS Web Crawler**: Efficient depth-first search crawling with configurable depth and page limits
- **Vector Database**: ChromaDB integration with sentence transformers for semantic search
- **FastAPI Backend**: RESTful API with CORS support for frontend integration
- **Content Extraction**: Intelligent HTML parsing and content extraction
- **Rate Limiting**: Respectful crawling with configurable delays
- **Error Handling**: Robust error handling and logging

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the server:
```bash
python start.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### POST /crawl
Crawl a website and store content in vector database.

**Request Body:**
```json
{
  "url": "https://docs.example.com",
  "max_depth": 3,
  "max_pages": 100,
  "delay": 1.0
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully crawled 25 pages",
  "pages_crawled": 25,
  "total_content_length": 150000
}
```

### GET /search
Search documents in the vector database.

**Query Parameters:**
- `query`: Search query string
- `limit`: Maximum number of results (default: 10)

### DELETE /clear-database
Clear all documents from the vector database.

### GET /health
Health check endpoint.

## Configuration

The crawler supports the following configuration options:

- **max_depth**: Maximum crawling depth (default: 3)
- **max_pages**: Maximum number of pages to crawl (default: 100)
- **delay**: Delay between requests in seconds (default: 1.0)

## Architecture

### Components

1. **WebCrawler**: DFS-based web crawler with content extraction
2. **VectorStore**: ChromaDB integration with sentence transformers
3. **FastAPI App**: RESTful API server with CORS support

### Crawling Process

1. **URL Validation**: Validates URLs and filters non-content links
2. **DFS Traversal**: Uses depth-first search for efficient crawling
3. **Content Extraction**: Extracts meaningful content from HTML
4. **Vector Storage**: Stores content in ChromaDB with embeddings
5. **Rate Limiting**: Respects robots.txt and implements delays

## Error Handling

The crawler includes comprehensive error handling for:
- Network timeouts and connection errors
- Invalid URLs and redirects
- HTML parsing errors
- Vector database operations
- Rate limiting and throttling

## Logging

All operations are logged with appropriate levels:
- INFO: Successful operations and progress
- WARNING: Non-critical issues (skipped URLs, timeouts)
- ERROR: Critical failures requiring attention

## Development

To run in development mode:
```bash
ENVIRONMENT=development python start.py
```

This enables auto-reload and detailed logging.
