import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import urljoin, urlparse
import validators
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import logging

class WebCrawler:
    def __init__(self, base_url, max_pages=50, delay=1, create_sitemap=True):
        self.base_url = base_url
        self.max_pages = max_pages
        self.delay = delay
        self.create_sitemap = create_sitemap
        self.visited_urls = set()
        self.pages_data = []
        self.sitemap = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Setup logging (disabled to reduce console output)
        logging.basicConfig(level=logging.WARNING)
        self.logger = logging.getLogger(__name__)
        
        # Initialize Selenium driver for JavaScript-heavy sites
        self.driver = None
        
    def setup_selenium(self):
        """Setup Selenium WebDriver for JavaScript-heavy sites"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup Selenium: {e}")
            return False
    
    def create_detailed_sitemap(self):
        """Create a detailed sitemap of the website before crawling"""
        self.logger.info("Creating detailed sitemap...")
        
        # Setup Selenium for sitemap creation
        self.setup_selenium()
        
        sitemap_urls = set()
        urls_to_scan = [self.base_url]
        scanned_urls = set()
        
        # First pass: discover all URLs
        while urls_to_scan and len(scanned_urls) < min(self.max_pages * 2, 2000):  # Scan more URLs for sitemap
            current_url = urls_to_scan.pop(0)
            
            if current_url in scanned_urls:
                continue
                
            self.logger.info(f"Scanning for sitemap: {current_url}")
            
            # Get page content
            soup = self.get_page_content(current_url)
            if not soup:
                scanned_urls.add(current_url)
                continue
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "No Title"
            
            # Add to sitemap
            sitemap_urls.add(current_url)
            self.sitemap[current_url] = {
                'title': title_text,
                'url': current_url,
                'discovered_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            scanned_urls.add(current_url)
            
            # Extract links for further scanning
            links = self.extract_links(soup, current_url)
            for link in links:
                if (link not in scanned_urls and 
                    link not in urls_to_scan and 
                    self.is_valid_url(link)):
                    urls_to_scan.append(link)
            
            # Respect delay
            time.sleep(self.delay / 2)  # Faster scanning for sitemap
        
        # Cleanup Selenium
        if self.driver:
            self.driver.quit()
            self.driver = None
        
        self.logger.info(f"Sitemap created with {len(sitemap_urls)} URLs")
        return list(sitemap_urls)
    
    def get_page_content(self, url):
        """Get page content using both requests and Selenium if needed"""
        try:
            # First try with requests
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check if page needs JavaScript
            if self.needs_javascript(soup):
                if self.driver:
                    return self.get_content_with_selenium(url)
                else:
                    self.logger.warning(f"JavaScript needed for {url} but Selenium not available")
            
            return soup
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def needs_javascript(self, soup):
        """Check if page needs JavaScript to render content"""
        # Check for common indicators of JavaScript-heavy sites
        scripts = soup.find_all('script')
        noscript = soup.find('noscript')
        
        # If there are many scripts or noscript tag, likely needs JS
        if len(scripts) > 5 or noscript:
            return True
        
        # Check for React/Angular/Vue indicators
        body = soup.find('body')
        if body and ('ng-app' in str(body) or 'react' in str(body) or 'vue' in str(body)):
            return True
            
        return False
    
    def get_content_with_selenium(self, url):
        """Get page content using Selenium"""
        try:
            self.driver.get(url)
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(2)  # Additional wait for dynamic content
            
            page_source = self.driver.page_source
            return BeautifulSoup(page_source, 'html.parser')
            
        except Exception as e:
            self.logger.error(f"Selenium failed for {url}: {e}")
            return None
    
    def extract_text_content(self, soup):
        """Extract clean text content from BeautifulSoup object"""
        if not soup:
            return ""
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def extract_links(self, soup, base_url):
        """Extract all links from the page"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            
            # Only include links from the same domain
            if self.is_same_domain(full_url, base_url):
                links.append(full_url)
        
        return list(set(links))  # Remove duplicates
    
    def is_same_domain(self, url1, url2):
        """Check if two URLs are from the same domain"""
        try:
            domain1 = urlparse(url1).netloc
            domain2 = urlparse(url2).netloc
            return domain1 == domain2
        except:
            return False
    
    def is_valid_url(self, url):
        """Check if URL is valid and should be crawled"""
        if not validators.url(url):
            return False
        
        # Skip common non-content URLs
        skip_patterns = [
            r'\.(pdf|doc|docx|xls|xlsx|ppt|pptx|zip|rar|exe|dmg)$',
            r'\.(jpg|jpeg|png|gif|svg|ico|css|js)$',
            r'#',
            r'mailto:',
            r'tel:',
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        return True
    
    def crawl(self):
        """Main crawling method"""
        self.logger.info(f"Starting crawl of {self.base_url}")
        
        # Create sitemap first if requested
        if self.create_sitemap:
            sitemap_urls = self.create_detailed_sitemap()
            # Use sitemap URLs for crawling
            urls_to_visit = sitemap_urls[:self.max_pages]
        else:
            # Setup Selenium if needed
            self.setup_selenium()
            urls_to_visit = [self.base_url]
        
        # Setup Selenium for content crawling
        if not self.driver:
            self.setup_selenium()
        
        while urls_to_visit and len(self.visited_urls) < self.max_pages:
            current_url = urls_to_visit.pop(0)
            
            if current_url in self.visited_urls:
                continue
                
            self.logger.info(f"Crawling: {current_url}")
            
            # Get page content
            soup = self.get_page_content(current_url)
            if not soup:
                continue
            
            # Extract content
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "No Title"
            
            content = self.extract_text_content(soup)
            
            # Store page data
            page_data = {
                'url': current_url,
                'title': title_text,
                'content': content,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.pages_data.append(page_data)
            self.visited_urls.add(current_url)
            
            # Extract links for further crawling (only if not using sitemap)
            if not self.create_sitemap and len(self.visited_urls) < self.max_pages:
                links = self.extract_links(soup, current_url)
                for link in links:
                    if (link not in self.visited_urls and 
                        link not in urls_to_visit and 
                        self.is_valid_url(link)):
                        urls_to_visit.append(link)
            
            # Respect delay
            time.sleep(self.delay)
        
        # Cleanup
        if self.driver:
            self.driver.quit()
        
        self.logger.info(f"Crawling completed. Visited {len(self.visited_urls)} pages.")
        return self.pages_data
    
    def save_to_json(self, filename='crawled_data.json'):
        """Save crawled data to JSON file"""
        data = {
            'base_url': self.base_url,
            'total_pages': len(self.pages_data),
            'crawl_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'pages': self.pages_data,
            'sitemap': self.sitemap if self.create_sitemap else None
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Data saved to {filename}")
        return filename
    
    def save_sitemap_to_json(self, filename='sitemap.json'):
        """Save sitemap to separate JSON file"""
        if not self.sitemap:
            self.logger.warning("No sitemap available to save")
            return None
        
        sitemap_data = {
            'base_url': self.base_url,
            'total_urls': len(self.sitemap),
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'urls': self.sitemap
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(sitemap_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Sitemap saved to {filename}")
        return filename

def crawl_website(url, max_pages=50, output_file='crawled_data.json', create_sitemap=True):
    """Convenience function to crawl a website"""
    crawler = WebCrawler(url, max_pages=max_pages, create_sitemap=create_sitemap)
    crawler.crawl()
    return crawler.save_to_json(output_file)

if __name__ == "__main__":
    # Example usage
    url = "https://example.com"
    crawl_website(url, max_pages=10)
