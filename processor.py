import re
import hashlib
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging
from difflib import SequenceMatcher
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from config import IMPACT_CRITERIA, RANKING_WEIGHTS

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

logger = logging.getLogger(__name__)

class NewsProcessor:
    """Process and rank news articles"""
    
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            max_features=1000
        )
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        if not text:
            return ""
        
        # Convert to lowercase and remove special characters
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _compute_fingerprint(self, text: str) -> str:
        """Compute a content fingerprint"""
        normalized = self._normalize_text(text)
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _compute_similarity(self, text1: str, text2: str) -> float:
        """Compute similarity between two texts"""
        if not text1 or not text2:
            return 0.0
        
        normalized1 = self._normalize_text(text1)
        normalized2 = self._normalize_text(text2)
        
        # Use sequence matcher for title similarity
        return SequenceMatcher(None, normalized1, normalized2).ratio()
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        if not text:
            return []
        
        tokens = word_tokenize(text.lower())
        keywords = [token for token in tokens 
                   if token.isalpha() and token not in self.stop_words and len(token) > 2]
        return keywords[:20]  # Limit to top 20 keywords
    
    def deduplicate_articles(self, articles: List[Dict]) -> List[Dict]:
        """Deduplicate articles based on title and content similarity"""
        if not articles:
            return []
        
        # Sort by publish date (earliest first)
        articles = sorted(articles, key=lambda x: x.get('published_at', datetime.now()))
        
        unique_articles = []
        seen_fingerprints = set()
        
        for article in articles:
            title = article.get('title', '')
            url = article.get('url', '')
            
            # Create fingerprint from title and URL
            fingerprint = self._compute_fingerprint(f"{title} {url}")
            
            # Check if we've seen this exact content
            if fingerprint in seen_fingerprints:
                continue
            
            # Check for similar titles
            is_duplicate = False
            for existing in unique_articles:
                existing_title = existing.get('title', '')
                
                # High similarity threshold for titles
                if self._compute_similarity(title, existing_title) > 0.8:
                    # Merge sources if it's the same story
                    if 'sources' not in existing:
                        existing['sources'] = [existing.get('source', '')]
                    existing['sources'].append(article.get('source', ''))
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_fingerprints.add(fingerprint)
                unique_articles.append(article)
        
        return unique_articles
    
    def generate_summary(self, article: Dict) -> str:
        """Generate a 2-3 sentence summary of the article"""
        title = article.get('title', '')
        text = article.get('text', '')
        category = article.get('category', 'global')
        
        # Extract key information
        keywords = self._extract_keywords(f"{title} {text}")
        
        # Simple summary generation
        summary_parts = []
        
        # What happened
        if any(word in title.lower() for word in ['funding', 'raise', 'investment']):
            summary_parts.append("A funding round was announced")
        elif any(word in title.lower() for word in ['acquire', 'acquisition', 'merger']):
            summary_parts.append("An acquisition or merger was announced")
        elif any(word in title.lower() for word in ['layoff', 'firing', 'job cuts']):
            summary_parts.append("Layoffs or job cuts were announced")
        elif any(word in title.lower() for word in ['launch', 'release', 'announce']):
            summary_parts.append("A new product or service was launched")
        else:
            summary_parts.append("A significant development was reported")
        
        # Why it matters
        if category == 'india':
            summary_parts.append("This development has implications for the Indian startup ecosystem")
        else:
            summary_parts.append("This development has global implications for the tech industry")
        
        # Additional context
        if len(summary_parts) < 3:
            summary_parts.append("The story has attracted significant attention from the tech community")
        
        return " ".join(summary_parts)
    
    def calculate_impact_score(self, article: Dict) -> float:
        """Calculate impact score based on content analysis"""
        title = article.get('title', '').lower()
        text = article.get('text', '').lower()
        combined_text = f"{title} {text}"
        
        impact_score = 0.0
        
        for criterion, config in IMPACT_CRITERIA.items():
            keywords = config['keywords']
            score = config['score']
            
            if any(keyword in combined_text for keyword in keywords):
                impact_score += score
        
        return min(impact_score, 100.0)  # Cap at 100
    
    def calculate_virality_score(self, articles: List[Dict]) -> Dict[str, float]:
        """Calculate virality scores for all articles"""
        if not articles:
            return {}
        
        # Extract engagement metrics
        engagement_data = []
        for article in articles:
            # Combine Reddit scores and other engagement metrics
            reddit_score = article.get('reddit_score', 0)
            reddit_comments = article.get('reddit_comments', 0)
            
            # Simple engagement calculation
            engagement = reddit_score + (reddit_comments * 0.1)
            engagement_data.append(engagement)
        
        # Normalize to 0-100 scale
        if engagement_data:
            max_engagement = max(engagement_data) if engagement_data else 1
            virality_scores = {}
            
            for i, article in enumerate(articles):
                normalized_score = (engagement_data[i] / max_engagement) * 100
                virality_scores[article.get('url', '')] = normalized_score
        else:
            virality_scores = {article.get('url', ''): 0 for article in articles}
        
        return virality_scores
    
    def calculate_controversy_score(self, articles: List[Dict]) -> Dict[str, float]:
        """Calculate controversy scores based on sentiment divergence"""
        # For now, use a simple heuristic based on keywords
        controversy_scores = {}
        
        for article in articles:
            title = article.get('title', '').lower()
            text = article.get('text', '').lower()
            combined_text = f"{title} {text}"
            
            # Controversy indicators
            controversy_keywords = [
                'controversy', 'debate', 'dispute', 'conflict', 'criticism',
                'backlash', 'outrage', 'protest', 'boycott', 'lawsuit'
            ]
            
            controversy_count = sum(1 for keyword in controversy_keywords 
                                 if keyword in combined_text)
            
            # Normalize to 0-100
            controversy_score = min(controversy_count * 20, 100)
            controversy_scores[article.get('url', '')] = controversy_score
        
        return controversy_scores
    
    def rank_articles(self, articles: List[Dict]) -> List[Dict]:
        """Rank articles based on virality, impact, and controversy"""
        if not articles:
            return []
        
        # Calculate individual scores
        virality_scores = self.calculate_virality_score(articles)
        controversy_scores = self.calculate_controversy_score(articles)
        
        # Process each article
        for article in articles:
            url = article.get('url', '')
            
            # Calculate impact score
            impact_score = self.calculate_impact_score(article)
            
            # Get other scores
            virality_score = virality_scores.get(url, 0)
            controversy_score = controversy_scores.get(url, 0)
            
            # Calculate final score
            final_score = (
                RANKING_WEIGHTS['virality'] * virality_score +
                RANKING_WEIGHTS['impact'] * impact_score +
                RANKING_WEIGHTS['controversy'] * controversy_score
            )
            
            # Store scores
            article['scores'] = {
                'virality': virality_score,
                'impact': impact_score,
                'controversy': controversy_score,
                'final': final_score
            }
            
            # Generate summary
            article['summary'] = self.generate_summary(article)
            
            # Add tags
            article['tags'] = self._extract_tags(article)
        
        # Sort by final score (highest first)
        ranked_articles = sorted(articles, key=lambda x: x['scores']['final'], reverse=True)
        
        return ranked_articles
    
    def _extract_tags(self, article: Dict) -> List[str]:
        """Extract relevant tags from article"""
        tags = []
        title = article.get('title', '').lower()
        text = article.get('text', '').lower()
        combined_text = f"{title} {text}"
        
        # Category tag
        category = article.get('category', 'global')
        tags.append(category)
        
        # Content-based tags
        if any(word in combined_text for word in ['funding', 'raise', 'investment']):
            tags.append('funding')
        if any(word in combined_text for word in ['acquire', 'acquisition', 'merger']):
            tags.append('m&a')
        if any(word in combined_text for word in ['layoff', 'firing', 'job cuts']):
            tags.append('layoffs')
        if any(word in combined_text for word in ['regulation', 'policy', 'government']):
            tags.append('policy')
        if any(word in combined_text for word in ['launch', 'release', 'announce']):
            tags.append('product')
        if any(word in combined_text for word in ['hack', 'breach', 'security']):
            tags.append('security')
        
        return list(set(tags))  # Remove duplicates
    
    def process_articles(self, articles: List[Dict]) -> List[Dict]:
        """Complete processing pipeline"""
        logger.info(f"Processing {len(articles)} articles")
        
        # Step 1: Deduplicate
        unique_articles = self.deduplicate_articles(articles)
        logger.info(f"After deduplication: {len(unique_articles)} articles")
        
        # Step 2: Rank
        ranked_articles = self.rank_articles(unique_articles)
        logger.info(f"Ranking completed for {len(ranked_articles)} articles")
        
        return ranked_articles 