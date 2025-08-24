# 🤖 TalkDocs - AI-Powered Code Documentation Assistant

> **Transform any documentation website into an intelligent AI assistant for developers**

TalkDocs is a powerful AI-driven tool that crawls documentation websites and provides instant, contextual help for developers. No more manual searching through pages - get instant answers about APIs, functions, configuration, and implementation details through natural language chat.

## 🎯 **What Problem Does TalkDocs Solve?**

### **The Developer Documentation Challenge**

- ❌ **Manual Navigation**: Spending hours clicking through documentation pages
- ❌ **Context Switching**: Constantly switching between browser tabs and code editor
- ❌ **Information Overload**: Struggling to find specific implementation details
- ❌ **Time Waste**: Reading irrelevant sections to find what you need
- ❌ **Version Confusion**: Unsure if you're looking at the right documentation version

### **TalkDocs Solution**

- ✅ **Instant Answers**: Ask questions in natural language, get precise answers
- ✅ **Context-Aware**: AI understands your specific documentation context
- ✅ **Code Examples**: Get relevant code snippets and implementation patterns
- ✅ **API Understanding**: Quick explanations of functions, parameters, and usage
- ✅ **Troubleshooting**: Find solutions to common issues and debugging help
- ✅ **Integration Guidance**: Understand setup, configuration, and best practices

## 🏗️ **System Architecture**

### **High-Level Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Interface │    │   CLI Interface │    │   User Input    │
│   (Streamlit)   │    │   (talkdocs_cli)│    │   (Questions)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                        ┌─────────────────┐
                        │   Core Engine   │
                        │   (TalkDocs)    │
                        └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Web Crawler    │    │   AI Chatbot    │    │  Data Storage   │
│  (web_crawler)  │    │  (chatbot)      │    │   (JSON Files)  │
│  + Portia AI    │    │  (Google AI)    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Component Architecture**

#### **1. Web Crawler Module** (`web_crawler.py`)

```python
class WebCrawler:
    ├── Selenium WebDriver (Chrome headless)
    ├── BeautifulSoup Parser (HTML parsing)
    ├── Requests Session (HTTP requests)
    ├── URL Discovery & Filtering
    ├── Content Extraction & Cleaning
    ├── Sitemap Generation
    ├── Rate Limiting & Delays
    └── JSON Data Export
```

#### **2. AI Chatbot Module** (`chatbot.py`)

```python
class DocumentChatbot:
    ├── Google Generative AI (Gemini)
    ├── RAG (Retrieval-Augmented Generation)
    ├── Document Context Management
    ├── Query Processing & Embedding
    ├── Response Generation
    ├── Source Attribution
    └── JSON Document Loading
```

#### **3. Portia AI Integration** (`portia_web_tools.py`)

```python
class WebCrawlerTool:
    ├── Portia AI SDK Integration
    ├── Enhanced Web Crawling
    ├── Structured Data Extraction
    └── JSON Output Formatting

class WebExtractorTool:
    ├── Single URL Content Extraction
    ├── Link Extraction
    └── Selenium Force Mode

class WebSitemapTool:
    ├── Advanced Sitemap Generation
    ├── URL Discovery
    └── File Export Options

class BulkWebExtractorTool:
    ├── Concurrent URL Processing
    ├── Rate Limiting
    └── Batch Processing
```

#### **4. Web Interface** (`app.py`)

```python
class StreamlitApp:
    ├── ChatGPT-style UI (Dark Mode)
    ├── Session State Management
    ├── File Upload & Processing
    ├── Real-time Chat Interface
    ├── Portia AI Integration
    ├── Custom CSS Styling
    └── Error Handling & Fallbacks
```

#### **5. CLI Interface** (`talkdocs_cli.py`)

```python
class TalkDocsCLI:
    ├── Argument Parsing (argparse)
    ├── Colored Terminal Output
    ├── Interactive Chat Mode
    ├── Single Question Mode
    ├── Data Management Commands
    ├── Portia AI Integration
    └── Silent Fallback Handling
```

#### **6. Data Storage**

```python
File Structure:
    ├── crawled_data_*.json (Crawled website data)
    ├── portia_output_*.txt (Portia AI logs)
    ├── sitemap_*.json (Generated sitemaps)
    └── .env (Environment variables)
```

### **Technical Architecture & Data Flow**

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Layer                               │
├─────────────────────────────────────────────────────────────────┤
│  Web Interface (app.py)    │    CLI Interface (talkdocs_cli.py) │
│  └── Streamlit UI          │    └── Command Line                │
│  └── Session Management    │    └── Colored Output              │
│  └── File Upload           │    └── Interactive Chat            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Core Engine Layer                          │
├─────────────────────────────────────────────────────────────────┤
│  Web Crawler (web_crawler.py)  │  AI Chatbot (chatbot.py)       │
│  ├── Selenium WebDriver        │  ├── Google Generative AI      │
│  ├── BeautifulSoup Parser      │  ├── RAG Implementation        │
│  ├── URL Discovery             │  ├── Document Context          │
│  ├── Content Extraction        │  ├── Query Processing          │
│  └── JSON Export               │  └── Response Generation       │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Portia AI Layer                             │
├─────────────────────────────────────────────────────────────────┤
│  Portia Tools (portia_web_tools.py)                             │
│  ├── WebCrawlerTool (Enhanced crawling)                         │
│  ├── WebExtractorTool (Single URL extraction)                   │
│  ├── WebSitemapTool (Sitemap generation)                        │
│  └── BulkWebExtractorTool (Batch processing)                    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Storage Layer                         │
├─────────────────────────────────────────────────────────────────┤
│  Local File System                                              │
│  ├── crawled_data_*.json (Website data)                         │
│  ├── portia_output_*.txt (Portia logs)                          │
│  ├── sitemap_*.json (Generated sitemaps)                        │
│  └── .env (Environment variables)                               │
└─────────────────────────────────────────────────────────────────┘
```

### **File Dependencies & Imports**

```
app.py
├── web_crawler.py
├── chatbot.py
├── portia_web_tools.py
└── streamlit (UI framework)

talkdocs_cli.py
├── web_crawler.py
├── chatbot.py
├── portia_web_tools.py
└── argparse (CLI framework)

web_crawler.py
├── selenium (Browser automation)
├── beautifulsoup4 (HTML parsing)
├── requests (HTTP requests)
└── webdriver_manager (Chrome driver)

chatbot.py
├── google.generativeai (AI model)
├── dotenv (Environment variables)
└── typing (Type hints)

portia_web_tools.py
├── portia (Portia AI SDK)
├── pydantic (Data validation)
├── web_crawler.py (Reuses existing crawler)
└── logging (Error handling)
```

### **Data Flow Architecture**

```
1. User Input → Web Interface/CLI
   ↓
2. URL Validation → Web Crawler
   ↓
3. Crawling Process → Selenium + BeautifulSoup
   ↓
4. Content Extraction → Structured Data
   ↓
5. JSON Storage → Local Files
   ↓
6. Document Loading → AI Chatbot
   ↓
7. Query Processing → RAG Implementation
   ↓
8. AI Response → Google Generative AI
   ↓
9. Formatted Output → User Interface
```

## 🚀 **Features Overview**

### **Core Features**

- 🔍 **Intelligent Web Crawling**: Advanced crawling with Selenium and BeautifulSoup
- 🤖 **AI-Powered Chat**: Context-aware responses using Google AI (Gemini)
- 📚 **Documentation Focus**: Specialized for code documentation and APIs
- 🔄 **RAG Integration**: Retrieval-Augmented Generation for accurate answers
- 🎨 **Modern UI**: ChatGPT-style interface with dark mode
- 💻 **CLI Interface**: Full-featured command-line tool
- 🔧 **Silent Fallback**: Graceful degradation when Portia AI unavailable

### **🚀 Portia AI Integration**

TalkDocs includes advanced integration with **Portia AI**, a powerful AI-driven web extraction platform that significantly enhances crawling capabilities:

#### **Portia AI Features**

- 🧠 **AI-Powered Extraction**: Intelligent content understanding and extraction
- 🎯 **Smart Content Recognition**: Automatically identifies documentation structure
- 🔍 **Advanced Parsing**: Handles complex layouts, dynamic content, and JavaScript-heavy sites
- 📊 **Structured Data Extraction**: Extracts tables, code blocks, and formatted content
- 🚀 **Performance Optimization**: Faster and more accurate than traditional crawling
- 🔄 **Automatic Fallback**: Seamlessly falls back to standard crawler if Portia AI is unavailable

#### **When to Use Portia AI**

- **Complex Documentation Sites**: Sites with dynamic content, JavaScript rendering
- **API Documentation**: Structured documentation with code examples
- **Large Documentation**: Sites with hundreds of pages
- **Modern Web Apps**: Single-page applications (SPAs) and React/Vue sites
- **Protected Content**: Sites with anti-bot measures

#### **Portia AI vs Standard Crawler**

| Feature                         | Standard Crawler | Portia AI              |
| ------------------------------- | ---------------- | ---------------------- |
| **Speed**                 | Fast             | Very Fast              |
| **Accuracy**              | Good             | Excellent              |
| **Complex Sites**         | Limited          | Excellent              |
| **JavaScript Support**    | Basic            | Advanced               |
| **Content Understanding** | Basic            | AI-Powered             |
| **Setup Complexity**      | Simple           | Simple                 |
| **Cost**                  | Free             | Free (with API limits) |

#### **Portia AI Installation**

```bash
# Install Portia AI SDK
pip install portia-sdk-python

# Set up Portia AI credentials (optional)
export PORTIA_API_KEY="your-portia-api-key"
```

#### **Portia AI Usage Examples**

```bash
# CLI with Portia AI
python talkdocs_cli.py crawl https://docs.python.org --use-portia --max-pages 100

# Web interface automatically uses Portia AI when available
# Just click "Crawl Website" and Portia AI will be used if installed
```

### **Advanced Features**

- 📊 **Sitemap Generation**: Automatic website structure mapping
- 🎯 **Content Filtering**: Smart filtering of relevant documentation
- 🔗 **Source Attribution**: Always know where answers come from
- 📱 **Responsive Design**: Works on desktop and mobile
- 🎨 **Custom Styling**: Beautiful, modern interface
- ⚡ **Performance Optimized**: Fast crawling and response times

## 📋 **Requirements**

### **System Requirements**

- **Python**: 3.7 or higher
- **Memory**: 4GB RAM minimum (8GB recommended)
- **Storage**: 1GB free space for data storage
- **Network**: Stable internet connection for crawling and AI

### **Python Dependencies**

```bash
# Core dependencies
streamlit>=1.28.0
google-generativeai>=0.3.0
beautifulsoup4>=4.12.0
selenium>=4.15.0
requests>=2.31.0
validators>=0.22.0
python-dotenv>=1.0.0
portia-sdk-python>=1.0.0  # For enhanced crawling
webdriver-manager>=4.0.0  # For Chrome driver management
```

### **API Requirements**

- **Google AI API Key**: Required for chatbot functionality
- **Chrome Browser**: Required for Selenium-based crawling

## 🛠️ **Installation**

### **1. Clone the Repository**

```bash
git clone https://github.com/yourusername/talkdocs.git
cd talkdocs
```

### **2. Create Virtual Environment**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### **3. Install Dependencies**

```bash
pip install -r requirements.txt
```

### **4. Set Up API Key**

```bash
# Option 1: Environment variable
export GOOGLE_API_KEY="your-google-ai-api-key-here"

# Option 2: .env file
echo "GOOGLE_API_KEY=your-google-ai-api-key-here" > .env

# Option 3: Set in web interface
# (Will be prompted when you first run the app)
```

### **5. Verify Installation**

```bash
# Test CLI
python talkdocs_cli.py --help

# Test web interface
streamlit run app.py
```

## 🎯 **Quick Start Guide**

### **Web Interface Quick Start**

```bash
# 1. Start the application
streamlit run app.py

# 2. Enter your Google AI API key in the sidebar

# 3. Crawl a documentation website
# Example: Python Requests library documentation
URL: https://docs.python-requests.org/en/latest/
Max Pages: 50
Delay: 1.0 seconds

# 4. Load documents and start chatting
# Ask questions like:
# - "How do I make a POST request with JSON data?"
# - "What are the parameters for requests.get()?"
# - "How do I handle authentication with requests?"
```

### **CLI Quick Start**

```bash
# 1. Crawl a documentation website
python talkdocs_cli.py crawl https://docs.python.org/3/library/requests.html --max-pages 100

# 2. Start interactive chat
python talkdocs_cli.py chat --load-url https://docs.python.org/3/library/requests.html

# 3. Ask specific questions
python talkdocs_cli.py ask "How do I make a POST request?" --load-url https://docs.python.org/3/library/requests.html

# 4. Get document summary
python talkdocs_cli.py summary --load-url https://docs.python.org/3/library/requests.html
```

## 💻 **Usage Examples**

### **Web Interface Usage**

#### **Crawling Documentation Sites**

```bash
# Python Documentation
URL: https://docs.python.org/3/
Max Pages: 200
Delay: 1.0s

# React Documentation
URL: https://react.dev/reference/react
Max Pages: 150
Delay: 1.5s

# Docker Documentation
URL: https://docs.docker.com/
Max Pages: 100
Delay: 1.0s

# FastAPI Documentation
URL: https://fastapi.tiangolo.com/
Max Pages: 80
Delay: 1.0s
```

#### **Common Questions to Ask**

```bash
# API Questions
"How do I make an HTTP POST request with authentication?"
"What are the required parameters for the login endpoint?"
"How do I handle rate limiting in the API?"

# Configuration Questions
"What are the available configuration options?"
"How do I set up environment variables?"
"What's the difference between development and production configs?"

# Implementation Questions
"How do I implement pagination in my API?"
"What's the best way to handle errors?"
"How do I add middleware to my application?"

# Troubleshooting Questions
"Why am I getting a 401 Unauthorized error?"
"How do I debug connection timeouts?"
"What does this error message mean?"
```

### **CLI Usage Examples**

#### **Basic Crawling**

```bash
# Crawl Python documentation
python talkdocs_cli.py crawl https://docs.python.org/3/ --max-pages 100

# Crawl with custom settings
python talkdocs_cli.py crawl https://docs.python.org/3/ \
  --max-pages 200 \
  --delay 0.5 \
  --no-sitemap

# Use Portia AI for enhanced crawling
python talkdocs_cli.py crawl https://docs.python.org/3/ --use-portia

# Portia AI with complex JavaScript sites
python talkdocs_cli.py crawl https://vuejs.org/guide/ --use-portia --max-pages 100

# Portia AI for API documentation
python talkdocs_cli.py crawl https://developer.mozilla.org/en-US/docs/Web/API --use-portia --max-pages 200

# Portia AI with custom delay for rate limiting
python talkdocs_cli.py crawl https://react.dev/reference/ --use-portia --delay 2.0 --max-pages 150
```

#### **Interactive Chat Sessions**

```bash
# Start chat with specific data file
python talkdocs_cli.py chat --load-file crawled_data_123.json

# Start chat with URL (auto-finds data)
python talkdocs_cli.py chat --load-url https://docs.python.org/3/

# Chat with API key override
python talkdocs_cli.py chat --load-url https://docs.python.org/3/ --api-key "your-key"
```

#### **Single Question Mode**

```bash
# Ask specific questions
python talkdocs_cli.py ask "How do I use the requests library?" \
  --load-url https://docs.python.org/3/library/requests.html

# Get implementation help
python talkdocs_cli.py ask "Show me code examples for POST requests" \
  --load-file crawled_data_requests.json

# Troubleshooting help
python talkdocs_cli.py ask "How do I handle SSL certificate errors?" \
  --load-url https://docs.python.org/3/library/requests.html
```

#### **Data Management**

```bash
# List all crawled data
python talkdocs_cli.py list

# Get document summary
python talkdocs_cli.py summary --load-url https://docs.python.org/3/

# Clear all data
python talkdocs_cli.py clear
```

## 🏗️ **Advanced Configuration**

### **Environment Variables**

```bash
# Required
GOOGLE_API_KEY=your-google-ai-api-key

# Optional
TALKDOCS_DATA_DIR=/path/to/data/directory
TALKDOCS_LOG_LEVEL=INFO
TALKDOCS_MAX_WORKERS=4
TALKDOCS_TIMEOUT=30
```

### **Configuration File**

Create `config.yaml` for advanced settings:

```yaml
# Crawler settings
crawler:
  default_max_pages: 100
  default_delay: 1.0
  user_agent: "TalkDocs/1.0 (Documentation Assistant)"
  timeout: 30
  retry_attempts: 3

# AI settings
ai:
  model: "gemini-3-12b-it"
  max_tokens: 2048
  temperature: 0.7
  top_k: 3

# Storage settings
storage:
  data_directory: "./data"
  backup_enabled: true
  compression_enabled: true

# UI settings
ui:
  theme: "dark"
  page_size: 20
  auto_refresh: true
```

### **Custom Crawling Rules**

```python
# Create custom_crawler.py
from web_crawler import WebCrawler

class CustomCrawler(WebCrawler):
    def is_valid_url(self, url):
        # Custom URL filtering logic
        if 'api' in url.lower():
            return True
        if 'docs' in url.lower():
            return True
        return False
  
    def extract_content(self, soup):
        # Custom content extraction
        content = super().extract_content(soup)
        # Add custom processing
        return content
```

## 🔧 **Troubleshooting**

### **Common Issues**

#### **1. API Key Issues**

```bash
# Error: Google AI API key not found!
# Solution: Set environment variable
export GOOGLE_API_KEY="your-api-key"

# Or use --api-key option
python talkdocs_cli.py chat --api-key "your-api-key"
```

#### **2. Crawling Issues**

```bash
# Error: No pages were crawled successfully
# Solutions:
# 1. Check internet connection
# 2. Verify URL is accessible
# 3. Try with --delay 2.0 (slower crawling)
# 4. Check if site blocks crawlers

# Error: Selenium WebDriver issues
# Solution: Install Chrome and ChromeDriver
pip install webdriver-manager
```

#### **3. Memory Issues**

```bash
# Error: Out of memory during crawling
# Solutions:
# 1. Reduce --max-pages
# 2. Increase system RAM
# 3. Use --no-sitemap to reduce memory usage
```

#### **4. Portia AI Issues**

```bash
# Error: Portia AI SDK not available
# Solution: Install Portia AI SDK
pip install portia-sdk-python

# Error: Portia AI API key not found
# Solution: Set up API key (optional)
export PORTIA_API_KEY="your-portia-api-key"

# Error: Portia AI crawling failed
# Solution: TalkDocs automatically falls back to standard crawler
# No action needed - this is handled silently

# Error: Portia AI rate limit exceeded
# Solution: Wait and retry, or use standard crawler
python talkdocs_cli.py crawl https://example.com --max-pages 50

# Error: Portia AI timeout
# Solution: Reduce max_pages or increase delay
python talkdocs_cli.py crawl https://example.com --max-pages 20 --delay 3.0

# Portia AI not working on specific site
# Solution: Use standard crawler for that site
python talkdocs_cli.py crawl https://problematic-site.com --max-pages 50

# Note: TalkDocs automatically falls back to standard crawler when Portia AI fails
```

### **Performance Optimization**

#### **Crawling Performance**

```bash
# Fast crawling (use with caution)
python talkdocs_cli.py crawl https://example.com --delay 0.1 --max-pages 50

# Balanced crawling (recommended)
python talkdocs_cli.py crawl https://example.com --delay 1.0 --max-pages 100

# Conservative crawling (for sensitive sites)
python talkdocs_cli.py crawl https://example.com --delay 2.0 --max-pages 200

# Portia AI optimized crawling
python talkdocs_cli.py crawl https://example.com --use-portia --max-pages 200 --delay 0.5

# Portia AI for complex sites
python talkdocs_cli.py crawl https://complex-site.com --use-portia --max-pages 100 --delay 1.0
```

#### **Portia AI Performance Tips**

```bash
# For large documentation sites
python talkdocs_cli.py crawl https://docs.example.com --use-portia --max-pages 500 --delay 0.3

# For JavaScript-heavy sites
python talkdocs_cli.py crawl https://spa.example.com --use-portia --max-pages 100 --delay 1.0

# For API documentation
python talkdocs_cli.py crawl https://api.example.com --use-portia --max-pages 300 --delay 0.5
```

#### **AI Response Optimization**

```python
# In chatbot.py, adjust these parameters:
MAX_TOKENS = 2048  # Reduce for faster responses
TEMPERATURE = 0.7  # Lower for more focused answers
TOP_K = 3         # Reduce for faster retrieval
```

## 🔒 **Security & Best Practices**

### **Security Considerations**

- 🔑 **API Key Protection**: Never commit API keys to version control
- 🌐 **Respectful Crawling**: Use appropriate delays and respect robots.txt
- 📊 **Data Privacy**: Crawled data is stored locally by default
- 🔒 **Access Control**: Implement proper access controls for shared data

### **Best Practices**

```bash
# 1. Use environment variables for sensitive data
export GOOGLE_API_KEY="your-key"

# 2. Implement rate limiting
python talkdocs_cli.py crawl https://example.com --delay 2.0

# 3. Regular data cleanup
python talkdocs_cli.py clear  # Remove old data

# 4. Backup important data
cp crawled_data_*.json ./backups/

# 5. Monitor resource usage
# Check memory and disk usage regularly
```

### **Ethical Crawling Guidelines**

- ✅ **Respect robots.txt**: Always check and follow robots.txt
- ✅ **Reasonable Delays**: Use delays of 1-2 seconds between requests
- ✅ **Limited Scope**: Only crawl necessary documentation pages
- ✅ **Attribution**: Always provide source attribution in responses
- ✅ **Fair Use**: Use crawled data for personal/educational purposes

## 📊 **Monitoring & Analytics**

### **Built-in Monitoring**

```bash
# Check crawling statistics
python talkdocs_cli.py stats --period daily

# Monitor data usage
python talkdocs_cli.py stats --metrics storage

# View performance metrics
python talkdocs_cli.py stats --metrics performance
```

### **Custom Analytics**

```python
# Create custom analytics script
import json
import os
from datetime import datetime

def analyze_usage():
    data_files = [f for f in os.listdir('.') if f.startswith('crawled_data_')]
  
    total_pages = 0
    total_size = 0
  
    for file in data_files:
        with open(file, 'r') as f:
            data = json.load(f)
            total_pages += len(data.get('pages', []))
            total_size += os.path.getsize(file)
  
    print(f"Total pages crawled: {total_pages}")
    print(f"Total data size: {total_size / 1024 / 1024:.2f} MB")
```

## 🚀 **Deployment Options**

### **Local Development**

```bash
# Standard local setup
git clone https://github.com/yourusername/talkdocs.git
cd talkdocs
pip install -r requirements.txt
streamlit run app.py
```

### **Docker Deployment**

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
# Build and run
docker build -t talkdocs .
docker run -p 8501:8501 -e GOOGLE_API_KEY="your-key" talkdocs
```

## 🤝 **Contributing**

### **Development Setup**

```bash
# Fork and clone
git clone https://github.com/yourusername/talkdocs.git
cd talkdocs

# Create development branch
git checkout -b feature/new-feature

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Run linting
flake8 .
black .
```

### **Contributing Guidelines**

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Add tests for new features**
5. **Update documentation**
6. **Submit a pull request**

### **Code Style**

```python
# Follow PEP 8 guidelines
# Use type hints
def crawl_website(url: str, max_pages: int = 50) -> bool:
    """Crawl a website and return success status."""
    pass

# Add docstrings for all functions
# Use meaningful variable names
# Keep functions small and focused
```

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### **FAQ**

#### **Q: Can I use TalkDocs for non-documentation websites?**

A: Yes, but it's optimized for documentation sites. For general websites, you may need to adjust crawling parameters.

#### **Q: How much does it cost to run TalkDocs?**

A: TalkDocs is free to use. You only pay for Google AI API usage, which is typically very low cost for documentation queries.

#### **Q: Can I use my own AI model instead of Google AI?**

A: Yes, you can modify the chatbot.py file to use other AI providers like OpenAI, Anthropic, or local models.

#### **Q: Can I deploy TalkDocs in a corporate environment?**

A: Yes, TalkDocs can be deployed on-premises or in private clouds. All components are self-contained.

#### **Q: What's the difference between Portia AI and the standard crawler?**

A: Portia AI provides AI-powered web extraction with better handling of complex sites, JavaScript-heavy pages, and structured content. The standard crawler uses Selenium and BeautifulSoup for basic crawling. TalkDocs automatically uses Portia AI when available and falls back to standard crawler when needed.

#### **Q: Do I need a Portia AI API key?**

A: No, Portia AI SDK can work without an API key for basic functionality. However, some advanced features may require authentication. TalkDocs works perfectly with or without Portia AI credentials.

#### **Q: When should I use Portia AI vs standard crawler?**

A: Use Portia AI for complex documentation sites, JavaScript-heavy pages, API documentation, and large sites. Use standard crawler for simple sites or when you want to avoid any external dependencies.

## 🎉 **Acknowledgments**

- **Portia AI** - For Providing custom tool functions to build the custom optimized web_crawler and extractor
- **Google AI**: For providing the Gemini API
- **Streamlit**: For the excellent web framework
- **BeautifulSoup**: For HTML parsing capabilities
- **Selenium**: For JavaScript-heavy site crawling
- **Open Source Community**: For all the amazing libraries that make this possible

---

**Made with ❤️ for developers who want to focus on coding, not documentation hunting.**
