# TalkDocs2 - Web Crawling with Portia AI Tools

A powerful web crawling and content extraction system that wraps your existing web crawler logic into custom Portia AI tools for direct invocation. This project provides structured, efficient web scraping capabilities with comprehensive error handling and metadata extraction.

## 🚀 Features

- **Direct Tool Invocation**: Use tools without LLM planning for predictable, efficient execution
- **JavaScript Support**: Handle modern websites with Selenium integration
- **Sitemap Generation**: Automatically discover and map website structures
- **Bulk Processing**: Extract content from multiple URLs efficiently
- **Structured Output**: JSON-formatted results with comprehensive metadata
- **Error Handling**: Robust error management with detailed feedback
- **Rate Limiting**: Configurable delays to respect target websites
- **Domain Restriction**: Crawl only within specified domains
- **Smart Data Management**: Automatically detect and reuse existing crawled data
- **Data Age Tracking**: Show when data was last crawled to help decide on re-crawling

## 🛠️ Custom Portia AI Tools

### 1. WebCrawlerTool (`web_crawler_tool`)
Comprehensive website crawler that discovers and extracts content from multiple pages.

**Features:**
- Automatic sitemap generation
- JavaScript-heavy site support
- Configurable page limits and delays
- Domain-restricted crawling

**Use Cases:**
- Website content audits
- Competitive analysis
- Documentation scraping
- Content migration

### 2. WebExtractorTool (`web_extractor_tool`)
Single-page content extractor for targeted data extraction.

**Features:**
- Clean text extraction
- Optional link extraction
- Selenium support for dynamic content
- Title and metadata extraction

**Use Cases:**
- Article content extraction
- Product information scraping
- News article processing
- Research data collection

### 3. WebSitemapTool (`web_sitemap_tool`)
Generates comprehensive website sitemaps by discovering all accessible URLs.

**Features:**
- Hierarchical URL discovery
- Title and metadata collection
- Export to JSON format
- Configurable depth limits

**Use Cases:**
- SEO analysis
- Website structure mapping
- Link inventory
- Content planning

### 4. BulkWebExtractorTool (`bulk_web_extractor_tool`)
Efficiently processes multiple URLs with controlled concurrency.

**Features:**
- Batch processing
- Success/failure tracking
- Rate limiting
- Progress monitoring

**Use Cases:**
- Large-scale content extraction
- URL validation
- Bulk data collection
- Content quality assessment

## 🚀 Proper Portia AI Integration

TalkDocs2 now includes **proper Portia AI integration** using the official Portia AI framework:

### Integration Features

- **PlanBuilderV2**: Uses Portia AI's `PlanBuilderV2` for structured plan creation
- **Direct Tool Invocation**: Proper `invoke_tool_step()` integration without mock contexts
- **Tools List**: Custom tools passed directly to Portia constructor
- **Automatic Fallback**: Falls back to standard crawler if Portia AI is unavailable
- **Error Handling**: Comprehensive error handling with clear user feedback

### How It Works

1. **Tool Creation**: Custom web crawler tools are instantiated as objects
2. **Tools List**: Tools are passed as a list to the Portia constructor
3. **Plan Building**: Uses `PlanBuilderV2` to create structured execution plans
4. **Direct Invocation**: Tools are invoked directly using `invoke_tool_step()`
5. **Result Processing**: Plan run outputs are processed and saved to JSON files

### Code Example

```python
from portia import Portia, PlanBuilderV2, Config, Input
from portia_web_tools import WebCrawlerTool

# Create custom tools
web_crawler_tool = WebCrawlerTool()
custom_tools = [web_crawler_tool]

# Create Portia instance
config = Config.from_default()
portia = Portia(config=config, tools=custom_tools)

# Build plan for direct tool invocation
plan = (
    PlanBuilderV2("Crawl website and extract structured data")
    .input(name="base_url", description="The website URL to crawl")
    .invoke_tool_step(
        step_name="Crawl Website",
        tool="web_crawler_tool",
        args={
            "base_url": Input("base_url"),
            "max_pages": 10,
            "create_sitemap": True,
            "output_format": "json"
        }
    )
    .build()
)

# Execute the plan
plan_run = portia.run_plan(plan, plan_run_inputs={"base_url": "https://example.com"})
```

### Web Interface Features

- **Workflow Selection**: Toggle between Standard Web Crawler and Portia AI Tools
- **Tool Testing**: Test individual Portia AI tools with the "🚀 Test Portia Tools" button
- **Status Indicators**: Clear visual feedback about Portia AI availability
- **Automatic Fallback**: Seamless fallback to standard crawler when needed

## 📦 Installation

1. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables** (create `.env` file):
```env
OPENAI_API_KEY=your_openai_key_here
PORTIA_API_KEY=your_portia_key_here  # Optional, for cloud features
```

## 🔧 Usage Examples

### Simple Direct Function Calls

```python
from portia_web_tools import (
    extract_content_direct,
    crawl_website_direct,
    generate_sitemap_direct,
    bulk_extract_direct
)

# Extract content from a single page
result = extract_content_direct(
    url="https://example.com",
    extract_links=True
)
print(f"Title: {result['title']}")
print(f"Content length: {result['content_length']} characters")

# Crawl a website
crawl_result = crawl_website_direct(
    base_url="https://example.com",
    max_pages=5,
    delay=1.0
)
print(f"Crawled {crawl_result['total_pages']} pages")

# Generate sitemap
sitemap = generate_sitemap_direct(
    base_url="https://example.com",
    max_urls=20
)
print(f"Found {sitemap['total_urls']} URLs")

# Bulk extraction
bulk_result = bulk_extract_direct(
    urls=["https://example.com", "https://httpbin.org/html"],
    delay=1.0
)
print(f"Success rate: {bulk_result['success_rate']}")
```

### Portia AI Direct Invocation

```python
from portia import PlanBuilderV2, Portia, Config, Input, StepOutput
from portia_web_tools import create_web_tools_registry

# Initialize Portia with web tools
config = Config.from_default()
web_tools = create_web_tools_registry()
portia = Portia(config=config, tools=web_tools)

# Create a plan for direct tool invocation
plan = (
    PlanBuilderV2("Extract and analyze website content")
    .input(name="target_url", description="URL to analyze")
    
    # Step 1: Extract content
    .invoke_tool_step(
        step_name="extract_content",
        tool="web_extractor_tool",
        args={
            "url": Input("target_url"),
            "extract_links": True
        }
    )
    
    # Step 2: Generate sitemap
    .invoke_tool_step(
        step_name="generate_sitemap",
        tool="web_sitemap_tool",
        args={
            "base_url": Input("target_url"),
            "max_urls": 10
        }
    )
    
    # Step 3: Process results
    .function_step(
        step_name="analyze_results",
        function=lambda content, sitemap: {
            "content_length": json.loads(content)["content_length"],
            "urls_found": json.loads(sitemap)["total_urls"],
            "analysis_complete": True
        },
        args={
            "content": StepOutput("extract_content"),
            "sitemap": StepOutput("generate_sitemap")
        }
    )
    
    .build()
)

# Execute the plan
result = portia.run_plan(
    plan,
    plan_run_inputs={"target_url": "https://docs.portialabs.ai/"}
)

# Access results
analysis = result.outputs.step_outputs["analyze_results"].value
print(f"Analysis complete: {analysis}")
```

### Complex Workflow with Conditionals

```python
# Conditional workflow based on page characteristics
plan = (
    PlanBuilderV2("Smart content extraction")
    .input(name="url", description="URL to process")
    
    # Initial check
    .invoke_tool_step(
        step_name="check_page",
        tool="web_extractor_tool",
        args={"url": Input("url")}
    )
    
    # Conditional processing
    .if_(
        condition=lambda result: json.loads(result)["content_length"] > 5000,
        args={"result": StepOutput("check_page")}
    )
    .invoke_tool_step(
        step_name="large_page_crawl",
        tool="web_crawler_tool",
        args={
            "base_url": Input("url"),
            "max_pages": 3,
            "use_selenium": True
        }
    )
    .else_()
    .invoke_tool_step(
        step_name="simple_extraction",
        tool="web_extractor_tool",
        args={
            "url": Input("url"),
            "extract_links": True
        }
    )
    .endif()
    
    .build()
)
```

## 📊 Tool Schemas

### WebCrawlerTool Parameters
```python
{
    "base_url": str,           # Required: Starting URL
    "max_pages": int,          # Default: 10, Range: 1-100
    "delay": float,            # Default: 1.0, Range: 0.1-5.0
    "create_sitemap": bool,    # Default: True
    "output_format": str       # Default: "json", Options: "json"|"text"
}
```

### WebExtractorTool Parameters
```python
{
    "url": str,                # Required: Target URL
    "extract_links": bool,     # Default: False
    "use_selenium": bool       # Default: False
}
```

### WebSitemapTool Parameters
```python
{
    "base_url": str,           # Required: Website base URL
    "max_urls": int,           # Default: 50, Range: 1-500
    "output_file": str         # Optional: Save to file
}
```

### BulkWebExtractorTool Parameters
```python
{
    "urls": List[str],         # Required: List of URLs
    "delay": float,            # Default: 1.0, Range: 0.1-3.0
    "max_concurrent": int      # Default: 3, Range: 1-10
}
```

## 🔍 Example Output Structures

### Content Extraction Result
```json
{
    "url": "https://example.com",
    "title": "Example Domain",
    "content": "This domain is for use in illustrative examples...",
    "links": ["https://www.iana.org/domains/example"],
    "extraction_timestamp": "2024-01-15 10:30:45",
    "selenium_used": false,
    "content_length": 1256,
    "links_found": 1
}
```

### Crawl Result
```json
{
    "base_url": "https://example.com",
    "total_pages": 3,
    "crawl_timestamp": "2024-01-15 10:30:45",
    "pages": [
        {
            "url": "https://example.com",
            "title": "Example Domain",
            "content": "Page content...",
            "timestamp": "2024-01-15 10:30:45"
        }
    ],
    "sitemap": {
        "https://example.com": {
            "title": "Example Domain",
            "url": "https://example.com",
            "discovered_at": "2024-01-15 10:30:45"
        }
    },
    "stats": {
        "visited_urls": 3,
        "max_pages_requested": 10,
        "delay_used": 1.0,
        "sitemap_created": true
    }
}
```

## 🎯 Advanced Features

### Smart Data Management
The application automatically detects when you've already crawled a website and offers options:
- **Automatic Detection**: Checks for existing data when entering a URL
- **Data Age Tracking**: Shows how old the existing data is (minutes, hours, days)
- **Smart Options**: Choose to use existing data, re-crawl, or cancel
- **Data Preview**: View sample of existing data before deciding
- **Bulk Management**: Load any previously crawled data from the sidebar

### Error Handling
Tools use Portia's error handling system:
- `ToolSoftError`: Retryable errors (network timeouts, temporary failures)
- `ToolHardError`: Non-retryable errors (invalid URLs, permission denied)

### Performance Optimization
- **Caching**: Reuse connections with session management
- **Rate Limiting**: Configurable delays between requests
- **Concurrency Control**: Limit simultaneous requests
- **Selenium Management**: Automatic driver lifecycle management
- **Data Reuse**: Avoid re-crawling when data already exists

### Output Formats
All tools return structured JSON with:
- **Metadata**: Timestamps, processing stats, configurations
- **Content**: Extracted text, titles, links
- **Status**: Success/failure indicators
- **Diagnostics**: Content length, processing time, errors

## 🚨 Best Practices

1. **Rate Limiting**: Always use appropriate delays to respect target websites
2. **Error Handling**: Implement proper try-catch blocks for robust workflows
3. **Resource Management**: Tools automatically clean up Selenium drivers
4. **URL Validation**: Tools validate URLs before processing
5. **Content Filtering**: Automatic filtering of non-content URLs (images, files)
6. **Data Management**: Use existing data when possible to save time and resources
7. **Regular Updates**: Re-crawl websites periodically to keep data fresh

## 📈 Monitoring and Debugging

Tools provide comprehensive logging:
```python
import logging
logging.basicConfig(level=logging.INFO)

# Run tools with detailed logging
result = extract_content_direct("https://example.com")
```

## 🤝 Integration with Existing Code

These tools wrap your existing `WebCrawler` class, so you can:
- Use existing configuration and logic
- Maintain compatibility with current code
- Add Portia AI capabilities incrementally
- Benefit from structured outputs and error handling

## 🔗 Quick Start

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up environment variables** in `.env` file:
```env
OPENAI_API_KEY=your_openai_key_here
```

3. **Run the Streamlit app:**
```bash
streamlit run app.py
```

4. **Use the web interface:**
   - Enter a URL to crawl
   - If data already exists, choose to use existing or re-crawl
   - Load documents and chat with the AI chatbot

5. **Test the tools programmatically:**
```python
from portia_web_tools import extract_content_direct

# Simple test
result = extract_content_direct("https://example.com")
print(f"Extracted: {result['title']}")
```

6. **Build complex workflows** using Portia AI's PlanBuilderV2 for direct tool invocation

## 📁 Project Structure

```
TalkDocs2/
├── app.py                      # Main Streamlit application
├── chatbot.py                  # Chatbot implementation
├── web_crawler.py             # Core web crawling logic
├── portia_web_tools.py        # Custom Portia AI tools
├── requirements.txt           # Python dependencies
├── README.md                  # This comprehensive guide
└── crawled_data_*.json        # Crawled data files
```

## 🎉 What You Get

- **4 Custom Portia AI Tools** for web crawling and extraction
- **Direct Tool Invocation** without LLM planning overhead
- **Structured JSON Outputs** with comprehensive metadata
- **Error Handling** with retryable and non-retryable error types
- **Performance Optimizations** with rate limiting and caching
- **JavaScript Support** for modern websites
- **Bulk Processing** capabilities for large-scale extraction
- **Sitemap Generation** for website structure discovery

Your web crawling logic is now ready for powerful, direct invocation with Portia AI! 🚀
