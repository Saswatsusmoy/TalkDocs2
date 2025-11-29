import asyncio
import aiohttp
from collections import deque
from urllib.parse import urljoin, urlparse, urlunparse, parse_qsl, urlencode
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from typing import Set, List, Dict, Optional, Tuple
import logging
from asyncio_throttle import Throttler
from tqdm.asyncio import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import time
import hashlib

logger = logging.getLogger(__name__)

class WebCrawler:
    def __init__(
        self,
        vector_store=None,
        *,
        max_retries: int = 3,
        backoff_factor: float = 1.5,
        persistence_workers: int = 3,
        max_concurrent_requests: int = 10,
        parse_workers: int = 4,
        user_agent: str = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        ),
    ):
        self.visited_fingerprints: Set[str] = set()
        self.session: Optional[aiohttp.ClientSession] = None
        self.throttler: Optional[Throttler] = None
        self.vector_store = vector_store
        self.robot_parsers: Dict[str, RobotFileParser] = {}
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.persistence_workers = max(1, persistence_workers)
        self.max_concurrent_requests = max(1, max_concurrent_requests)
        self.parse_workers = max(1, parse_workers)
        self.user_agent = user_agent
        self._fingerprint_cache: Dict[str, str] = {}
        self._parse_executor: Optional[ThreadPoolExecutor] = None
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._content_hashes: Set[str] = set()  # Track content hashes to detect duplicate pages
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                "User-Agent": self.user_agent
            }
        )
        # Initialize thread pool for HTML parsing
        self._parse_executor = ThreadPoolExecutor(max_workers=self.parse_workers)
        # Initialize semaphore for concurrent request limiting
        self._semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self._parse_executor:
            self._parse_executor.shutdown(wait=True)
    
    def _normalize_url(self, url: str) -> str:
        """Canonicalize URL for consistent comparison with improved duplicate detection"""
        if url in self._fingerprint_cache:
            return self._fingerprint_cache[url]
        
        try:
            parsed_url = urlparse(url)
            
            # Normalize scheme
            scheme = parsed_url.scheme.lower()
            if not scheme:
                scheme = 'https'  # Default to https
            
            # Normalize netloc (handle www, case, port)
            netloc = parsed_url.netloc.lower()
            # Remove www. prefix for consistency (optional - can be configured)
            if netloc.startswith('www.'):
                netloc = netloc[4:]
            # Remove default ports
            if ':80' in netloc and scheme == 'http':
                netloc = netloc.replace(':80', '')
            elif ':443' in netloc and scheme == 'https':
                netloc = netloc.replace(':443', '')
            
            # Normalize path
            path = parsed_url.path
            # Remove trailing slash (except for root)
            if path != '/' and path.endswith('/'):
                path = path[:-1]
            # Normalize multiple slashes
            path = re.sub(r'/+', '/', path) or '/'
            # Decode URL encoding for better comparison
            try:
                from urllib.parse import unquote
                path = unquote(path)
            except:
                pass
            
            # Normalize params (usually empty, but handle if present)
            params = parsed_url.params
            
            # Sort query params for consistent ordering
            if parsed_url.query:
                query_pairs = parse_qsl(parsed_url.query, keep_blank_values=True)
                # Remove common tracking parameters that don't affect content
                filtered_pairs = []
                skip_params = {'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
                              'ref', 'source', 'fbclid', 'gclid', '_ga', '_gl'}
                for key, value in query_pairs:
                    if key.lower() not in skip_params:
                        filtered_pairs.append((key.lower(), value))
                query = urlencode(sorted(filtered_pairs)) if filtered_pairs else ''
            else:
                query = ''
            
            # Remove fragment (anchor) - it doesn't affect page content
            normalized = urlunparse((scheme, netloc, path, params, query, ''))
            self._fingerprint_cache[url] = normalized
            return normalized
        except Exception as e:
            logger.warning(f"Failed to normalize URL {url}: {str(e)}")
            # Fallback to original URL
            return url
    
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
    
    async def _get_robot_parser(self, base_url: str) -> Optional[RobotFileParser]:
        """Retrieve and cache robots.txt parser for domain"""
        parsed = urlparse(base_url)
        robots_url = urlunparse((parsed.scheme, parsed.netloc, '/robots.txt', '', '', ''))
        
        if robots_url in self.robot_parsers:
            return self.robot_parsers[robots_url]
        
        parser = RobotFileParser()
        parser.set_url(robots_url)
        
        if not self.session:
            self.robot_parsers[robots_url] = None
            return None
        
        try:
            async with self.session.get(robots_url) as response:
                if response.status == 200:
                    content = await response.text()
                    parser.parse(content.splitlines())
                    self.robot_parsers[robots_url] = parser
                else:
                    self.robot_parsers[robots_url] = None
        except Exception as e:
            logger.debug(f"Failed to load robots.txt from {robots_url}: {str(e)}")
            self.robot_parsers[robots_url] = None
        
        return self.robot_parsers[robots_url]
    
    async def _is_allowed_by_robots(self, url: str, base_url: str) -> bool:
        """Check robots.txt rules for the target URL"""
        parser = await self._get_robot_parser(base_url)
        if parser is None:
            return True
        try:
            return parser.can_fetch(self.user_agent, url)
        except Exception:
            return True
    
    async def _should_visit(self, url: str, depth: int, max_depth: int, base_domain: str) -> Tuple[bool, Optional[str]]:
        """Determine whether a URL should be visited and return its fingerprint"""
        if depth > max_depth:
            return False, None
        
        if not self._is_valid_url(url, base_domain):
            return False, None
        
        normalized = self._normalize_url(url)
        if normalized in self.visited_fingerprints:
            return False, normalized
        
        if not await self._is_allowed_by_robots(url, base_domain):
            logger.info(f"Robots.txt disallows crawling: {url}")
            return False, normalized
        
        return True, normalized
    
    def _extract_canonical_url(self, soup: BeautifulSoup, current_url: str) -> Optional[str]:
        """Extract canonical URL from HTML if present"""
        try:
            # Check for canonical link tag
            canonical = soup.find('link', rel='canonical')
            if canonical and canonical.get('href'):
                canonical_url = canonical['href']
                # Make absolute if relative
                if not canonical_url.startswith('http'):
                    canonical_url = urljoin(current_url, canonical_url)
                return canonical_url
        except Exception as e:
            logger.debug(f"Failed to extract canonical URL: {str(e)}")
        return None
    
    def _compute_content_hash(self, content: str) -> str:
        """Compute hash of content for duplicate detection"""
        # Normalize content: lowercase, remove extra whitespace
        normalized = re.sub(r'\s+', ' ', content.lower().strip())
        # Compute hash
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()
    
    def _is_duplicate_content(self, content: str) -> bool:
        """Check if content hash has been seen before"""
        content_hash = self._compute_content_hash(content)
        if content_hash in self._content_hashes:
            return True
        self._content_hashes.add(content_hash)
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
    
    def _parse_html_in_thread(self, html: str, url: str) -> Dict[str, any]:
        """Parse HTML in a separate thread (CPU-intensive operation) with duplicate detection"""
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Check for canonical URL - use it if present
            canonical_url = self._extract_canonical_url(soup, url)
            if canonical_url:
                canonical_normalized = self._normalize_url(canonical_url)
                # If canonical URL is different, mark current URL as duplicate
                current_normalized = self._normalize_url(url)
                if canonical_normalized != current_normalized:
                    logger.info(f"Canonical URL found: {canonical_url} (current: {url})")
                    # Use canonical URL for the page
                    url = canonical_url
            
            # Extract content
            page_data = self._extract_content(soup)
            
            # Check for duplicate content using content hash
            if page_data.get('content'):
                if self._is_duplicate_content(page_data['content']):
                    logger.info(f"Duplicate content detected for {url}, skipping")
                    return None
            
            page_data['url'] = url
            page_data['timestamp'] = time.time()
            
            # Extract links for further crawling
            links = []
            seen_links = set()  # Track normalized links to avoid duplicates
            for link in soup.find_all('a', href=True):
                href = link['href']
                absolute_url = urljoin(url, href)
                if self._is_valid_url(absolute_url, url):
                    # Normalize link to avoid duplicate variations
                    normalized_link = self._normalize_url(absolute_url)
                    if normalized_link not in seen_links:
                        seen_links.add(normalized_link)
                        links.append(absolute_url)
            
            page_data['links'] = links
            return page_data
        except Exception as e:
            logger.error(f"Error parsing HTML for {url}: {str(e)}")
            return None
    
    async def _fetch_page(self, url: str) -> Optional[Dict]:
        """Fetch a single page and extract content with parallel processing"""
        attempt = 0
        while attempt < self.max_retries:
            try:
                # Use semaphore to limit concurrent requests
                async with self._semaphore:
                    async with self.throttler:
                        async with self.session.get(url) as response:
                            if response.status != 200:
                                logger.warning(f"Failed to fetch {url}: HTTP {response.status}")
                                if 400 <= response.status < 500:
                                    return None
                                raise aiohttp.ClientError(f"HTTP {response.status}")
                            
                            content_type = response.headers.get('content-type', '').lower()
                            if 'text/html' not in content_type:
                                logger.info(f"Skipping non-HTML content: {url}")
                                return None
                            
                            html = await response.text()
                            
                            # Parse HTML in thread pool (CPU-intensive)
                            loop = asyncio.get_event_loop()
                            page_data = await loop.run_in_executor(
                                self._parse_executor,
                                self._parse_html_in_thread,
                                html,
                                url
                            )
                            
                            if page_data:
                                logger.info(f"Successfully processed: {url}")
                                return page_data
                            return None
            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching {url} (attempt {attempt + 1}/{self.max_retries})")
            except aiohttp.ClientError as e:
                logger.warning(f"Network error fetching {url}: {str(e)} (attempt {attempt + 1}/{self.max_retries})")
            except Exception as e:
                logger.warning(f"Error fetching {url}: {str(e)} (attempt {attempt + 1}/{self.max_retries})")
            
            attempt += 1
            if attempt < self.max_retries:
                backoff = self.backoff_factor ** attempt
                await asyncio.sleep(backoff)
        
        logger.error(f"Exceeded max retries for {url}")
        return None
    
    async def _persistence_worker(self, queue: asyncio.Queue, new_pages: List[Dict], source_url: str):
        """Persist fetched pages asynchronously"""
        while True:
            page = await queue.get()
            if page is None:
                queue.task_done()
                break
            
            if not self.vector_store:
                new_pages.append(page)
                queue.task_done()
                continue
            
            try:
                await self.vector_store.store_documents([page], source_url=source_url)
                new_pages.append(page)
            except Exception as e:
                logger.error(f"Failed to persist page {page.get('url')}: {str(e)}")
            finally:
                queue.task_done()
    
    async def crawl_domain(self, start_url: str, max_depth: int = 3, max_pages: int = 1000, delay: float = 0.3) -> Dict:
        """
        Crawl a domain using DFS (Depth-First Search)
        """
        async with self:
            self.throttler = Throttler(rate_limit=1/delay, period=1.0)
            
            # Initialize
            self.visited_fingerprints.clear()
            self._fingerprint_cache.clear()
            self._content_hashes.clear()  # Reset content hashes for new crawl
            pages = []
            pages_collected = 0
            url_queue = deque([(start_url, 0)])  # (url, depth)
            
            logger.info(f"Starting DFS crawl from {start_url}")
            logger.info(f"Max depth: {max_depth}, Max pages: {max_pages}, Delay: {delay}s")
            
            with tqdm(total=max_pages, desc="Crawling pages") as pbar:
                while url_queue and pages_collected < max_pages:
                    current_url, depth = url_queue.pop()  # DFS: LIFO
                    
                    should_visit, fingerprint = await self._should_visit(
                        current_url, depth, max_depth, start_url
                    )
                    if not should_visit:
                        continue
                    
                    if fingerprint:
                        self.visited_fingerprints.add(fingerprint)
                    
                    # Fetch page
                    page_data = await self._fetch_page(current_url)
                    
                    if page_data:
                        pages.append(page_data)
                        pages_collected += 1
                        pbar.update(1)
                        pbar.set_postfix({
                            'current': current_url[:50] + '...' if len(current_url) > 50 else current_url,
                            'depth': depth
                        })
                        
                        # Add new links to queue (DFS: add to front)
                        if depth < max_depth:
                            new_links = [
                                link for link in page_data.get('links', [])
                                if self._normalize_url(link) not in self.visited_fingerprints
                            ]
                            for link in new_links:
                                url_queue.append((link, depth + 1))
                    
                    # Small delay to be respectful
                    await asyncio.sleep(0.1)
            
            logger.info(f"Crawl completed. Visited {len(self.visited_fingerprints)} URLs, processed {len(pages)} pages")
            
            return {
                'pages': pages,
                'total_visited': len(self.visited_fingerprints),
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
    
    async def crawl_domain_with_duplicate_check(self, start_url: str, max_depth: int = 3, max_pages: int = 1000, delay: float = 0.3) -> Dict[str, any]:
        """
        Crawl a domain with duplicate URL checking
        Returns both new pages and existing documents
        """
        async with self:
            self.throttler = Throttler(rate_limit=1/delay, period=1.0)
            
            # Initialize
            self.visited_fingerprints.clear()
            self._fingerprint_cache.clear()
            self._content_hashes.clear()  # Reset content hashes for new crawl
            new_pages = []
            new_pages_count = 0
            existing_documents = []
            url_queue = deque([(start_url, 0)])  # (url, depth)
            page_queue: Optional[asyncio.Queue] = None
            persistence_tasks: List[asyncio.Task] = []
            
            if self.vector_store:
                page_queue = asyncio.Queue()
                for _ in range(self.persistence_workers):
                    task = asyncio.create_task(
                        self._persistence_worker(page_queue, new_pages, start_url)
                    )
                    persistence_tasks.append(task)
            
            logger.info(f"Starting crawl with duplicate check from {start_url}")
            logger.info(f"Max depth: {max_depth}, Max pages: {max_pages}, Delay: {delay}s")
            
            async def process_url(url_info: Tuple[str, int]) -> Optional[Dict]:
                """Process a single URL and return page data"""
                url, depth = url_info
                
                should_visit, fingerprint = await self._should_visit(
                    url, depth, max_depth, start_url
                )
                if not should_visit:
                    return None
                
                if fingerprint:
                    self.visited_fingerprints.add(fingerprint)
                
                # Check if URL already exists in database
                if self.vector_store:
                    url_exists = await self._check_existing_urls([url])
                    if url_exists.get(url, False):
                        logger.info(f"URL already exists in database, skipping: {url}")
                        # Get existing document
                        try:
                            existing_docs = await self.vector_store.get_existing_documents_for_urls([url])
                            if existing_docs:
                                existing_documents.extend(existing_docs)
                                logger.info(f"Retrieved existing document for: {url}")
                        except Exception as e:
                            logger.warning(f"Failed to retrieve existing document for {url}: {str(e)}")
                        return None
                
                # Fetch page
                page_data = await self._fetch_page(url)
                return (page_data, url, depth) if page_data else None
            
            with tqdm(total=max_pages, desc="Crawling pages") as pbar:
                while url_queue and new_pages_count < max_pages:
                    # Process multiple URLs concurrently
                    batch_size = min(self.max_concurrent_requests, max_pages - new_pages_count)
                    batch = []
                    
                    # Collect a batch of URLs to process
                    while url_queue and len(batch) < batch_size:
                        batch.append(url_queue.pop())
                    
                    if not batch:
                        break
                    
                    # Process batch concurrently
                    tasks = [process_url(url_info) for url_info in batch]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Process results
                    for i, result in enumerate(results):
                        if isinstance(result, Exception):
                            logger.error(f"Error processing URL: {str(result)}")
                            continue
                        
                        if result:  # (page_data, url, depth)
                            page_data, url, depth = result
                            
                            if page_queue:
                                await page_queue.put(page_data)
                            else:
                                new_pages.append(page_data)
                            
                            new_pages_count += 1
                            pbar.update(1)
                            pbar.set_postfix({
                                'current': url[:50] + '...' if len(url) > 50 else url,
                                'depth': depth,
                                'new': new_pages_count,
                                'existing': len(existing_documents),
                                'concurrent': len(batch)
                            })
                            
                            # Add new links to queue (DFS)
                            if depth < max_depth:
                                new_links = [
                                    link for link in page_data.get('links', [])
                                    if self._normalize_url(link) not in self.visited_fingerprints
                                ]
                                for link in new_links:
                                    url_queue.append((link, depth + 1))
                    
                    # Small delay between batches
                    if url_queue and new_pages_count < max_pages:
                        await asyncio.sleep(0.05)
            
            # Ensure persistence tasks finish processing
            if page_queue:
                for _ in persistence_tasks:
                    await page_queue.put(None)
                await page_queue.join()
                await asyncio.gather(*persistence_tasks, return_exceptions=True)
            
            logger.info(f"Crawl completed. Visited {len(self.visited_fingerprints)} URLs, "
                       f"processed {len(new_pages)} new pages, "
                       f"retrieved {len(existing_documents)} existing documents")
            
            return {
                'new_pages': new_pages,
                'existing_documents': existing_documents,
                'total_visited': len(self.visited_fingerprints),
                'successful_new_pages': len(new_pages),
                'retrieved_existing_documents': len(existing_documents),
                'start_url': start_url
            }
