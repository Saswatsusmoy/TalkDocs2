#!/usr/bin/env python3
"""
TalkDocs CLI - Command Line Interface for TalkDocs
A powerful CLI tool for web crawling and AI document analysis
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional
import validators
from dotenv import load_dotenv

# Import the existing modules
from web_crawler import WebCrawler
from chatbot import DocumentChatbot
from portia_web_tools import WebCrawlerTool, WebExtractorTool, WebSitemapTool

# Load environment variables
load_dotenv()

class TalkDocsCLI:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.chatbot = None
        self.crawled_data = None
        self.current_url = None
        
        # Colors for CLI output
        self.colors = {
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'purple': '\033[95m',
            'cyan': '\033[96m',
            'white': '\033[97m',
            'bold': '\033[1m',
            'underline': '\033[4m',
            'end': '\033[0m'
        }
    
    def print_colored(self, text: str, color: str = 'white', bold: bool = False):
        """Print colored text to terminal"""
        color_code = self.colors.get(color, '')
        bold_code = self.colors['bold'] if bold else ''
        print(f"{color_code}{bold_code}{text}{self.colors['end']}")
    
    def print_header(self, text: str):
        """Print a formatted header"""
        print("\n" + "="*60)
        self.print_colored(f"  {text}", 'cyan', bold=True)
        print("="*60)
    
    def print_success(self, text: str):
        """Print success message"""
        self.print_colored(f"✅ {text}", 'green')
    
    def print_error(self, text: str):
        """Print error message"""
        self.print_colored(f"❌ {text}", 'red')
    
    def print_warning(self, text: str):
        """Print warning message"""
        self.print_colored(f"⚠️ {text}", 'yellow')
    
    def print_info(self, text: str):
        """Print info message"""
        self.print_colored(f"ℹ️ {text}", 'blue')
    
    def initialize_chatbot(self) -> bool:
        """Initialize the chatbot with API key"""
        if not self.api_key:
            self.print_error("Google AI API key not found!")
            self.print_info("Please set GOOGLE_API_KEY environment variable or use --api-key option")
            return False
        
        try:
            self.chatbot = DocumentChatbot(api_key=self.api_key)
            self.print_success("Chatbot initialized successfully!")
            return True
        except Exception as e:
            self.print_error(f"Failed to initialize chatbot: {str(e)}")
            return False
    
    def crawl_website(self, url: str, max_pages: int = 50, delay: float = 1.0, 
                     create_sitemap: bool = True, use_portia: bool = False) -> bool:
        """Crawl a website and save the data"""
        if not validators.url(url):
            self.print_error("Invalid URL format")
            return False
        
        self.print_header("Web Crawler")
        self.print_info(f"Starting crawl of: {url}")
        self.print_info(f"Max pages: {max_pages}, Delay: {delay}s, Sitemap: {create_sitemap}")
        
        try:
            if use_portia:
                return self._crawl_with_portia(url, max_pages, delay, create_sitemap)
            else:
                return self._crawl_standard(url, max_pages, delay, create_sitemap)
        except KeyboardInterrupt:
            self.print_warning("Crawling interrupted by user")
            return False
        except Exception as e:
            self.print_error(f"Crawling failed: {str(e)}")
            return False
    
    def _crawl_standard(self, url: str, max_pages: int, delay: float, create_sitemap: bool) -> bool:
        """Standard web crawling"""
        self.print_info("Using standard web crawler...")
        
        crawler = WebCrawler(
            base_url=url,
            max_pages=max_pages,
            delay=delay,
            create_sitemap=create_sitemap
        )
        
        # Start crawling with progress
        self.print_info("Crawling in progress...")
        pages_data = crawler.crawl()
        
        if not pages_data:
            self.print_error("No pages were crawled successfully")
            return False
        
        # Save data
        normalized_url = url.rstrip('/')
        url_hash = str(hash(normalized_url))
        filename = f"crawled_data_{url_hash}.json"
        
        saved_filename = crawler.save_to_json(filename)
        self.print_success(f"Crawling completed! Saved to: {saved_filename}")
        self.print_info(f"Pages crawled: {len(pages_data)}")
        
        # Store data for chat - create the expected structure
        self.crawled_data = {
            'base_url': url,
            'total_pages': len(pages_data),
            'crawl_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'pages': pages_data,
            'sitemap': crawler.sitemap if create_sitemap else None
        }
        self.current_url = url
        
        return True
    
    def _crawl_standard_silent(self, url: str, max_pages: int, delay: float, create_sitemap: bool) -> bool:
        """Standard web crawling without any output messages"""
        crawler = WebCrawler(
            base_url=url,
            max_pages=max_pages,
            delay=delay,
            create_sitemap=create_sitemap
        )
        
        # Start crawling silently
        pages_data = crawler.crawl()
        
        if not pages_data:
            return False
        
        # Save data
        normalized_url = url.rstrip('/')
        url_hash = str(hash(normalized_url))
        filename = f"crawled_data_{url_hash}.json"
        
        saved_filename = crawler.save_to_json(filename)
        
        # Store data for chat - create the expected structure
        self.crawled_data = {
            'base_url': url,
            'total_pages': len(pages_data),
            'crawl_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'pages': pages_data,
            'sitemap': crawler.sitemap if create_sitemap else None
        }
        self.current_url = url
        
        return True
    
    def _crawl_with_portia(self, url: str, max_pages: int, delay: float, create_sitemap: bool) -> bool:
        """Crawl using Portia AI tools"""
        self.print_info("Using Portia AI tools...")
        
        try:
            from portia import Portia, PlanBuilderV2, Config, Input
        except ImportError:
            # Silent fallback to standard crawler
            return self._crawl_standard_silent(url, max_pages, delay, create_sitemap)
        
        # Create custom web tools
        web_crawler_tool = WebCrawlerTool()
        web_extractor_tool = WebExtractorTool()
        web_sitemap_tool = WebSitemapTool()
        
        custom_tools = [web_crawler_tool, web_extractor_tool, web_sitemap_tool]
        
        # Create Portia instance
        config = Config.from_default()
        portia = Portia(config=config, tools=custom_tools)
        
        # Build plan
        plan = (
            PlanBuilderV2("Crawl website and extract structured data")
            .input(name="base_url", description="The website URL to crawl", default_value=url)
            .input(name="max_pages", description="Maximum pages to crawl", default_value=max_pages)
            .input(name="delay", description="Delay between requests", default_value=delay)
            .input(name="create_sitemap", description="Whether to create sitemap", default_value=create_sitemap)
            .invoke_tool_step(
                step_name="Crawl Website",
                tool="web_crawler_tool",
                args={
                    "base_url": Input("base_url"),
                    "max_pages": Input("max_pages"),
                    "delay": Input("delay"),
                    "create_sitemap": Input("create_sitemap"),
                    "output_format": "json"
                }
            )
            .build()
        )
        
        # Execute plan
        self.print_info("Executing Portia AI crawling plan...")
        try:
            plan_run = portia.run_plan(plan, plan_run_inputs={
                "base_url": url,
                "max_pages": max_pages,
                "delay": delay,
                "create_sitemap": create_sitemap
            })
            
            if plan_run and plan_run.outputs and plan_run.outputs.step_outputs:
                crawl_result = plan_run.outputs.step_outputs.get("Crawl Website")
                if crawl_result and crawl_result.value:
                    if isinstance(crawl_result.value, str):
                        result_data = json.loads(crawl_result.value)
                    else:
                        result_data = crawl_result.value
                    
                    # Save data
                    normalized_url = url.rstrip('/')
                    url_hash = str(hash(normalized_url))
                    filename = f"crawled_data_{url_hash}.json"
                    
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(result_data, f, indent=2, ensure_ascii=False)
                    
                    self.print_success(f"Portia AI crawling completed! Saved to: {filename}")
                    self.print_info(f"Pages crawled: {len(result_data.get('pages', []))}")
                    
                    # Store data for chat
                    self.crawled_data = result_data
                    self.current_url = url
                    
                    return True
            
            # If Portia fails, silently fallback to standard crawler
            return self._crawl_standard_silent(url, max_pages, delay, create_sitemap)
            
        except Exception as e:
            # Silent fallback to standard crawler on any Portia error
            return self._crawl_standard_silent(url, max_pages, delay, create_sitemap)
    
    def load_existing_data(self, filename: str) -> bool:
        """Load existing crawled data from file"""
        if not os.path.exists(filename):
            self.print_error(f"File not found: {filename}")
            return False
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different data structures
            if isinstance(data, list):
                # If data is a list, convert to expected format
                self.crawled_data = {
                    'base_url': 'Unknown URL',
                    'total_pages': len(data),
                    'crawl_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'pages': data,
                    'sitemap': None
                }
            else:
                # Expected dictionary format
                self.crawled_data = data
            
            self.current_url = self.crawled_data.get('base_url', 'Unknown URL')
            
            self.print_success(f"Loaded existing data from: {filename}")
            self.print_info(f"Pages: {len(self.crawled_data.get('pages', []))}")
            self.print_info(f"URL: {self.current_url}")
            
            return True
        except Exception as e:
            self.print_error(f"Failed to load data: {str(e)}")
            return False
    
    def list_existing_data(self) -> List[Dict]:
        """List all existing crawled data files"""
        crawled_files = []
        
        for filename in os.listdir('.'):
            if filename.startswith('crawled_data_') and filename.endswith('.json'):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        # Handle different data structures
                        if isinstance(data, list):
                            page_count = len(data)
                            base_url = 'Unknown URL'
                            crawl_timestamp = 'Unknown time'
                        else:
                            page_count = len(data.get('pages', []))
                            base_url = data.get('base_url', 'Unknown URL')
                            crawl_timestamp = data.get('crawl_timestamp', 'Unknown time')
                        
                        crawled_files.append({
                            'filename': filename,
                            'base_url': base_url,
                            'crawl_timestamp': crawl_timestamp,
                            'page_count': page_count,
                            'data': data
                        })
                except Exception:
                    continue
        
        return crawled_files
    
    def load_documents_to_chatbot(self) -> bool:
        """Load documents into the chatbot"""
        if not self.chatbot:
            if not self.initialize_chatbot():
                return False
        
        if not self.crawled_data:
            self.print_error("No crawled data available. Please crawl a website first.")
            return False
        
        try:
            success = self.chatbot.load_documents_from_data(self.crawled_data)
            if success:
                self.print_success(f"Loaded {len(self.chatbot.documents)} documents into chatbot")
                return True
            else:
                self.print_error("Failed to load documents into chatbot")
                return False
        except Exception as e:
            self.print_error(f"Error loading documents: {str(e)}")
            return False
    
    def interactive_chat(self):
        """Start interactive chat session"""
        if not self.chatbot:
            if not self.initialize_chatbot():
                return
        
        if not self.chatbot.documents:
            self.print_error("No documents loaded. Please load documents first.")
            return
        
        self.print_header("Interactive Chat Session")
        self.print_info(f"🤖 AI Coding Documentation Assistant ready with {len(self.chatbot.documents)} documents")
        self.print_info("💡 Ask me about APIs, functions, configuration, integration, or any code documentation!")
        self.print_info("Type 'quit', 'exit', or 'q' to end the session")
        self.print_info("Type 'clear' to clear chat history")
        print()
        
        chat_history = []
        
        while True:
            try:
                # Get user input
                user_input = input(f"{self.colors['green']}You: {self.colors['end']}")
                
                # Check for exit commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    self.print_info("Ending chat session...")
                    break
                
                # Check for clear command
                if user_input.lower() == 'clear':
                    chat_history = []
                    self.print_info("Chat history cleared")
                    print()
                    continue
                
                # Skip empty input
                if not user_input.strip():
                    continue
                
                # Add to history
                chat_history.append({"role": "user", "content": user_input})
                
                # Get bot response
                self.print_info("AI is thinking...")
                response = self.chatbot.chat(user_input, use_rag=True)
                
                # Add response to history
                chat_history.append({"role": "assistant", "content": response})
                
                # Display response
                print(f"{self.colors['blue']}AI: {self.colors['end']}{response}")
                print()
                
            except KeyboardInterrupt:
                self.print_warning("Chat session interrupted")
                break
            except Exception as e:
                self.print_error(f"Error in chat: {str(e)}")
    
    def single_chat(self, question: str) -> str:
        """Send a single question and get response"""
        if not self.chatbot:
            if not self.initialize_chatbot():
                return "Error: Chatbot not initialized"
        
        if not self.chatbot.documents:
            return "Error: No documents loaded. Please load documents first."
        
        try:
            response = self.chatbot.chat(question, use_rag=True)
            return response
        except Exception as e:
            return f"Error: {str(e)}"
    
    def show_document_summary(self):
        """Show summary of loaded documents"""
        if not self.chatbot or not self.chatbot.documents:
            self.print_error("No documents loaded")
            return
        
        self.print_header("Document Summary")
        summary = self.chatbot.get_document_summary()
        print(summary)
    
    def clear_all_data(self):
        """Clear all crawled data files"""
        crawled_files = self.list_existing_data()
        
        if not crawled_files:
            self.print_info("No crawled data files found")
            return
        
        self.print_warning(f"This will delete {len(crawled_files)} crawled data files")
        confirm = input("Are you sure? (y/N): ")
        
        if confirm.lower() == 'y':
            deleted_count = 0
            for file_info in crawled_files:
                try:
                    os.remove(file_info['filename'])
                    deleted_count += 1
                    self.print_success(f"Deleted: {file_info['filename']}")
                except Exception as e:
                    self.print_error(f"Failed to delete {file_info['filename']}: {str(e)}")
            
            self.print_success(f"Deleted {deleted_count} files")
        else:
            self.print_info("Operation cancelled")

def main():
    parser = argparse.ArgumentParser(
        description="TalkDocs CLI - AI-powered code documentation assistant for developers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Crawl a website
  python talkdocs_cli.py crawl https://example.com --max-pages 100
  
  # Load existing data and start interactive chat
  python talkdocs_cli.py chat --load-file crawled_data_123.json
  
  # Ask a single question
  python talkdocs_cli.py ask "What is the main topic?" --load-file crawled_data_123.json
  
  # List all crawled data
  python talkdocs_cli.py list
  
  # Clear all data
  python talkdocs_cli.py clear
        """
    )
    
    parser.add_argument('--api-key', help='Google AI API key (or set GOOGLE_API_KEY env var)')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Crawl command
    crawl_parser = subparsers.add_parser('crawl', help='Crawl a website')
    crawl_parser.add_argument('url', help='Website URL to crawl')
    crawl_parser.add_argument('--max-pages', type=int, default=50, help='Maximum pages to crawl (default: 50)')
    crawl_parser.add_argument('--delay', type=float, default=1.0, help='Delay between requests in seconds (default: 1.0)')
    crawl_parser.add_argument('--no-sitemap', action='store_true', help='Skip sitemap creation')
    crawl_parser.add_argument('--use-portia', action='store_true', help='Use Portia AI tools for crawling')
    
    # Chat command
    chat_parser = subparsers.add_parser('chat', help='Start interactive chat session')
    chat_parser.add_argument('--load-file', help='Load existing crawled data file')
    chat_parser.add_argument('--load-url', help='Load data for specific URL')
    
    # Ask command
    ask_parser = subparsers.add_parser('ask', help='Ask a single question')
    ask_parser.add_argument('question', help='Question to ask')
    ask_parser.add_argument('--load-file', help='Load existing crawled data file')
    ask_parser.add_argument('--load-url', help='Load data for specific URL')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all crawled data files')
    
    # Summary command
    summary_parser = subparsers.add_parser('summary', help='Show document summary')
    summary_parser.add_argument('--load-file', help='Load existing crawled data file')
    summary_parser.add_argument('--load-url', help='Load data for specific URL')
    
    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear all crawled data files')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize CLI
    cli = TalkDocsCLI()
    
    # Set API key if provided
    if args.api_key:
        cli.api_key = args.api_key
    
    # Execute commands
    if args.command == 'crawl':
        create_sitemap = not args.no_sitemap
        success = cli.crawl_website(
            url=args.url,
            max_pages=args.max_pages,
            delay=args.delay,
            create_sitemap=create_sitemap,
            use_portia=args.use_portia
        )
        
        if success:
            cli.print_success("Crawling completed successfully!")
        else:
            cli.print_error("Crawling failed")
            sys.exit(1)
    
    elif args.command == 'chat':
        # Load data if specified
        if args.load_file:
            if not cli.load_existing_data(args.load_file):
                sys.exit(1)
        elif args.load_url:
            # Find data for URL
            crawled_files = cli.list_existing_data()
            found_file = None
            for file_info in crawled_files:
                if file_info['base_url'] == args.load_url:
                    found_file = file_info['filename']
                    break
            
            if found_file:
                if not cli.load_existing_data(found_file):
                    sys.exit(1)
            else:
                cli.print_error(f"No data found for URL: {args.load_url}")
                sys.exit(1)
        
        # Load documents to chatbot
        if not cli.load_documents_to_chatbot():
            sys.exit(1)
        
        # Start interactive chat
        cli.interactive_chat()
    
    elif args.command == 'ask':
        # Load data if specified
        if args.load_file:
            if not cli.load_existing_data(args.load_file):
                sys.exit(1)
        elif args.load_url:
            # Find data for URL
            crawled_files = cli.list_existing_data()
            found_file = None
            for file_info in crawled_files:
                if file_info['base_url'] == args.load_url:
                    found_file = file_info['filename']
                    break
            
            if found_file:
                if not cli.load_existing_data(found_file):
                    sys.exit(1)
            else:
                cli.print_error(f"No data found for URL: {args.load_url}")
                sys.exit(1)
        
        # Load documents to chatbot
        if not cli.load_documents_to_chatbot():
            sys.exit(1)
        
        # Ask question
        response = cli.single_chat(args.question)
        print(response)
    
    elif args.command == 'list':
        crawled_files = cli.list_existing_data()
        
        if not crawled_files:
            cli.print_info("No crawled data files found")
        else:
            cli.print_header("Crawled Data Files")
            for i, file_info in enumerate(crawled_files, 1):
                print(f"{i}. {file_info['filename']}")
                print(f"   URL: {file_info['base_url']}")
                print(f"   Pages: {file_info['page_count']}")
                print(f"   Crawled: {file_info['crawl_timestamp']}")
                print()
    
    elif args.command == 'summary':
        # Load data if specified
        if args.load_file:
            if not cli.load_existing_data(args.load_file):
                sys.exit(1)
        elif args.load_url:
            # Find data for URL
            crawled_files = cli.list_existing_data()
            found_file = None
            for file_info in crawled_files:
                if file_info['base_url'] == args.load_url:
                    found_file = file_info['filename']
                    break
            
            if found_file:
                if not cli.load_existing_data(found_file):
                    sys.exit(1)
            else:
                cli.print_error(f"No data found for URL: {args.load_url}")
                sys.exit(1)
        
        # Load documents to chatbot
        if not cli.load_documents_to_chatbot():
            sys.exit(1)
        
        # Show summary
        cli.show_document_summary()
    
    elif args.command == 'clear':
        cli.clear_all_data()

if __name__ == "__main__":
    main()
