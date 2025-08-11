import requests
import feedparser
import re
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
import logging

from config import SCRAPING_CONFIG, SOURCES

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseScraper:
    """Base class for all scrapers"""
    
    def __init__(self, source_id: str, source_config: Dict):
        self.source_id = source_id
        self.source_config = source_config
        
        # Create session with better SSL handling
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification to avoid LibreSSL issues
        self.session.headers.update({
            'User-Agent': random.choice(SCRAPING_CONFIG['user_agents'])
        })
        
        # Disable SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def fetch_list(self) -> List[Dict]:
        """Fetch latest articles - to be implemented by subclasses"""
        raise NotImplementedError
    
    def fetch_article(self, url: str) -> Optional[Dict]:
        """Fetch article content - to be implemented by subclasses"""
        raise NotImplementedError
    
    def _make_request(self, url: str, retries: int = 0) -> Optional[requests.Response]:
        """Make HTTP request with retry logic and rate limiting"""
        if retries >= SCRAPING_CONFIG['max_retries']:
            logger.error(f"Max retries exceeded for {url}")
            return None
        
        try:
            # Random delay to avoid rate limiting
            time.sleep(random.uniform(SCRAPING_CONFIG['request_delay'], SCRAPING_CONFIG['request_delay'] * 2))
            
            # Random user agent
            user_agent = random.choice(SCRAPING_CONFIG['user_agents'])
            
            headers = {
                'User-Agent': user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # Better SSL handling
            response = self.session.get(
                url, 
                headers=headers, 
                timeout=SCRAPING_CONFIG['timeout'],
                allow_redirects=True,
                verify=False  # Disable SSL verification to avoid LibreSSL issues
            )
            
            if response.status_code == 200:
                return response
            elif response.status_code in [429, 503]:  # Rate limited or service unavailable
                logger.warning(f"Rate limited for {url}, waiting longer...")
                time.sleep(SCRAPING_CONFIG['request_delay'] * 3)
                return self._make_request(url, retries + 1)
            else:
                logger.warning(f"HTTP {response.status_code} for {url}")
                return None
                
        except requests.exceptions.SSLError as e:
            logger.warning(f"SSL error for {url}: {e}")
            # Try without SSL verification
            try:
                response = self.session.get(
                    url, 
                    headers=headers, 
                    timeout=SCRAPING_CONFIG['timeout'],
                    allow_redirects=True,
                    verify=False
                )
                return response if response.status_code == 200 else None
            except Exception as e2:
                logger.error(f"SSL retry failed for {url}: {e2}")
                return None
        except Exception as e:
            logger.error(f"Request failed for {url}: {e}")
            time.sleep(SCRAPING_CONFIG['request_delay'])
            return self._make_request(url, retries + 1)
    
    def _clean_url(self, url: str) -> str:
        """Remove tracking parameters and normalize URL"""
        parsed = urlparse(url)
        # Remove common tracking parameters
        query_params = parse_qs(parsed.query)
        clean_params = {k: v for k, v in query_params.items() 
                       if not any(tracker in k.lower() for tracker in ['utm_', 'ref_', 'source', 'campaign'])}
        
        clean_query = '&'.join([f"{k}={v[0]}" for k, v in clean_params.items()])
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}{'?' + clean_query if clean_query else ''}"
    
    def _extract_date(self, text: str) -> Optional[datetime]:
        """Extract date from various formats"""
        if not text:
            return None
        
        # Common date patterns
        patterns = [
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{2}/\d{2}/\d{4})',
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})',
            r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return datetime.strptime(match.group(1), '%Y-%m-%d')
                except ValueError:
                    try:
                        return datetime.strptime(match.group(1), '%d/%m/%Y')
                    except ValueError:
                        try:
                            return datetime.strptime(match.group(1), '%d %b %Y')
                        except ValueError:
                            try:
                                return datetime.strptime(match.group(1), '%d %B %Y')
                            except ValueError:
                                continue
        
        return None

    def _is_url_reachable(self, url: str) -> bool:
        try:
            resp = self.session.head(url, allow_redirects=True, timeout=SCRAPING_CONFIG['timeout'])
            return resp.status_code == 200
        except Exception as e:
            logger.warning(f"URL not reachable: {url} ({e})")
            return False

class RSSScraper(BaseScraper):
    """Scraper for RSS feed sources"""
    
    def fetch_list(self) -> List[Dict]:
        """Fetch latest articles from RSS feed"""
        articles = []
        
        if 'rss' not in self.source_config:
            logger.warning(f"No RSS feed configured for {self.source_id}")
            return articles
        
        response = self._make_request(self.source_config['rss'])
        if not response:
            return articles
        
        try:
            feed = feedparser.parse(response.content)
            cutoff_time = datetime.now() - timedelta(hours=SCRAPING_CONFIG['time_window_hours'])
            
            for entry in feed.entries:
                # Extract date
                pub_date = None
                if hasattr(entry, 'published_parsed'):
                    pub_date = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed'):
                    pub_date = datetime(*entry.updated_parsed[:6])
                
                if pub_date and pub_date < cutoff_time:
                    continue
                
                article = {
                    'title': entry.title,
                    'url': self._clean_url(entry.link),
                    'published_at': pub_date,
                    'source': self.source_config['name'],
                    'source_id': self.source_id,
                    'category': self.source_config['category']
                }
                # Remove the overly strict URL check - RSS feeds are generally reliable
                # We'll validate URLs when actually fetching content later
                articles.append(article)
                
        except Exception as e:
            logger.error(f"Error parsing RSS feed for {self.source_id}: {e}")
        
        return articles
    
    def fetch_article(self, url: str) -> Optional[Dict]:
        """Fetch article content"""
        response = self._make_request(url)
        if not response:
            return None
        
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = None
            title_selectors = ['h1', '.title', '.headline', 'title']
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text().strip()
                    break
            
            # Extract text content
            text_content = []
            content_selectors = [
                'article', '.content', '.post-content', '.entry-content',
                '.article-body', '.story-content'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Remove script and style elements
                    for script in content_elem(["script", "style"]):
                        script.decompose()
                    
                    text_content = [p.get_text().strip() for p in content_elem.find_all(['p', 'h2', 'h3', 'h4'])]
                    text_content = [text for text in text_content if len(text) > 50]  # Filter short paragraphs
                    break
            
            # Extract byline/author
            byline = None
            byline_selectors = ['.byline', '.author', '.writer', '[rel="author"]']
            for selector in byline_selectors:
                byline_elem = soup.select_one(selector)
                if byline_elem:
                    byline = byline_elem.get_text().strip()
                    break
            
            return {
                'title': title,
                'text': '\n'.join(text_content),
                'byline': byline,
                'url': url
            }
            
        except Exception as e:
            logger.error(f"Error parsing article {url}: {e}")
            return None

class RedditScraper(BaseScraper):
    """Scraper for Reddit sources"""
    
    def fetch_list(self) -> List[Dict]:
        """Fetch latest posts from Reddit"""
        articles = []
        
        # Reddit JSON API for public data
        subreddit = self.source_id.replace('reddit_', '')
        json_url = f"https://reddit.com/r/{subreddit}/hot.json"
        
        response = self._make_request(json_url)
        if not response:
            return articles
        
        try:
            data = response.json()
            cutoff_time = datetime.now() - timedelta(hours=SCRAPING_CONFIG['time_window_hours'])
            
            for post in data['data']['children']:
                post_data = post['data']
                
                # Convert Reddit timestamp to datetime
                pub_date = datetime.fromtimestamp(post_data['created_utc'])
                
                if pub_date < cutoff_time:
                    continue
                
                # Only include posts with external links (news articles)
                if post_data['is_self']:
                    continue
                
                article = {
                    'title': post_data['title'],
                    'url': self._clean_url(post_data['url']),
                    'published_at': pub_date,
                    'source': self.source_config['name'],
                    'source_id': self.source_id,
                    'category': self.source_config['category'],
                    'reddit_score': post_data['score'],
                    'reddit_comments': post_data['num_comments']
                }
                # Remove the overly strict URL check - Reddit JSON API is reliable
                articles.append(article)
                
        except Exception as e:
            logger.error(f"Error parsing Reddit data for {self.source_id}: {e}")
        
        return articles

class TheInformationScraper(BaseScraper):
    """Special scraper for The Information (public pages only)"""
    
    def fetch_list(self) -> List[Dict]:
        """Fetch latest articles from The Information homepage"""
        articles = []
        
        response = self._make_request(self.source_config['url'])
        if not response:
            return articles
        
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            cutoff_time = datetime.now() - timedelta(hours=SCRAPING_CONFIG['time_window_hours'])
            
            # Look for article links on homepage
            article_links = soup.find_all('a', href=re.compile(r'/articles/'))
            
            for link in article_links[:20]:  # Limit to first 20 articles
                url = urljoin(self.source_config['url'], link['href'])
                
                # Extract title
                title = link.get_text().strip()
                if not title:
                    continue
                
                # For The Information, we'll use current time as we can't easily get publish date
                # In a real implementation, you'd need to visit each article page
                pub_date = datetime.now()
                
                article = {
                    'title': title,
                    'url': self._clean_url(url),
                    'published_at': pub_date,
                    'source': self.source_config['name'],
                    'source_id': self.source_id,
                    'category': self.source_config['category']
                }
                # Remove the overly strict URL check - we're scraping public pages
                articles.append(article)
                
        except Exception as e:
            logger.error(f"Error parsing The Information for {self.source_id}: {e}")
        
        return articles

def get_scraper(source_id: str) -> BaseScraper:
    """Factory function to get the appropriate scraper for a source"""
    source_config = SOURCES[source_id]
    
    if source_id.startswith('reddit_'):
        return RedditScraper(source_id, source_config)
    elif source_id == 'theinformation':
        return TheInformationScraper(source_id, source_config)
    else:
        return RSSScraper(source_id, source_config)

def scrape_all_sources() -> List[Dict]:
    """Scrape all configured sources"""
    all_articles = []
    
    for source_id, source_config in SOURCES.items():
        try:
            scraper = get_scraper(source_id)
            articles = scraper.fetch_list()
            logger.info(f"Scraped {len(articles)} articles from {source_config['name']}")
            all_articles.extend(articles)
            
        except Exception as e:
            logger.error(f"Error scraping {source_id}: {e}")
            continue
    
    return all_articles

def fetch_article_content(url: str, source_id: str) -> Optional[Dict]:
    """Fetch content for a specific article"""
    source_config = SOURCES[source_id]
    scraper = get_scraper(source_id)
    return scraper.fetch_article(url) 