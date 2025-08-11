import json
import os
from datetime import datetime, date
from typing import List, Dict, Optional
import logging
from pathlib import Path

from config import DATA_DIR, ARCHIVE_DIR

logger = logging.getLogger(__name__)

class DataManager:
    """Manage data persistence for daily news editions"""
    
    def __init__(self):
        self.data_dir = Path(DATA_DIR)
        self.archive_dir = Path(ARCHIVE_DIR)
        
        # Ensure directories exist
        self.data_dir.mkdir(exist_ok=True)
        self.archive_dir.mkdir(exist_ok=True)
    
    def _get_date_string(self, date_obj: Optional[date] = None) -> str:
        """Get date string in YYYY-MM-DD format"""
        if date_obj is None:
            date_obj = date.today()
        return date_obj.strftime('%Y-%m-%d')
    
    def _get_edition_path(self, date_obj: Optional[date] = None) -> Path:
        """Get path for daily edition file"""
        date_str = self._get_date_string(date_obj)
        return self.data_dir / f"edition_{date_str}.json"
    
    def _get_archive_path(self, date_obj: Optional[date] = None) -> Path:
        """Get path for archived edition file"""
        date_str = self._get_date_string(date_obj)
        return self.archive_dir / f"edition_{date_str}.json"
    
    def _convert_datetime_fields(self, obj):
        """Convert datetime objects to ISO format strings for JSON serialization"""
        if isinstance(obj, dict):
            converted = {}
            for key, value in obj.items():
                converted[key] = self._convert_datetime_fields(value)
            return converted
        elif isinstance(obj, list):
            return [self._convert_datetime_fields(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj

    def save_daily_edition(self, articles: List[Dict], date_obj: Optional[date] = None) -> bool:
        """Save daily edition data"""
        try:
            # Convert datetime objects to ISO format strings
            converted_articles = self._convert_datetime_fields(articles)
            
            edition_data = {
                'date': self._get_date_string(date_obj),
                'generated_at': datetime.now().isoformat(),
                'total_articles': len(articles),
                'articles': converted_articles
            }
            
            edition_path = self._get_edition_path(date_obj)
            
            with open(edition_path, 'w', encoding='utf-8') as f:
                json.dump(edition_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved daily edition for {self._get_date_string(date_obj)} with {len(articles)} articles")
            return True
            
        except Exception as e:
            logger.error(f"Error saving daily edition: {e}")
            return False
    
    def load_daily_edition(self, date_obj: Optional[date] = None) -> Optional[Dict]:
        """Load daily edition data"""
        try:
            edition_path = self._get_edition_path(date_obj)
            
            if not edition_path.exists():
                return None
            
            with open(edition_path, 'r', encoding='utf-8') as f:
                edition_data = json.load(f)
            
            logger.info(f"Loaded daily edition for {self._get_date_string(date_obj)}")
            return edition_data
            
        except Exception as e:
            logger.error(f"Error loading daily edition: {e}")
            return None
    
    def archive_daily_edition(self, date_obj: Optional[date] = None) -> bool:
        """Move daily edition to archive"""
        try:
            edition_path = self._get_edition_path(date_obj)
            archive_path = self._get_archive_path(date_obj)
            
            if not edition_path.exists():
                logger.warning(f"No edition file found for {self._get_date_string(date_obj)}")
                return False
            
            # Move to archive
            edition_path.rename(archive_path)
            
            logger.info(f"Archived daily edition for {self._get_date_string(date_obj)}")
            return True
            
        except Exception as e:
            logger.error(f"Error archiving daily edition: {e}")
            return False
    
    def get_available_dates(self) -> List[str]:
        """Get list of available edition dates"""
        dates = []
        
        # Check current data directory
        for file_path in self.data_dir.glob("edition_*.json"):
            date_str = file_path.stem.replace("edition_", "")
            dates.append(date_str)
        
        # Check archive directory
        for file_path in self.archive_dir.glob("edition_*.json"):
            date_str = file_path.stem.replace("edition_", "")
            dates.append(date_str)
        
        return sorted(dates, reverse=True)
    
    def get_edition_summary(self, date_str: str) -> Optional[Dict]:
        """Get summary information for a specific edition"""
        try:
            # Try current data directory first
            edition_path = self.data_dir / f"edition_{date_str}.json"
            
            if not edition_path.exists():
                # Try archive directory
                edition_path = self.archive_dir / f"edition_{date_str}.json"
            
            if not edition_path.exists():
                return None
            
            with open(edition_path, 'r', encoding='utf-8') as f:
                edition_data = json.load(f)
            
            # Create summary
            summary = {
                'date': edition_data['date'],
                'total_articles': edition_data['total_articles'],
                'generated_at': edition_data['generated_at'],
                'top_stories': []
            }
            
            # Get top 5 stories
            articles = edition_data.get('articles', [])
            for i, article in enumerate(articles[:5]):
                summary['top_stories'].append({
                    'rank': i + 1,
                    'title': article.get('title', ''),
                    'url': article.get('url', ''),
                    'score': article.get('scores', {}).get('final', 0),
                    'category': article.get('category', 'global')
                })
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting edition summary for {date_str}: {e}")
            return None
    
    def search_editions(self, query: str, date_range: Optional[tuple] = None, 
                       category_filter: Optional[str] = None, min_score: float = 0) -> List[Dict]:
        """Search through archived editions"""
        results = []
        available_dates = self.get_available_dates()
        
        for date_str in available_dates:
            # Apply date range filter
            if date_range:
                edition_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                if not (date_range[0] <= edition_date <= date_range[1]):
                    continue
            
            edition_data = self.load_daily_edition(datetime.strptime(date_str, '%Y-%m-%d').date())
            if not edition_data:
                continue
            
            # Search through articles
            for article in edition_data.get('articles', []):
                title = article.get('title', '').lower()
                summary = article.get('summary', '').lower()
                category = article.get('category', 'global')
                score = article.get('scores', {}).get('final', 0)
                
                # Apply filters
                if category_filter and category != category_filter:
                    continue
                
                if score < min_score:
                    continue
                
                # Search query
                if query.lower() in title or query.lower() in summary:
                    results.append({
                        'date': date_str,
                        'article': article
                    })
        
        return results
    
    def get_statistics(self) -> Dict:
        """Get overall statistics"""
        stats = {
            'total_editions': 0,
            'total_articles': 0,
            'date_range': None,
            'top_categories': {},
            'top_sources': {}
        }
        
        available_dates = self.get_available_dates()
        if not available_dates:
            return stats
        
        stats['total_editions'] = len(available_dates)
        stats['date_range'] = (available_dates[-1], available_dates[0])
        
        category_counts = {}
        source_counts = {}
        
        for date_str in available_dates:
            edition_data = self.load_daily_edition(datetime.strptime(date_str, '%Y-%m-%d').date())
            if not edition_data:
                continue
            
            for article in edition_data.get('articles', []):
                stats['total_articles'] += 1
                
                # Count categories
                category = article.get('category', 'global')
                category_counts[category] = category_counts.get(category, 0) + 1
                
                # Count sources
                source = article.get('source', 'Unknown')
                source_counts[source] = source_counts.get(source, 0) + 1
        
        stats['top_categories'] = dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5])
        stats['top_sources'] = dict(sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        
        return stats 