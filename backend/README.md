# TalkDocs2 Backend

A RAG-based chatbot backend using Google's Generative AI (Gemini) and ChromaDB for document storage and retrieval.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   - Copy `.env.example` to `.env`
   - Get your Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Add your API key to the `.env` file:
     ```
     GEMINI_API_KEY=your_gemini_api_key_here
     ```

3. **Run the backend:**
   ```bash
   python main.py
   ```
   
   The API will be available at `http://localhost:8000`

## API Endpoints

### Chat
- `POST /chat` - Chat with the RAG-powered AI assistant
- `GET /chat/stats` - Get chat service statistics

### Document Management
- `POST /crawl` - Crawl a website with duplicate checking and store documents
- `POST /check-urls` - Check which URLs already exist in the database
- `GET /search` - Search documents in the vector database
- `GET /documents` - Get metadata for all stored documents
- `GET /documents/{doc_id}` - Get a specific document by ID
- `DELETE /clear-database` - Clear all documents

### Source Management
- `GET /sources` - Get list of all available document sources
- `POST /sources/active` - Set the active source for chat and search
- `GET /sources/active` - Get the currently active source

### Storage & Backup
- `POST /backup` - Create a backup of all documents and vector database
- `GET /storage/info` - Get storage usage information

### Health
- `GET /health` - Health check
- `GET /` - API info

## Usage

1. **Check URLs before crawling:**
   ```bash
   curl -X POST "http://localhost:8000/check-urls" \
        -H "Content-Type: application/json" \
        -d '{"urls": ["https://example.com", "https://example.com/page1"]}'
   ```

2. **Crawl documents (with duplicate checking):**
   ```bash
   curl -X POST "http://localhost:8000/crawl" \
        -H "Content-Type: application/json" \
        -d '{"url": "https://example.com", "max_pages": 50}'
   ```

3. **Chat with the AI:**
   ```bash
   curl -X POST "http://localhost:8000/chat" \
        -H "Content-Type: application/json" \
        -d '{"message": "What is this documentation about?"}'
   ```

4. **View stored documents:**
   ```bash
   curl "http://localhost:8000/documents"
   ```

5. **Create a backup:**
   ```bash
   curl -X POST "http://localhost:8000/backup" \
        -H "Content-Type: application/json" \
        -d '{"backup_name": "my_backup"}'
   ```

6. **Check storage usage:**
   ```bash
   curl "http://localhost:8000/storage/info"
   ```

7. **List available sources:**
   ```bash
   curl "http://localhost:8000/sources"
   ```

8. **Set active source:**
   ```bash
   curl -X POST "http://localhost:8000/sources/active" \
        -H "Content-Type: application/json" \
        -d '{"source_id": "source_docs_python_org"}'
   ```

## Storage Architecture

### Persistent Storage
- **ChromaDB**: Vector database stored in `./data/chroma_db/`
- **Raw Documents**: JSON files stored in `./data/documents/`
- **Document Index**: Metadata index in `./data/documents/document_index.json`
- **Backups**: Automatic backups in `./data/documents/backups/`

### Data Structure
```
data/
├── chroma_db/           # ChromaDB vector database
│   ├── talkdocs_collection_source_docs_python_org/  # Source-specific collections
│   ├── talkdocs_collection_source_github_com/       # Each source has its own collection
│   └── ...
├── documents/           # Raw document storage
│   ├── source_docs_python_org/    # Source-specific directories
│   │   ├── {doc_id}.json         # Individual document files
│   │   └── source_docs_python_org_index.json  # Source-specific index
│   ├── source_github_com/
│   │   ├── {doc_id}.json
│   │   └── source_github_com_index.json
│   └── backups/        # Backup directories
│       └── backup_YYYYMMDD_HHMMSS/
└── ...
```

## Architecture

- **FastAPI**: Web framework
- **ChromaDB**: Persistent vector database for document storage
- **FastEmbed**: Lightweight embedding generation
- **Google Generative AI**: Gemma-3-12B-IT model for response generation
- **RAG (Retrieval-Augmented Generation)**: Combines document retrieval with AI generation
- **Local File Storage**: Raw document backup and management

The system works by:
1. Checking if URLs already exist before crawling to avoid duplicates
2. Crawling and storing only new documents as both raw JSON files and vector embeddings
3. When a user asks a question, retrieving relevant documents from ChromaDB
4. Using those documents as context for Gemma to generate accurate responses
5. All data persists locally and can be backed up for long-term storage

## Duplicate Prevention

The system automatically prevents duplicate content by:
- **URL Checking**: Before crawling, the system checks if URLs already exist in the database
- **Skip Existing**: If a URL is found, the system retrieves the existing document instead of re-crawling
- **Efficient Storage**: Only new content is processed and stored, saving time and resources
- **Progress Tracking**: The crawler shows both new pages crawled and existing documents retrieved

## Source Separation

The system now supports complete source isolation:
- **Separate Collections**: Each URL domain gets its own ChromaDB collection
- **Isolated Storage**: Documents are stored in source-specific directories
- **Source Selection**: Frontend dropdown allows users to select which documentation to search
- **No Cross-Contamination**: Results from different sources never mix
- **Source Management**: Easy switching between different documentation sources

### Key Benefits:
- **Clean Separation**: Each documentation source is completely isolated
- **Focused Results**: AI only searches within the selected source
- **Easy Management**: Simple dropdown to switch between sources
- **Scalable**: Support unlimited documentation sources
- **User Control**: Users choose which documentation to query

## Enhanced Response Formatting

The AI assistant now provides beautifully formatted responses with:
- **Markdown Support**: Full markdown formatting with headers, lists, tables, and more
- **Syntax Highlighting**: Code blocks with proper syntax highlighting for multiple languages
- **Copy Functionality**: Easy copying of code snippets and entire responses
- **Responsive Design**: Optimized for both desktop and mobile viewing
- **Theme Support**: Consistent styling across light and dark themes

### Supported Formatting:
- **Headers** (H1-H6) with proper hierarchy
- **Code blocks** with syntax highlighting
- **Inline code** with terminal-style formatting
- **Lists** (ordered and unordered)
- **Tables** with borders and styling
- **Blockquotes** for important notes
- **Links** that open in new tabs
- **Bold** and *italic* text formatting
- **Horizontal rules** for section separation

## Enhanced Conversation Context

The chatbot now maintains rich conversation context by:
- **Conversation Memory**: Remembers up to 20 previous messages for context
- **Contextual Responses**: References previous questions and answers for continuity
- **Follow-up Support**: Builds upon earlier topics and provides related information
- **Smart Context Management**: Optimizes context length to avoid token limits
- **Conversational Flow**: Maintains natural conversation flow across multiple exchanges

### Context Features:
- **Previous Message Integration**: Uses recent conversation history to provide better responses
- **Topic Continuity**: References earlier topics when relevant
- **Follow-up Questions**: Understands and responds to follow-up questions in context
- **Context Optimization**: Automatically manages context length for optimal performance