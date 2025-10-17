import asyncio
import aiohttp
from urllib.parse import urljoin, urlparse, urlunparse
from bs4 import BeautifulSoup
from typing import Set, List, Dict, Optional
import logging
from asyncio_throttle import Throttler
from tqdm.asyncio import tqdm
import re
import time

logger = logging.getLogger(__name__)

class WebCrawler:
    def __init__(self, vector_store=None):
        self.visited_urls: Set[str] = set()
        self.session: Optional[aiohttp.ClientSession] = None
        self.throttler: Optional[Throttler] = None
        self.vector_store = vector_store
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _is_valid_url(self, url: str, base_domain: str) -> bool:
        """Check if URL is valid and belongs to the same domain"""
        try:
            parsed_url = urlparse(url)
            parsed_base = urlparse(base_domain)
            
            # Must be http or https
            if parsed_url.scheme not in ['http', 'https']:
                return False
            
            # Must be same domain
            if parsed_url.netloc != parsed_base.netloc:
                return False
            
            # Skip common non-content URLs
            skip_patterns = [
                r'\.(pdf|doc|docx|xls|xlsx|ppt|pptx|zip|rar|tar|gz)$',
                r'\.(jpg|jpeg|png|gif|svg|ico|webp)$',
                r'\.(css|js|json|xml)$',
                r'#',  # Fragment identifiers
                r'mailto:',  # Email links
                r'tel:',  # Phone links
            ]
            
            for pattern in skip_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    return False
            
            return True
        except Exception:
            return False
    
    def _extract_content(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract meaningful content from HTML"""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Extract title
        title = ""
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()
        
        # Extract main content
        content = ""
        
        # Try to find main content area
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main|body', re.I))
        
        if main_content:
            content = main_content.get_text(separator=' ', strip=True)
        else:
            # Fallback to body content
            body = soup.find('body')
            if body:
                content = body.get_text(separator=' ', strip=True)
        
        # Clean up content
        content = re.sub(r'\s+', ' ', content)  # Replace multiple whitespace with single space
        content = content.strip()
        
        # Extract meta description
        meta_desc = ""
        meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
        if meta_desc_tag:
            meta_desc = meta_desc_tag.get('content', '').strip()
        
        return {
            'title': title,
            'content': content,
            'meta_description': meta_desc
        }
    
    async def _fetch_page(self, url: str) -> Optional[Dict]:
        """Fetch a single page and extract content"""
        try:
            async with self.throttler:
                async with self.session.get(url) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to fetch {url}: HTTP {response.status}")
                        return None
                    
                    content_type = response.headers.get('content-type', '').lower()
                    if 'text/html' not in content_type:
                        logger.info(f"Skipping non-HTML content: {url}")
                        return None
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')
                    
                    # Extract content
                    page_data = self._extract_content(soup)
                    page_data['url'] = url
                    page_data['timestamp'] = time.time()
                    
                    # Extract links for further crawling
                    links = []
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        absolute_url = urljoin(url, href)
                        if self._is_valid_url(absolute_url, url):
                            links.append(absolute_url)
                    
                    page_data['links'] = links
                    
                    logger.info(f"Successfully processed: {url}")
                    return page_data
                    
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching {url}")
        except Exception as e:
            logger.warning(f"Error fetching {url}: {str(e)}")
        
        return None
    
    async def crawl_domain(self, start_url: str, max_depth: int = 3, max_pages: int = 100, delay: float = 1.0) -> Dict:
        """
        Crawl a domain using DFS (Depth-First Search)
        """
        async with self:
            self.throttler = Throttler(rate_limit=1/delay, period=1.0)
            
            # Initialize
            self.visited_urls.clear()
            pages = []
            url_queue = [(start_url, 0)]  # (url, depth)
            
            logger.info(f"Starting DFS crawl from {start_url}")
            logger.info(f"Max depth: {max_depth}, Max pages: {max_pages}, Delay: {delay}s")
            
            with tqdm(total=max_pages, desc="Crawling pages") as pbar:
                while url_queue and len(pages) < max_pages:
                    current_url, depth = url_queue.pop(0)  # DFS: pop from front
                    
                    # Skip if already visited or depth exceeded
                    if current_url in self.visited_urls or depth > max_depth:
                        continue
                    
                    self.visited_urls.add(current_url)
                    
                    # Fetch page
                    page_data = await self._fetch_page(current_url)
                    
                    if page_data:
                        pages.append(page_data)
                        pbar.update(1)
                        pbar.set_postfix({
                            'current': current_url[:50] + '...' if len(current_url) > 50 else current_url,
                            'depth': depth
                        })
                        
                        # Add new links to queue (DFS: add to front)
                        if depth < max_depth:
                            new_links = [link for link in page_data.get('links', []) 
                                        if link not in self.visited_urls]
                            # Add new links to front of queue for DFS
                            url_queue = [(link, depth + 1) for link in new_links] + url_queue
                    
                    # Small delay to be respectful
                    await asyncio.sleep(0.1)
            
            logger.info(f"Crawl completed. Visited {len(self.visited_urls)} URLs, processed {len(pages)} pages")
            
            return {
                'pages': pages,
                'total_visited': len(self.visited_urls),
                'successful_pages': len(pages)
            }
    
    async def _check_existing_urls(self, urls: List[str]) -> Dict[str, bool]:
        """Check which URLs already exist in the database"""
        if not self.vector_store:
            return {url: False for url in urls}
        
        try:
            url_check = await self.vector_store.check_urls_exist(urls)
            return {url: info.get('exists', False) for url, info in url_check.items()}
        except Exception as e:
            logger.warning(f"Failed to check existing URLs: {str(e)}")
            return {url: False for url in urls}
    
    async def crawl_domain_with_duplicate_check(self, start_url: str, max_depth: int = 3, max_pages: int = 100, delay: float = 1.0) -> Dict[str, any]:
        """
        Crawl a domain with duplicate URL checking
        Returns both new pages and existing documents
        """
        async with self:
            self.throttler = Throttler(rate_limit=1/delay, period=1.0)
            
            # Initialize
            self.visited_urls.clear()
            new_pages = []
            existing_documents = []
            url_queue = [(start_url, 0)]  # (url, depth)
            
            logger.info(f"Starting crawl with duplicate check from {start_url}")
            logger.info(f"Max depth: {max_depth}, Max pages: {max_pages}, Delay: {delay}s")
            
            with tqdm(total=max_pages, desc="Crawling pages") as pbar:
                while url_queue and len(new_pages) < max_pages:
                    current_url, depth = url_queue.pop(0)  # DFS: pop from front
                    
                    # Skip if already visited or depth exceeded
                    if current_url in self.visited_urls or depth > max_depth:
                        continue
                    
                    self.visited_urls.add(current_url)
                    
                    # Check if URL already exists in database
                    if self.vector_store:
                        url_exists = await self._check_existing_urls([current_url])
                        if url_exists.get(current_url, False):
                            logger.info(f"URL already exists in database, skipping: {current_url}")
                            # Get existing document
                            try:
                                existing_docs = await self.vector_store.get_existing_documents_for_urls([current_url])
                                if existing_docs:
                                    existing_documents.extend(existing_docs)
                                    logger.info(f"Retrieved existing document for: {current_url}")
                            except Exception as e:
                                logger.warning(f"Failed to retrieve existing document for {current_url}: {str(e)}")
                            continue
                    
                    # Fetch page
                    page_data = await self._fetch_page(current_url)
                    
                    if page_data:
                        new_pages.append(page_data)
                        pbar.update(1)
                        pbar.set_postfix({
                            'current': current_url[:50] + '...' if len(current_url) > 50 else current_url,
                            'depth': depth,
                            'new': len(new_pages),
                            'existing': len(existing_documents)
                        })
                        
                        # Add new links to queue (DFS: add to front)
                        if depth < max_depth:
                            new_links = [link for link in page_data.get('links', []) 
                                        if link not in self.visited_urls]
                            # Add new links to front of queue for DFS
                            url_queue = [(link, depth + 1) for link in new_links] + url_queue
                    
                    # Small delay to be respectful
                    await asyncio.sleep(0.1)
            
            logger.info(f"Crawl completed. Visited {len(self.visited_urls)} URLs, "
                       f"processed {len(new_pages)} new pages, "
                       f"retrieved {len(existing_documents)} existing documents")
            
            return {
                'new_pages': new_pages,
                'existing_documents': existing_documents,
                'total_visited': len(self.visited_urls),
                'successful_new_pages': len(new_pages),
                'retrieved_existing_documents': len(existing_documents),
                'start_url': start_url
            }
