# TalkDocs2

A documentation chatbot that crawls websites and answers questions using the content it finds. Built with RAG (Retrieval-Augmented Generation) to provide accurate, context-aware responses from your documentation.

## What it does

TalkDocs2 lets you point it at any documentation website or GitHub repository, and it will crawl the content, understand it, and answer questions about it. Think of it as having a knowledgeable assistant that has read all your docs and can help users find what they need.

### Key capabilities

**Smart crawling** - Automatically discovers and extracts content from documentation sites, avoiding duplicates and handling different page structures.

**Intelligent storage** - Uses vector embeddings to understand document meaning, not just keywords. Each documentation source is kept separate so you can query specific docs.

**Natural conversation** - Powered by Google's Gemma AI model, it maintains conversation context and provides helpful, accurate answers based on the actual documentation content.

**Clean interface** - Terminal-inspired design that developers will feel at home with. No clutter, just focused functionality.

## How it works

The system has two main parts: a FastAPI backend that handles the heavy lifting, and a Next.js frontend that provides the chat interface.

**Backend** handles crawling websites, storing documents in ChromaDB with vector embeddings, and running the AI model. It keeps everything organized by source so you can have multiple documentation sets without them interfering with each other.

**Frontend** is a clean chat interface built with React and TypeScript. It's designed to feel like a terminal but be as easy to use as any modern web app.

When you ask a question, here's what happens: the system finds the most relevant parts of your documentation using vector similarity, passes that context to the Gemma AI model, and returns a natural response based on your actual docs.

## Getting started

You'll need Python 3.8+, Node.js 16+, and a Google Gemini API key. Get your API key from the Google AI Studio.

**Backend setup:**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
python main.py
```

**Frontend setup:**
```bash
cd frontend
npm install
npm run dev
```

The backend will run on http://localhost:8000 and the frontend on http://localhost:3000.

## Using TalkDocs2

**Adding documentation:**
1. Open the app and click Settings
2. Paste your documentation URL (like docs.example.com or a GitHub repo)
3. Click Crawl and wait for it to finish
4. The system will discover and index all the content

**Asking questions:**
1. Go back to the main chat
2. Select which documentation source you want to query
3. Ask questions naturally - the AI will find relevant information and give you helpful answers
4. The conversation remembers context, so you can ask follow-up questions

**Managing multiple sources:**
You can crawl multiple documentation sites and switch between them. Each source is kept separate, so you won't get mixed results from different docs.

## API Reference

The backend provides a REST API for programmatic access:

**Document management:**
- `POST /crawl` - Start crawling a website
- `POST /check-urls` - See which URLs are already indexed
- `GET /documents` - List all stored documents
- `GET /documents/{id}` - Get a specific document
- `DELETE /clear-database` - Clear all stored data

**Chat:**
- `POST /chat` - Send a message and get AI response
- `GET /chat/stats` - Get information about the chat service

**Source management:**
- `GET /sources` - List all available documentation sources
- `POST /sources/active` - Set which source to use for chat
- `GET /sources/active` - Get the currently active source

**Storage:**
- `POST /backup` - Create a backup of all data
- `GET /storage/info` - Get storage usage information

## Configuration

The crawler defaults work well for most documentation sites - it goes 3 levels deep, limits to 100 pages, and waits 1 second between requests to be respectful. Duplicate checking is automatic.

Documents are stored in `./data/chroma_db/` using ChromaDB with FastEmbed for vector embeddings. Raw documents are backed up to `./data/documents/` organized by source.

The AI model is Google's Gemma-3-12B-IT, configured to maintain conversation context while staying focused on documentation content.

## Project structure

```
TalkDocs2/
├── backend/                 # FastAPI backend
│   ├── main.py             # Main application
│   ├── crawler.py          # Website crawler
│   ├── vector_store.py     # ChromaDB integration
│   ├── rag_chat.py         # AI chat service
│   └── requirements.txt    # Python dependencies
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── app/           # Next.js app directory
│   │   ├── components/    # React components
│   │   └── contexts/      # React contexts
│   └── package.json       # Node dependencies
└── data/                  # Generated at runtime
    ├── chroma_db/         # Vector database storage
    └── documents/         # Raw document backups
```

## Data storage

ChromaDB handles the vector storage with separate collections for each documentation source. This keeps everything organized and prevents cross-contamination between different docs.

Raw documents are backed up as JSON files in `./data/documents/` organized by source, with metadata indexes for quick lookup.

## Development

For local development, run both the backend and frontend:

```bash
# Backend
cd backend
pip install -r requirements.txt
python main.py

# Frontend (in another terminal)
cd frontend
npm install
npm run dev
```

The backend API can be tested with curl, Postman, or directly through the frontend interface.

## Deployment

Deploy the FastAPI backend to your preferred cloud service and the Next.js frontend to any static hosting. Make sure to set the `GEMINI_API_KEY` environment variable and configure persistent storage for ChromaDB.

## Troubleshooting

**API key issues:** Make sure your `GEMINI_API_KEY` is set in the backend `.env` file.

**Crawling problems:** Check that the URL is accessible and doesn't block automated requests.

**Chat not responding:** Verify the backend is running and accessible from the frontend.

**Sources not loading:** Check that ChromaDB is running and the data directory is writable.

## Contributing

Fork the repo, make your changes, test them thoroughly, and submit a pull request.
