"""
Custom Portia AI Tools for Web Crawling and Content Extraction
This module wraps the existing web crawler logic into Portia AI tools for direct invocation.
"""

import json
import time
import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from portia import Tool, ToolRunContext
from portia.errors import ToolHardError, ToolSoftError

# Import your existing web crawler
from web_crawler import WebCrawler


# Schema definitions for tool inputs
class WebCrawlerToolSchema(BaseModel):
    """Schema for the Web Crawler Tool"""
    base_url: str = Field(..., description="The base URL to start crawling from")
    max_pages: int = Field(default=10, description="Maximum number of pages to crawl", ge=1, le=100)
    delay: float = Field(default=1.0, description="Delay between requests in seconds", ge=0.1, le=5.0)
    create_sitemap: bool = Field(default=True, description="Whether to create a detailed sitemap first")
    output_format: str = Field(default="json", description="Output format: 'json' or 'text'")


class WebExtractorToolSchema(BaseModel):
    """Schema for the Web Content Extractor Tool"""
    url: str = Field(..., description="Single URL to extract content from")
    extract_links: bool = Field(default=False, description="Whether to extract links from the page")
    use_selenium: bool = Field(default=False, description="Force use of Selenium for JavaScript-heavy sites")


class WebSitemapToolSchema(BaseModel):
    """Schema for the Web Sitemap Generator Tool"""
    base_url: str = Field(..., description="The base URL to generate sitemap for")
    max_urls: int = Field(default=50, description="Maximum number of URLs to include in sitemap", ge=1, le=500)
    output_file: Optional[str] = Field(default=None, description="Optional filename to save sitemap")


class BulkWebExtractorToolSchema(BaseModel):
    """Schema for the Bulk Web Content Extractor Tool"""
    urls: List[str] = Field(..., description="List of URLs to extract content from")
    delay: float = Field(default=1.0, description="Delay between requests in seconds", ge=0.1, le=3.0)
    max_concurrent: int = Field(default=3, description="Maximum concurrent requests", ge=1, le=10)


# Custom Portia AI Tools
class WebCrawlerTool(Tool[str]):
    """
    Comprehensive web crawler tool that crawls websites and extracts content.
    Can handle JavaScript-heavy sites and creates detailed sitemaps.
    """
    
    id: str = "web_crawler_tool"
    name: str = "Web Crawler Tool"
    description: str = (
        "Crawls websites starting from a base URL and extracts content from multiple pages. "
        "Supports JavaScript-heavy sites using Selenium and can create detailed sitemaps. "
        "Returns structured data with page titles, content, and metadata."
    )
    args_schema: type[BaseModel] = WebCrawlerToolSchema
    output_schema: tuple[str, str] = ("str", "JSON string containing crawled website data with pages and metadata")

    def run(self, ctx: ToolRunContext, base_url: str, max_pages: int = 10, 
            delay: float = 1.0, create_sitemap: bool = True, output_format: str = "json") -> str:
        """Run the Web Crawler Tool"""
        
        try:
            # Setup logging (disabled to reduce console output)
            logging.basicConfig(level=logging.WARNING)
            logger = logging.getLogger(self.id)
            
            # Ensure proper types (convert if needed)
            max_pages = int(max_pages) if not isinstance(max_pages, int) else max_pages
            delay = float(delay) if not isinstance(delay, float) else delay
            create_sitemap = bool(create_sitemap) if not isinstance(create_sitemap, bool) else create_sitemap
            
            # Initialize crawler with parameters
            crawler = WebCrawler(
                base_url=base_url,
                max_pages=max_pages,
                delay=delay,
                create_sitemap=create_sitemap
            )
            
            # Perform crawling
            pages_data = crawler.crawl()
            
            if not pages_data:
                raise ToolSoftError(f"No pages were successfully crawled from {base_url}")
            
            # Prepare output data
            result_data = {
                'base_url': base_url,
                'total_pages': len(pages_data),
                'crawl_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'pages': pages_data,
                'sitemap': crawler.sitemap if create_sitemap else None,
                'stats': {
                    'visited_urls': len(crawler.visited_urls),
                    'max_pages_requested': max_pages,
                    'delay_used': delay,
                    'sitemap_created': create_sitemap
                }
            }
            
            if output_format.lower() == "json":
                return json.dumps(result_data, indent=2, ensure_ascii=False)
            else:
                # Text format
                text_output = f"Web Crawl Results for: {base_url}\n"
                text_output += f"Crawled {len(pages_data)} pages\n"
                text_output += f"Timestamp: {result_data['crawl_timestamp']}\n\n"
                
                for page in pages_data:
                    text_output += f"URL: {page['url']}\n"
                    text_output += f"Title: {page['title']}\n"
                    text_output += f"Content Preview: {page['content'][:200]}...\n"
                    text_output += "-" * 50 + "\n"
                
                return text_output
            
        except Exception as e:
            raise ToolHardError(f"Web crawler failed: {str(e)}")


class WebExtractorTool(Tool[str]):
    """
    Single page content extractor tool.
    Extracts clean text content from a single web page.
    """
    
    id: str = "web_extractor_tool"
    name: str = "Web Content Extractor Tool"
    description: str = (
        "Extracts clean text content from a single web page. "
        "Can handle JavaScript-heavy sites and optionally extract links. "
        "Returns structured data with page title, content, and optional links."
    )
    args_schema: type[BaseModel] = WebExtractorToolSchema
    output_schema: tuple[str, str] = ("str", "JSON string containing extracted page content and metadata")

    def run(self, ctx: ToolRunContext, url: str, extract_links: bool = False, 
            use_selenium: bool = False) -> str:
        """Run the Web Content Extractor Tool"""
        
        try:
            # Setup logging (disabled to reduce console output)
            logging.basicConfig(level=logging.WARNING)
            logger = logging.getLogger(self.id)
            
            # Initialize crawler for single page
            crawler = WebCrawler(base_url=url, max_pages=1, create_sitemap=False)
            
            if use_selenium:
                crawler.setup_selenium()
            
            # Get page content
            soup = crawler.get_page_content(url)
            if not soup:
                raise ToolSoftError(f"Failed to fetch content from {url}")
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "No Title"
            
            # Extract content
            content = crawler.extract_text_content(soup)
            
            # Extract links if requested
            links = []
            if extract_links:
                links = crawler.extract_links(soup, url)
            
            result_data = {
                'url': url,
                'title': title_text,
                'content': content,
                'links': links if extract_links else None,
                'extraction_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'selenium_used': use_selenium,
                'content_length': len(content),
                'links_found': len(links) if extract_links else 0
            }
            
            # Cleanup
            if crawler.driver:
                crawler.driver.quit()
            
            return json.dumps(result_data, indent=2, ensure_ascii=False)
            
        except Exception as e:
            raise ToolHardError(f"Content extraction failed: {str(e)}")


class WebSitemapTool(Tool[str]):
    """
    Website sitemap generator tool.
    Creates a comprehensive sitemap of a website.
    """
    
    id: str = "web_sitemap_tool"
    name: str = "Web Sitemap Generator Tool"
    description: str = (
        "Generates a comprehensive sitemap of a website by discovering all accessible URLs. "
        "Returns structured data with URL hierarchy, titles, and discovery metadata."
    )
    args_schema: type[BaseModel] = WebSitemapToolSchema
    output_schema: tuple[str, str] = ("str", "JSON string containing website sitemap with URLs and metadata")

    def run(self, ctx: ToolRunContext, base_url: str, max_urls: int = 50, 
            output_file: Optional[str] = None) -> str:
        """Run the Web Sitemap Generator Tool"""
        
        try:
            # Setup logging (disabled to reduce console output)
            logging.basicConfig(level=logging.WARNING)
            logger = logging.getLogger(self.id)
            
            # Initialize crawler for sitemap creation
            crawler = WebCrawler(base_url=base_url, max_pages=max_urls, create_sitemap=True)
            
            # Create detailed sitemap
            sitemap_urls = crawler.create_detailed_sitemap()
            
            result_data = {
                'base_url': base_url,
                'total_urls': len(sitemap_urls),
                'max_urls_requested': max_urls,
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'urls': list(sitemap_urls),
                'detailed_sitemap': crawler.sitemap
            }
            
            # Save to file if requested
            if output_file:
                crawler.save_sitemap_to_json(output_file)
                result_data['saved_to_file'] = output_file
            
            return json.dumps(result_data, indent=2, ensure_ascii=False)
            
        except Exception as e:
            raise ToolHardError(f"Sitemap generation failed: {str(e)}")


class BulkWebExtractorTool(Tool[str]):
    """
    Bulk web content extractor tool.
    Extracts content from multiple URLs efficiently.
    """
    
    id: str = "bulk_web_extractor_tool"
    name: str = "Bulk Web Content Extractor Tool"
    description: str = (
        "Extracts content from multiple URLs efficiently with controlled concurrency. "
        "Returns structured data with success/failure status for each URL."
    )
    args_schema: type[BaseModel] = BulkWebExtractorToolSchema
    output_schema: tuple[str, str] = ("str", "JSON string containing extracted content from multiple URLs")

    def run(self, ctx: ToolRunContext, urls: List[str], delay: float = 1.0, 
            max_concurrent: int = 3) -> str:
        """Run the Bulk Web Content Extractor Tool"""
        
        try:
            # Setup logging (disabled to reduce console output)
            logging.basicConfig(level=logging.WARNING)
            logger = logging.getLogger(self.id)
            
            results = []
            successful_extractions = 0
            failed_extractions = 0
            
            for i, url in enumerate(urls):
                try:
                    # Initialize crawler for single page
                    crawler = WebCrawler(base_url=url, max_pages=1, create_sitemap=False)
                    
                    # Get page content
                    soup = crawler.get_page_content(url)
                    if not soup:
                        results.append({
                            'url': url,
                            'status': 'failed',
                            'error': 'Failed to fetch content',
                            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                        })
                        failed_extractions += 1
                        continue
                    
                    # Extract content
                    title = soup.find('title')
                    title_text = title.get_text().strip() if title else "No Title"
                    content = crawler.extract_text_content(soup)
                    
                    results.append({
                        'url': url,
                        'status': 'success',
                        'title': title_text,
                        'content': content,
                        'content_length': len(content),
                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                    })
                    successful_extractions += 1
                    
                    # Cleanup
                    if crawler.driver:
                        crawler.driver.quit()
                    
                except Exception as e:
                    results.append({
                        'url': url,
                        'status': 'failed',
                        'error': str(e),
                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                    })
                    failed_extractions += 1
                
                # Respect delay between requests
                if i < len(urls) - 1:  # Don't delay after the last URL
                    time.sleep(delay)
            
            result_data = {
                'total_urls': len(urls),
                'successful_extractions': successful_extractions,
                'failed_extractions': failed_extractions,
                'success_rate': f"{(successful_extractions/len(urls)*100):.1f}%",
                'extraction_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'delay_used': delay,
                'results': results
            }
            
            return json.dumps(result_data, indent=2, ensure_ascii=False)
            
        except Exception as e:
            raise ToolHardError(f"Bulk extraction failed: {str(e)}")


# Tool registry helper
def create_web_tools_registry():
    """Create a registry of all web-related tools"""
    from portia import InMemoryToolRegistry
    
    tools = [
        WebCrawlerTool(),
        WebExtractorTool(),
        WebSitemapTool(),
        BulkWebExtractorTool()
    ]
    
    return InMemoryToolRegistry.from_local_tools(tools)


# Convenience functions for direct tool usage
def crawl_website_direct(base_url: str, max_pages: int = 10, **kwargs) -> Dict[str, Any]:
    """Direct function to crawl a website without Portia orchestration"""
    tool = WebCrawlerTool()
    result_json = tool.run(
        ctx=None,  # Not needed for direct usage
        base_url=base_url,
        max_pages=max_pages,
        **kwargs
    )
    return json.loads(result_json)


def extract_content_direct(url: str, **kwargs) -> Dict[str, Any]:
    """Direct function to extract content from a single URL"""
    tool = WebExtractorTool()
    result_json = tool.run(
        ctx=None,  # Not needed for direct usage
        url=url,
        **kwargs
    )
    return json.loads(result_json)


def generate_sitemap_direct(base_url: str, **kwargs) -> Dict[str, Any]:
    """Direct function to generate a sitemap"""
    tool = WebSitemapTool()
    result_json = tool.run(
        ctx=None,  # Not needed for direct usage
        base_url=base_url,
        **kwargs
    )
    return json.loads(result_json)


def bulk_extract_direct(urls: List[str], **kwargs) -> Dict[str, Any]:
    """Direct function to extract content from multiple URLs"""
    tool = BulkWebExtractorTool()
    result_json = tool.run(
        ctx=None,  # Not needed for direct usage
        urls=urls,
        **kwargs
    )
    return json.loads(result_json)


if __name__ == "__main__":
    # Example usage of the tools
    pass
