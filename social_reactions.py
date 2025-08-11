import requests
import logging
import re
import time
from typing import List, Dict, Optional
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from config import SCRAPING_CONFIG

logger = logging.getLogger(__name__)

class SocialReactionsScraper:
    """Scrape public social reactions for news articles"""
    
    def __init__(self):
        """Initialize the social reactions scraper"""
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification to avoid LibreSSL issues
        
        # Disable SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Set default headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def _make_request(self, url: str, retries: int = 0) -> Optional[requests.Response]:
        """Make HTTP request with retry logic"""
        if retries >= SCRAPING_CONFIG['max_retries']:
            logger.warning(f"Max retries exceeded for {url}")
            return None
        
        try:
            # Add delay to avoid rate limiting
            time.sleep(SCRAPING_CONFIG['request_delay'])
            
            response = self.session.get(
                url, 
                timeout=SCRAPING_CONFIG['timeout'],
                allow_redirects=True
            )
            
            if response.status_code == 200:
                return response
            elif response.status_code in [429, 503]:  # Rate limited
                logger.warning(f"Rate limited for {url}, waiting...")
                time.sleep(SCRAPING_CONFIG['request_delay'] * 2)
                return self._make_request(url, retries + 1)
            else:
                logger.warning(f"HTTP {response.status_code} for {url}")
                return None
                
        except requests.exceptions.SSLError as e:
            logger.warning(f"SSL error for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Request failed for {url}: {e}")
            time.sleep(SCRAPING_CONFIG['request_delay'])
            return self._make_request(url, retries + 1)
    
    def _extract_keywords(self, title: str) -> List[str]:
        """Extract search keywords from article title"""
        # Remove common words and extract key terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        # Clean title
        title = re.sub(r'[^\w\s]', ' ', title.lower())
        words = title.split()
        
        # Filter out stop words and short words
        keywords = [word for word in words if word not in stop_words and len(word) > 3]
        
        # Take top 3-5 keywords
        return keywords[:5]
    
    def _is_permalink_reachable(self, url: str) -> bool:
        """Check if permalink URL format is valid (less strict than actual reachability)"""
        try:
            # Just check if URL format is valid, don't actually test reachability
            # Social media URLs are generally reliable
            if url.startswith(('http://', 'https://')):
                return True
            return False
        except Exception as e:
            logger.warning(f"Invalid permalink format: {url} ({e})")
            return False
    
    def scrape_twitter_reactions(self, article: Dict) -> List[Dict]:
        """Scrape Twitter reactions for an article"""
        reactions = []
        title = article.get('title', '')
        keywords = self._extract_keywords(title)
        
        if not keywords:
            return reactions
        
        # Search for tweets about this story
        search_terms = ' '.join(keywords[:3])  # Use top 3 keywords
        search_url = f"https://twitter.com/search?q={quote_plus(search_terms)}&src=typed_query&f=live"
        
        response = self._make_request(search_url)
        if not response:
            return reactions
        
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for tweet elements (this is a simplified approach)
            tweet_elements = soup.find_all('article')
            
            for tweet in tweet_elements[:10]:  # Limit to first 10 tweets
                try:
                    # Extract tweet text
                    text_elem = tweet.find('div', {'data-testid': 'tweetText'})
                    if not text_elem:
                        continue
                    
                    text = text_elem.get_text().strip()
                    if len(text) < 10:  # Skip very short tweets
                        continue
                    
                    # Extract engagement metrics (simplified)
                    engagement = {
                        'likes': 0,
                        'retweets': 0,
                        'replies': 0
                    }
                    
                    # Try to find engagement elements
                    like_elem = tweet.find('div', {'data-testid': 'like'})
                    if like_elem:
                        like_text = like_elem.get_text()
                        if like_text.isdigit():
                            engagement['likes'] = int(like_text)
                    
                    # Extract author info
                    author_elem = tweet.find('span', {'class': 'css-901oao'})
                    author = author_elem.get_text() if author_elem else "Unknown"
                    
                    # Try to extract permalink (simplified approach)
                    # In a real implementation, you'd need to parse the tweet structure more carefully
                    permalink = f"https://twitter.com/{author}/status/{hash(text)}"  # Placeholder
                    
                    # Create reaction object
                    reaction = {
                        'platform': 'twitter',
                        'text': text[:200] + '...' if len(text) > 200 else text,
                        'author': author,
                        'engagement': engagement,
                        'permalink': permalink,
                        'score': engagement['likes'] + engagement['retweets'] * 2 + engagement['replies']
                    }
                    
                    # Only include if permalink format is valid
                    if self._is_permalink_reachable(permalink):
                        reactions.append(reaction)
                    
                except Exception as e:
                    logger.warning(f"Error parsing tweet: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error scraping Twitter reactions: {e}")
        
        return reactions
    
    def scrape_reddit_reactions(self, article: Dict) -> List[Dict]:
        """Scrape Reddit reactions for an article"""
        reactions = []
        title = article.get('title', '')
        url = article.get('url', '')
        
        # Search for Reddit posts linking to this article
        search_url = f"https://reddit.com/search.json?q=url:{quote_plus(url)}&restrict_sr=on&sort=relevance&t=day"
        
        response = self._make_request(search_url)
        if not response:
            return reactions
        
        try:
            data = response.json()
            
            for post in data.get('data', {}).get('children', []):
                post_data = post['data']
                
                # Extract post info
                post_title = post_data.get('title', '')
                post_text = post_data.get('selftext', '')
                subreddit = post_data.get('subreddit', '')
                score = post_data.get('score', 0)
                num_comments = post_data.get('num_comments', 0)
                permalink = f"https://reddit.com{post_data.get('permalink', '')}"
                
                # Create reaction object
                reaction = {
                    'platform': 'reddit',
                    'text': post_text[:200] + '...' if len(post_text) > 200 else post_text,
                    'author': f"r/{subreddit}",
                    'engagement': {
                        'upvotes': score,
                        'comments': num_comments
                    },
                    'permalink': permalink,
                    'score': score + (num_comments * 0.1)
                }
                
                # Only include if permalink format is valid
                if self._is_permalink_reachable(permalink):
                    reactions.append(reaction)
        
        except Exception as e:
            logger.error(f"Error scraping Reddit reactions: {e}")
        
        return reactions
    
    def get_top_reactions(self, article: Dict, max_reactions: int = 2) -> List[Dict]:
        """Get top reactions for an article from all platforms"""
        all_reactions = []
        
        # Scrape Twitter reactions
        twitter_reactions = self.scrape_twitter_reactions(article)
        all_reactions.extend(twitter_reactions)
        
        # Scrape Reddit reactions
        reddit_reactions = self.scrape_reddit_reactions(article)
        all_reactions.extend(reddit_reactions)
        
        # Sort by engagement score
        all_reactions.sort(key=lambda x: x['score'], reverse=True)
        
        # Select top reactions with diverse viewpoints
        selected_reactions = []
        seen_viewpoints = set()
        
        for reaction in all_reactions:
            if len(selected_reactions) >= max_reactions:
                break
            
            # Simple viewpoint diversity check
            text_keywords = set(reaction['text'].lower().split()[:5])
            
            # Check if this reaction has a different viewpoint
            is_diverse = True
            for selected in selected_reactions:
                selected_keywords = set(selected['text'].lower().split()[:5])
                similarity = len(text_keywords & selected_keywords) / len(text_keywords | selected_keywords)
                if similarity > 0.7:  # High similarity threshold
                    is_diverse = False
                    break
            
            if is_diverse:
                selected_reactions.append(reaction)
                seen_viewpoints.add(tuple(sorted(text_keywords)))
        
        return selected_reactions
    
    def scrape_all_reactions(self, articles: List[Dict]) -> Dict[str, List[Dict]]:
        """Scrape reactions for all articles"""
        article_reactions = {}
        
        for i, article in enumerate(articles):
            logger.info(f"Scraping reactions for article {i+1}/{len(articles)}: {article.get('title', '')[:50]}...")
            
            reactions = self.get_top_reactions(article)
            article_reactions[article.get('url', '')] = reactions
            
            # Rate limiting between articles
            time.sleep(SCRAPING_CONFIG['request_delay'] * 2)
        
        return article_reactions 