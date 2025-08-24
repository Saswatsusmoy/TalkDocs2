# TalkDocs CLI - Command Line Interface

A powerful command-line tool for web crawling and AI document analysis, built on top of the TalkDocs platform.

## 🚀 Features

- **Web Crawling**: Crawl websites with configurable settings
- **AI Document Analysis**: Chat with your crawled documents using Google AI
- **Portia AI Integration**: Enhanced crawling with Portia AI tools
- **Interactive Chat**: Real-time conversation with your documents
- **Data Management**: List, load, and manage crawled data
- **Colored Output**: Beautiful terminal interface with colors and emojis

## 📋 Requirements

- Python 3.7+
- Google AI API key
- Required Python packages (see installation)

## 🔧 Installation

1. **Clone or download the TalkDocs project**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your Google AI API key**:
   ```bash
   # Option 1: Environment variable
   export GOOGLE_API_KEY="your-api-key-here"
   
   # Option 2: .env file
   echo "GOOGLE_API_KEY=your-api-key-here" > .env
   ```

4. **Make the CLI executable** (optional):
   ```bash
   chmod +x talkdocs_cli.py
   ```

## 🎯 Quick Start

### 1. Crawl a Website
```bash
# Basic crawl
python talkdocs_cli.py crawl https://example.com

# Advanced crawl with options
python talkdocs_cli.py crawl https://example.com --max-pages 100 --delay 2.0 --use-portia
```

### 2. Start Interactive Chat
```bash
# Load existing data and chat
python talkdocs_cli.py chat --load-file crawled_data_123.json

# Or load by URL
python talkdocs_cli.py chat --load-url https://example.com
```

### 3. Ask a Single Question
```bash
python talkdocs_cli.py ask "What is the main topic?" --load-file crawled_data_123.json
```

## 📖 Command Reference

### `crawl` - Crawl a Website
Crawl a website and save the data for analysis.

```bash
python talkdocs_cli.py crawl <URL> [OPTIONS]
```

**Options:**
- `--max-pages <number>`: Maximum pages to crawl (default: 50)
- `--delay <seconds>`: Delay between requests (default: 1.0)
- `--no-sitemap`: Skip sitemap creation
- `--use-portia`: Use Portia AI tools for enhanced crawling
- `--api-key <key>`: Google AI API key (if not set in environment)

**Examples:**
```bash
# Basic crawl
python talkdocs_cli.py crawl https://example.com

# Large crawl with custom settings
python talkdocs_cli.py crawl https://example.com --max-pages 200 --delay 0.5

# Use Portia AI tools
python talkdocs_cli.py crawl https://example.com --use-portia --max-pages 100
```

### `chat` - Interactive Chat Session
Start an interactive chat session with your documents.

```bash
python talkdocs_cli.py chat [OPTIONS]
```

**Options:**
- `--load-file <filename>`: Load specific crawled data file
- `--load-url <url>`: Load data for specific URL
- `--api-key <key>`: Google AI API key (if not set in environment)

**Examples:**
```bash
# Load by filename
python talkdocs_cli.py chat --load-file crawled_data_123.json

# Load by URL
python talkdocs_cli.py chat --load-url https://example.com
```

**Interactive Commands:**
- `quit`, `exit`, `q`: End the chat session
- `clear`: Clear chat history

### `ask` - Single Question
Ask a single question and get an immediate response.

```bash
python talkdocs_cli.py ask <QUESTION> [OPTIONS]
```

**Options:**
- `--load-file <filename>`: Load specific crawled data file
- `--load-url <url>`: Load data for specific URL
- `--api-key <key>`: Google AI API key (if not set in environment)

**Examples:**
```bash
# Ask about main topic
python talkdocs_cli.py ask "What is the main topic?" --load-file data.json

# Ask about specific content
python talkdocs_cli.py ask "What are the key features mentioned?" --load-url https://example.com
```

### `list` - List Crawled Data
List all available crawled data files.

```bash
python talkdocs_cli.py list
```

**Output:**
```
============================================================
  Crawled Data Files
============================================================
1. crawled_data_123.json
   URL: https://example.com
   Pages: 45
   Crawled: 2024-01-15 14:30:22

2. crawled_data_456.json
   URL: https://another-site.com
   Pages: 23
   Crawled: 2024-01-15 16:45:10
```

### `summary` - Document Summary
Show a summary of loaded documents.

```bash
python talkdocs_cli.py summary [OPTIONS]
```

**Options:**
- `--load-file <filename>`: Load specific crawled data file
- `--load-url <url>`: Load data for specific URL
- `--api-key <key>`: Google AI API key (if not set in environment)

### `clear` - Clear All Data
Delete all crawled data files.

```bash
python talkdocs_cli.py clear
```

⚠️ **Warning**: This will permanently delete all crawled data files.

## 🔄 Workflow Examples

### Complete Workflow
```bash
# 1. Crawl a website
python talkdocs_cli.py crawl https://example.com --max-pages 100

# 2. Start interactive chat
python talkdocs_cli.py chat --load-url https://example.com

# 3. Ask specific questions
python talkdocs_cli.py ask "What are the main features?" --load-url https://example.com
```

### Batch Processing
```bash
# Crawl multiple sites
python talkdocs_cli.py crawl https://site1.com --max-pages 50
python talkdocs_cli.py crawl https://site2.com --max-pages 50

# List all data
python talkdocs_cli.py list

# Chat with specific site
python talkdocs_cli.py chat --load-url https://site1.com
```

### Research Workflow
```bash
# 1. Crawl research papers
python talkdocs_cli.py crawl https://research-site.com --max-pages 200

# 2. Get summary
python talkdocs_cli.py summary --load-url https://research-site.com

# 3. Ask research questions
python talkdocs_cli.py ask "What are the key findings?" --load-url https://research-site.com
```

## 🎨 Output Formatting

The CLI uses colored output for better readability:

- **✅ Green**: Success messages
- **❌ Red**: Error messages
- **⚠️ Yellow**: Warning messages
- **ℹ️ Blue**: Information messages
- **🔵 Cyan**: Headers and important information

## 🔧 Configuration

### Environment Variables
- `GOOGLE_API_KEY`: Your Google AI API key

### API Key Options
1. **Environment variable**: `export GOOGLE_API_KEY="your-key"`
2. **Command line**: `--api-key "your-key"`
3. **`.env` file**: Create a `.env` file with `GOOGLE_API_KEY=your-key`

### Crawling Settings
- **Default max pages**: 50
- **Default delay**: 1.0 seconds
- **Default sitemap**: Enabled
- **Default crawler**: Standard (Portia AI optional)

## 🐛 Troubleshooting

### Common Issues

**1. API Key Not Found**
```
❌ Google AI API key not found!
ℹ️ Please set GOOGLE_API_KEY environment variable or use --api-key option
```
**Solution**: Set your API key using one of the methods above.

**2. Portia AI SDK Not Available**
```
❌ Portia AI SDK not available. Install with: pip install portia-sdk-python
ℹ️ Falling back to standard crawler...
```
**Solution**: Install Portia SDK or use standard crawler.

**3. Invalid URL**
```
❌ Invalid URL format
```
**Solution**: Ensure URL includes protocol (http:// or https://).

**4. No Documents Loaded**
```
❌ No documents loaded. Please load documents first.
```
**Solution**: Crawl a website first or load existing data.

### Error Codes
- **Exit code 1**: Error occurred during operation
- **Exit code 0**: Successful operation

## 📁 File Structure

```
talkdocs_cli.py          # Main CLI script
crawled_data_*.json      # Crawled data files
.env                     # Environment variables (optional)
requirements.txt         # Python dependencies
```

## 🔗 Integration

The CLI tool integrates with:
- **Web Crawler**: Uses the same crawling engine as the web interface
- **Chatbot**: Uses the same AI analysis capabilities
- **Portia AI**: Optional enhanced crawling with AI tools
- **Data Files**: Compatible with web interface data format

## 🤝 Contributing

To contribute to the CLI tool:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This CLI tool is part of the TalkDocs project and follows the same license terms.

## 🆘 Support

For support and questions:
1. Check the troubleshooting section
2. Review the examples
3. Check the main TalkDocs documentation
4. Open an issue on the project repository

---

**Happy crawling and chatting! 🚀**
