import os
from datetime import datetime, timedelta

# Sources configuration
SOURCES = {
    # India sources
    'yourstory': {
        'name': 'YourStory',
        'url': 'https://yourstory.com',
        'rss': 'https://yourstory.com/feed',
        'category': 'india'
    },
    'inc42': {
        'name': 'Inc42',
        'url': 'https://inc42.com',
        'rss': 'https://inc42.com/feed',
        'category': 'india'
    },
    'entrackr': {
        'name': 'Entrackr',
        'url': 'https://entrackr.com',
        'rss': 'https://entrackr.com/feed',
        'category': 'india'
    },
    'reddit_indianstartups': {
        'name': 'r/indianstartups',
        'url': 'https://reddit.com/r/indianstartups',
        'category': 'india'
    },
    'livemint': {
        'name': 'Livemint',
        'url': 'https://www.livemint.com',
        'rss': 'https://www.livemint.com/rss/technology',
        'category': 'india'
    },
    'moneycontrol': {
        'name': 'Moneycontrol',
        'url': 'https://www.moneycontrol.com',
        'rss': 'https://www.moneycontrol.com/rss/technology.xml',
        'category': 'india'
    },
    
    # Global sources
    'techcrunch': {
        'name': 'TechCrunch',
        'url': 'https://techcrunch.com',
        'rss': 'https://techcrunch.com/feed',
        'category': 'global'
    },
    'theinformation': {
        'name': 'The Information',
        'url': 'https://theinformation.com',
        'category': 'global'
    },
    'wired': {
        'name': 'Wired',
        'url': 'https://wired.com',
        'rss': 'https://wired.com/feed/rss',
        'category': 'global'
    },
    'crunchbase': {
        'name': 'Crunchbase News',
        'url': 'https://news.crunchbase.com',
        'rss': 'https://news.crunchbase.com/feed',
        'category': 'global'
    },
    'theverge': {
        'name': 'The Verge',
        'url': 'https://theverge.com',
        'rss': 'https://theverge.com/rss/index.xml',
        'category': 'global'
    },
    'reddit_technology': {
        'name': 'r/technology',
        'url': 'https://reddit.com/r/technology',
        'category': 'global'
    },
    'reddit_startups': {
        'name': 'r/startups',
        'url': 'https://reddit.com/r/startups',
        'category': 'global'
    },
    'reuters_tech': {
        'name': 'Reuters Technology',
        'url': 'https://www.reuters.com',
        'rss': 'https://www.reuters.com/arc/outboundfeeds/rss/?outputType=xml',
        'category': 'global'
    }
}

# Social platforms for reactions
SOCIAL_PLATFORMS = {
    'twitter': {
        'name': 'X (Twitter)',
        'search_url': 'https://twitter.com/search',
        'base_url': 'https://twitter.com'
    },
    'reddit': {
        'name': 'Reddit',
        'subreddits': ['technology', 'startups', 'indianstartups', 'programming', 'webdev'],
        'base_url': 'https://reddit.com'
    },
    'hackernews': {
        'name': 'Hacker News',
        'search_url': 'https://hn.algolia.com',
        'base_url': 'https://news.ycombinator.com'
    }
}

# Scraping settings
SCRAPING_CONFIG = {
    'user_agents': [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
    ],
    'request_delay': 3.0,  # Increased delay to avoid rate limiting
    'timeout': 45,  # Increased timeout for slow sources
    'max_retries': 5,  # More retries for reliability
    'time_window_hours': 48,  # Look back 48 hours for stories
    'max_articles_per_source': 15,  # Reduced to avoid overwhelming sources
    'batch_size': 5,  # Process sources in smaller batches
    'batch_delay': 10  # Wait between batches
}

# Ranking weights
RANKING_WEIGHTS = {
    'virality': 0.5,
    'impact': 0.35,
    'controversy': 0.15
}

# Impact scoring criteria
IMPACT_CRITERIA = {
    'funding_round': {
        'keywords': ['funding', 'raise', 'investment', 'series', 'venture', 'capital', 'round'],
        'score': 20
    },
    'acquisition': {
        'keywords': ['acquire', 'acquisition', 'merger', 'buyout', 'takeover', 'purchase'],
        'score': 25
    },
    'layoffs': {
        'keywords': ['layoff', 'firing', 'job cuts', 'restructuring', 'downsizing', 'redundancy'],
        'score': 15
    },
    'policy': {
        'keywords': ['regulation', 'policy', 'government', 'legal', 'law', 'compliance'],
        'score': 20
    },
    'product_launch': {
        'keywords': ['launch', 'release', 'announce', 'new product', 'beta', 'preview'],
        'score': 10
    },
    'security': {
        'keywords': ['hack', 'breach', 'security', 'cyber', 'vulnerability', 'attack'],
        'score': 15
    },
    'india_macro': {
        'keywords': ['india', 'indian', 'delhi', 'mumbai', 'bangalore', 'hyderabad', 'chennai'],
        'score': 10
    },
    'ai_ml': {
        'keywords': ['ai', 'artificial intelligence', 'machine learning', 'ml', 'neural', 'gpt'],
        'score': 15
    },
    'crypto': {
        'keywords': ['crypto', 'bitcoin', 'blockchain', 'nft', 'defi', 'ethereum'],
        'score': 12
    },
    'ipo': {
        'keywords': ['ipo', 'initial public offering', 'public listing', 'stock market'],
        'score': 18
    }
}

# File paths
DATA_DIR = 'data'
ARCHIVE_DIR = os.path.join(DATA_DIR, 'archive')
TEMPLATES_DIR = 'templates'
STATIC_DIR = 'static'

# Website settings
SITE_CONFIG = {
    'title': 'Top Startup & Tech News',
    'description': 'Daily ranked startup and tech news from India and around the world',
    'min_stories_per_day': 10,
    'max_stories_per_day': 50,
    'enable_analytics': False,  # Set to True to add Google Analytics
    'enable_dark_mode': True,   # Enable dark mode toggle
    'enable_search': True,      # Enable search functionality
    'enable_filters': True,     # Enable category and score filters
    'enable_sharing': True      # Enable social sharing buttons
}

# Create directories if they don't exist
for directory in [DATA_DIR, ARCHIVE_DIR, TEMPLATES_DIR, STATIC_DIR]:
    os.makedirs(directory, exist_ok=True) 