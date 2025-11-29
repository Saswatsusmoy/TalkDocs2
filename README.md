# TalkDocs2

A documentation chatbot that crawls websites and answers questions using the content it finds. Built with RAG (Retrieval-Augmented Generation) to provide accurate, context-aware responses from your documentation.

## What it does

TalkDocs2 lets you point it at any documentation website or GitHub repository, and it will crawl the content, understand it, and answer questions about it. Think of it as having a knowledgeable assistant that has read all your docs and can help users find what they need.

### Key capabilities

**Smart crawling** - Automatically discovers and extracts content from documentation sites, avoiding duplicates and handling different page structures.

**Intelligent storage** - Uses vector embeddings to understand document meaning, not just keywords. Each documentation source is kept separate so you can query specific docs.

**Natural conversation** - Uses a Retrieval-Augmented Generation (RAG) pipeline on top of either a **local LM Studio model** or **Google Gemini**, maintaining conversation context and providing helpful, accurate answers based on the actual documentation content.

**Clean interface** - Terminal-inspired design that developers will feel at home with. No clutter, just focused functionality.

---

## Quickstart (local dev)

1. **Clone and install**
   - **Backend**
     ```bash
     cd backend
     pip install -r requirements.txt
     ```
   - **Frontend**
     ```bash
     cd frontend
     npm install
     ```

2. **Configure AI provider**
   - **Option A – Local (default): LM Studio**
     - Install LM Studio and start a chat model with an OpenAI-compatible server.
     - By default the backend expects it at `http://localhost:1234/v1`.
   - **Option B – Cloud: Gemini**
     - Get an API key from Google AI Studio.
     - Set `MODEL_PROVIDER=gemini` and `GEMINI_API_KEY=...` in `backend/.env`.

3. **Run the stack**
   ```bash
   # Backend
   cd backend
   python start.py   # or: python main.py

   # Frontend (in another terminal)
   cd frontend
   npm run dev
   ```

4. **Open the app**
   - Backend: `http://localhost:8000`
   - Frontend: `http://localhost:3000`

---

## How it works

The system has two main parts: a FastAPI backend that handles the heavy lifting, and a Next.js frontend that provides the chat interface.

**Backend** handles crawling websites, storing documents in ChromaDB with vector embeddings, and running the AI model. It keeps everything organized by source so you can have multiple documentation sets without them interfering with each other.

**Frontend** is a clean chat interface built with React and TypeScript. It's designed to feel like a terminal but be as easy to use as any modern web app.

When you ask a question, here's what happens: the system finds the most relevant parts of your documentation using vector similarity, passes that context to the Gemma AI model, and returns a natural response based on your actual docs.

## Getting started

You'll need:

- **Python**: 3.10+ (3.12 recommended)
- **Node.js**: 18+ (LTS recommended)
- **Package managers**: `pip` and `npm`
- **AI provider**:
  - For **local**: LM Studio running with an OpenAI-compatible HTTP server, or
  - For **cloud**: a Google Gemini API key from Google AI Studio

**Backend setup:**
```bash
cd backend
pip install -r requirements.txt
# (optional but recommended) create a .env file and configure MODEL_PROVIDER + keys
# e.g. MODEL_PROVIDER=lm_studio or MODEL_PROVIDER=gemini
python start.py   # development entrypoint (reload enabled when ENVIRONMENT=development)
# or:
# python main.py  # simple uvicorn runner
```

**Frontend setup:**
```bash
cd frontend
npm install
npm run dev
```

The backend will run on http://localhost:8000 and the frontend on http://localhost:3000.

---

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

---

## Command Line Interface (CLI)

TalkDocs2 includes a powerful CLI for terminal-based interaction. After installing dependencies, you can use it from the backend directory:

> The CLI uses the **same vector store, model provider, and environment variables** as the backend API.

### Basic Usage

**Interactive Mode (Default):**
```bash
cd backend
python cli.py
```

This launches an interactive menu that stays open until you choose to exit. You can navigate through all features using the menu.

**Command Mode:**
```bash
python cli.py --help
python cli.py crawl https://docs.example.com
python cli.py chat "What is MLX?"
```

You can also use individual commands directly without entering interactive mode.

### Interactive Menu

When you run `python cli.py` without any arguments, you'll see an interactive menu:

```
╔═══════════════════════════════════════════════════════════╗
║           TalkDocs2 - Documentation Chatbot           ║
╚═══════════════════════════════════════════════════════════╝

Main Menu:

  1.  Chat with Documentation (Interactive)
  2.  Chat with Documentation (Single Query)
  3.  Crawl Website
  4.  Manage Sources
  5.  Search Documents
  6.  Manage AI Provider
  7.  View Statistics
  8.  Clear Database
  9.  Exit
```

Simply select a number to access that feature. The menu will return after each operation, allowing you to perform multiple tasks in one session. Press `Ctrl+C` or select option 9 to exit.

### Commands

**Crawl a website:**
```bash
python cli.py crawl https://docs.example.com --depth 3 --pages 100
```

**Chat with documentation (single query):**
```bash
python cli.py chat "What is MLX?"
```

**Interactive chat mode:**
```bash
python cli.py chat --interactive
```

**List all sources:**
```bash
python cli.py sources
```

**Set active source:**
```bash
python cli.py sources --set source_example_com
```

**Delete a source:**
```bash
python cli.py sources --delete source_example_com
```

**Search documents:**
```bash
python cli.py search "machine learning" --limit 10
```

**Manage AI model provider:**
```bash
# Get current provider
python cli.py provider --get

# Switch to Gemini
python cli.py provider --set gemini

# Switch to LM Studio
python cli.py provider --set lm_studio
```

**View system statistics:**
```bash
python cli.py stats
```

**Clear all data:**
```bash
python cli.py clear
```

### CLI Options

- `crawl <url>` - Crawl and index a website
  - `--depth, -d` - Maximum crawl depth (default: 3)
  - `--pages, -p` - Maximum pages to crawl (default: 100)
  - `--delay` - Delay between requests in seconds (default: 1.0)

- `chat [query]` - Chat with documentation
  - `--interactive, -i` - Start interactive chat mode
  - `--source, -s` - Source ID to use

- `sources` - Manage documentation sources
  - `--list, -l` - List all sources (default)
  - `--set, -s <id>` - Set active source
  - `--delete, -d <id>` - Delete a source

- `provider` - Manage AI model provider
  - `--get, -g` - Get current provider
  - `--set, -s <provider>` - Set provider (lm_studio or gemini)

- `search <query>` - Search documents
  - `--limit, -l` - Number of results (default: 10)
  - `--source, -s` - Source ID to search

- `stats` - Show system statistics

- `clear` - Clear all documents (with confirmation)

---

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

---

## Configuration

### Crawler defaults

The crawler defaults work well for most documentation sites:

- **Depth**: 3 levels deep
- **Pages**: 100–1000 pages (API default vs CLI default)
- **Request delay**: ~0.3–1.0 seconds between requests

Duplicate checking is automatic and prevents re‑indexing the same pages.

### Storage locations

Documents are stored in `./data/chroma_db/` using ChromaDB with FastEmbed for vector embeddings. Raw documents are backed up to `./data/documents/` organized by source.

### Model providers & environment variables

TalkDocs2 supports two model providers:

- **LM Studio (local, default)**
- **Google Gemini (cloud)**

Configure them via environment variables in `backend/.env` (loaded with `python-dotenv`):

#### Core selection

- **`MODEL_PROVIDER`** (optional, default: `lm_studio`)
  - `lm_studio` – use a local model served by LM Studio
  - `gemini` – use Google Gemini via `google-generativeai`

#### When using LM Studio (`MODEL_PROVIDER=lm_studio`)

- **`LM_STUDIO_BASE_URL`** (optional, default: `http://localhost:1234/v1`)
  - Must point to an OpenAI-compatible server started by LM Studio.
- **`LM_STUDIO_MODEL`** (optional, default: `local-model`)
  - The model identifier configured in LM Studio.
- **`LM_STUDIO_API_KEY`** (optional, default: `lm-studio`)
  - Dummy key used to satisfy the OpenAI client; LM Studio does not require it by default.

#### When using Gemini (`MODEL_PROVIDER=gemini`)

- **`GEMINI_API_KEY`** (required)
  - Your API key from Google AI Studio.
- **`GEMINI_MODEL`** (optional, default: `models/gemini-flash-lite-latest`)
  - Any text-capable Gemini model ID.
- **`GEMINI_MAX_OUTPUT_TOKENS`** (optional, default: `32768`)
  - Upper bound on tokens per response.

#### RAG & reranking tuning (optional)

These control how much context is used and how results are re-ranked:

- **`USE_NEURAL_RERANKER`**: `true`/`false` (default: `true`)
  - Uses a `sentence-transformers` cross‑encoder when available; otherwise falls back to rule-based reranking.
- **`RERANKER_MODEL`** (optional, default: `cross-encoder/ms-marco-MiniLM-L-6-v2`)
  - Cross-encoder model name for reranking.
- **`MAX_HISTORY_MESSAGES`** (default: `20`)
- **`MAX_HISTORY_CHARS`** (default: `8000`)
- **`MAX_MESSAGE_CHARS`** (default: `2000`)
- **`MAX_CONTEXT_CHARS`** (default: `12000`)
- **`MAX_DOC_CHARS`** (default: `2000`)

These limits keep prompts efficient while still giving the model enough context to answer well.

---

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

---

## Data storage

ChromaDB handles the vector storage with separate collections for each documentation source. This keeps everything organized and prevents cross-contamination between different docs.

Raw documents are backed up as JSON files in `./data/documents/` organized by source, with metadata indexes for quick lookup.

---

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

---

## Deployment

Deploy the FastAPI backend to your preferred cloud service and the Next.js frontend to any static hosting.

- **Backend**
  - Expose port `8000` (or your chosen port).
  - Mount a persistent volume for `backend/data/` so ChromaDB and document backups survive restarts.
  - Set environment variables for your chosen provider (`MODEL_PROVIDER`, and either LM Studio or Gemini vars).
- **Frontend**
  - Configure the API base URL (if different from `http://localhost:8000`).

For **LM Studio** in production, ensure the LM Studio server is reachable from the backend.  
For **Gemini**, ensure outbound network access to the Google Generative AI API.

---

## Troubleshooting

**API key issues:** Make sure your `GEMINI_API_KEY` is set in the backend `.env` file.

**Crawling problems:** Check that the URL is accessible and doesn't block automated requests.

**Chat not responding:** Verify the backend is running and accessible from the frontend.

**Sources not loading:** Check that ChromaDB is running and the data directory is writable.

If something fails unexpectedly, also check:

- Backend logs from `python start.py` or your process manager
- That your `MODEL_PROVIDER` and related env vars are consistent (e.g., not pointing to LM Studio without a running server)

---

## Contributing

Fork the repo, make your changes, test them thoroughly, and submit a pull request.
