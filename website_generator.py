import os
from datetime import datetime, date
from typing import List, Dict, Optional
import logging
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template

from config import TEMPLATES_DIR, STATIC_DIR, SITE_CONFIG
from data_manager import DataManager

logger = logging.getLogger(__name__)

class WebsiteGenerator:
    """Generate static website pages"""
    
    def __init__(self):
        self.data_manager = DataManager()
        self.templates_dir = Path(TEMPLATES_DIR)
        self.static_dir = Path(STATIC_DIR)
        
        # Ensure directories exist
        self.templates_dir.mkdir(exist_ok=True)
        self.static_dir.mkdir(exist_ok=True)
        
        # Set up Jinja2 environment
        self.env = Environment(loader=FileSystemLoader(str(self.templates_dir)))
        
        # Create default templates if they don't exist
        self._create_default_templates()
    
    def _create_default_templates(self):
        """Create default HTML templates"""
        
        # Base template
        base_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}{{ site_title }}{% endblock %}</title>
    <meta name="description" content="{{ site_description }}">
    <link rel="stylesheet" href="static/styles.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <header class="header">
        <div class="container">
            <h1 class="logo">{{ site_title }}</h1>
            <nav class="nav">
                <a href="index.html" class="nav-link">Today</a>
                <a href="archive.html" class="nav-link">Archive</a>
            </nav>
        </div>
    </header>
    
    <main class="main">
        <div class="container">
            {% block content %}{% endblock %}
        </div>
    </main>
    
    <footer class="footer">
        <div class="container">
            <p>&copy; {{ current_year }} {{ site_title }}. Updated daily with ranked startup and tech news.</p>
        </div>
    </footer>
</body>
</html>"""
        
        # Today page template
        today_template = """{% extends "base.html" %}

{% block title %}{{ site_title }} — {{ date }}{% endblock %}

{% block content %}
<div class="page-header">
    <h2>Top Startup & Tech News — {{ date }}</h2>
    <p class="subtitle">{{ total_articles }} stories ranked by impact, virality, and controversy</p>
</div>

{% if articles %}
<div class="articles-list">
    {% for article in articles %}
    <article class="article-card">
        <div class="article-header">
            <span class="rank">#{{ loop.index }}</span>
            <h3 class="article-title">
                <a href="{{ article.url }}" target="_blank" rel="noopener">{{ article.title }}</a>
            </h3>
        </div>
        
        <div class="article-summary">
            {{ article.summary }}
        </div>
        
        <div class="article-meta">
            <div class="sources">
                <strong>Sources:</strong>
                {% for source in article.sources %}
                <a href="{{ article.url }}" target="_blank" rel="noopener">{{ source }}</a>{% if not loop.last %}, {% endif %}
                {% endfor %}
            </div>
            
            {% if article.reactions %}
            <div class="reactions">
                <strong>🔥 Viral Reactions & Public Opinions:</strong>
                {% for reaction in article.reactions %}
                <div class="reaction">
                    <div class="reaction-header">
                        <span class="platform platform-{{ reaction.platform }}">{{ reaction.platform|title }}</span>
                        {% if reaction.engagement %}
                            {% if reaction.platform == 'twitter' %}
                                <span class="engagement">
                                    ❤️ {{ reaction.engagement.likes|default(0) }} 
                                    🔄 {{ reaction.engagement.retweets|default(0) }}
                                    💬 {{ reaction.engagement.replies|default(0) }}
                                </span>
                            {% elif reaction.platform == 'reddit' %}
                                <span class="engagement">
                                    ⬆️ {{ reaction.engagement.upvotes|default(0) }}
                                    💬 {{ reaction.engagement.comments|default(0) }}
                                </span>
                            {% endif %}
                        {% endif %}
                    </div>
                    <blockquote class="reaction-text">{{ reaction.text }}</blockquote>
                    <div class="reaction-meta">
                        <span class="author">
                            {% if reaction.platform == 'twitter' %}
                                🐦 @{{ reaction.author }}
                            {% elif reaction.platform == 'reddit' %}
                                📱 {{ reaction.author }}
                            {% else %}
                                👤 {{ reaction.author }}
                            {% endif %}
                        </span>
                        {% if reaction.permalink %}
                        <a href="{{ reaction.permalink }}" target="_blank" rel="noopener" class="view-link">🔗 View Original</a>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>
            {% endif %}
        </div>
        
        <div class="article-scores">
            <div class="score-badges">
                <span class="badge category-{{ article.category }}">{{ article.category|title }}</span>
                <span class="badge score-final">{{ "%.1f"|format(article.scores.final) }}</span>
                {% if article.scores.india_boost and article.scores.india_boost > 0 %}
                <span class="badge score-india-boost">🇮🇳 +{{ article.scores.india_boost }}</span>
                {% endif %}
                <span class="badge score-virality">{{ "%.1f"|format(article.scores.virality) }}</span>
                <span class="badge score-impact">{{ "%.1f"|format(article.scores.impact) }}</span>
                <span class="badge score-controversy">{{ "%.1f"|format(article.scores.controversy) }}</span>
            </div>
            
            <div class="tags">
                {% for tag in article.tags %}
                <span class="tag">{{ tag }}</span>
                {% endfor %}
            </div>
        </div>
    </article>
    {% endfor %}
</div>
{% else %}
<div class="no-articles">
    <p>No articles available for today. Check back later!</p>
</div>
{% endif %}
{% endblock %}"""
        
        # Archive page template
        archive_template = """{% extends "base.html" %}

{% block title %}{{ site_title }} — Archive{% endblock %}

{% block content %}
<div class="page-header">
    <h2>News Archive</h2>
    <p class="subtitle">Browse past editions and search through historical data</p>
</div>

<div class="archive-controls">
    <form class="search-form" method="GET">
        <input type="text" name="q" placeholder="Search articles..." value="{{ search_query }}">
        <select name="category">
            <option value="">All Categories</option>
            <option value="india" {% if category_filter == 'india' %}selected{% endif %}>India</option>
            <option value="global" {% if category_filter == 'global' %}selected{% endif %}>Global</option>
        </select>
        <input type="number" name="min_score" placeholder="Min Score" value="{{ min_score }}" min="0" max="100" step="0.1">
        <button type="submit">Search</button>
    </form>
</div>

{% if editions %}
<div class="editions-list">
    {% for edition in editions %}
    <div class="edition-card">
        <div class="edition-header">
            <h3><a href="edition_{{ edition.date }}.html">{{ edition.date }}</a></h3>
            <span class="article-count">{{ edition.total_articles }} articles</span>
        </div>
        
        {% if edition.top_stories %}
        <div class="top-stories">
            <strong>Top stories:</strong>
            <ul>
                {% for story in edition.top_stories %}
                <li>
                    <span class="rank">#{{ story.rank }}</span>
                    <a href="{{ story.url }}" target="_blank" rel="noopener">{{ story.title }}</a>
                    <span class="score">{{ "%.1f"|format(story.score) }}</span>
                </li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}
    </div>
    {% endfor %}
</div>
{% else %}
<div class="no-editions">
    <p>No archived editions found.</p>
</div>
{% endif %}

{% if search_results %}
<div class="search-results">
    <h3>Search Results ({{ search_results|length }} found)</h3>
    {% for result in search_results %}
    <div class="search-result">
        <div class="result-date">{{ result.date }}</div>
        <h4><a href="{{ result.article.url }}" target="_blank" rel="noopener">{{ result.article.title }}</a></h4>
        <p>{{ result.article.summary }}</p>
        <div class="result-meta">
            <span class="category">{{ result.article.category }}</span>
            <span class="score">{{ "%.1f"|format(result.article.scores.final) }}</span>
        </div>
    </div>
    {% endfor %}
</div>
{% endif %}
{% endblock %}"""
        
        # Save templates
        templates = {
            'base.html': base_template,
            'today.html': today_template,
            'archive.html': archive_template
        }
        
        for filename, content in templates.items():
            template_path = self.templates_dir / filename
            if not template_path.exists():
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(content)
    
    def _create_css_styles(self):
        """Create CSS styles for the website"""
        css_content = """/* Reset and base styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f8f9fa;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* Header */
.header {
    background: #fff;
    border-bottom: 1px solid #e1e5e9;
    padding: 1rem 0;
    position: sticky;
    top: 0;
    z-index: 100;
}

.header .container {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo {
    font-size: 1.5rem;
    font-weight: 700;
    color: #1a73e8;
    text-decoration: none;
}

.nav {
    display: flex;
    gap: 2rem;
}

.nav-link {
    text-decoration: none;
    color: #666;
    font-weight: 500;
    transition: color 0.2s;
}

.nav-link:hover {
    color: #1a73e8;
}

/* Main content */
.main {
    padding: 2rem 0;
}

.page-header {
    margin-bottom: 2rem;
    text-align: center;
}

.page-header h2 {
    font-size: 2rem;
    font-weight: 700;
    color: #1a1a1a;
    margin-bottom: 0.5rem;
}

.subtitle {
    color: #666;
    font-size: 1.1rem;
}

/* Article cards */
.articles-list {
    display: grid;
    gap: 2rem;
}

.article-card {
    background: #fff;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s, box-shadow 0.2s;
}

.article-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.article-header {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 1rem;
}

.rank {
    background: #1a73e8;
    color: #fff;
    font-weight: 700;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.875rem;
    min-width: 2rem;
    text-align: center;
}

.article-title {
    font-size: 1.25rem;
    font-weight: 600;
    line-height: 1.4;
    flex: 1;
}

.article-title a {
    color: #1a1a1a;
    text-decoration: none;
    transition: color 0.2s;
}

.article-title a:hover {
    color: #1a73e8;
}

.article-summary {
    color: #555;
    margin-bottom: 1.5rem;
    line-height: 1.6;
}

.article-meta {
    margin-bottom: 1.5rem;
}

.sources {
    margin-bottom: 1rem;
}

.sources a {
    color: #1a73e8;
    text-decoration: none;
}

.sources a:hover {
    text-decoration: underline;
}

.reactions {
    border-top: 1px solid #e1e5e9;
    padding-top: 1rem;
}

.reaction {
    background: #f8f9fa;
    padding: 1.5rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    border-left: 4px solid #1a73e8;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.reaction-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.platform {
    font-weight: 600;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.75rem;
    text-transform: uppercase;
}

.platform-twitter {
    background: #1da1f2;
    color: white;
}

.platform-reddit {
    background: #ff4500;
    color: white;
}

.engagement {
    font-size: 0.875rem;
    color: #666;
    font-weight: 500;
}

.reaction-text {
    font-style: italic;
    color: #555;
    margin: 0.5rem 0;
    padding-left: 1rem;
    border-left: 3px solid #1a73e8;
}

.reaction-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.875rem;
    color: #666;
}

.reaction-meta a {
    color: #1a73e8;
    text-decoration: none;
}

/* Score badges */
.article-scores {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
}

.score-badges {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
}

.badge {
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
}

.badge.category-india {
    background: #e8f5e8;
    color: #2e7d32;
}

.badge.category-global {
    background: #e3f2fd;
    color: #1565c0;
}

.badge.score-final {
    background: #1a73e8;
    color: #fff;
}

.badge.score-virality {
    background: #fff3e0;
    color: #f57c00;
}

.badge.score-impact {
    background: #f3e5f5;
    color: #7b1fa2;
}

.badge.score-controversy {
    background: #ffebee;
    color: #c62828;
}

.badge.score-india-boost {
    background: #e8f5e8;
    color: #2e7d32;
    border: 2px solid #4caf50;
}

.tags {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
}

.tag {
    background: #f1f3f4;
    color: #5f6368;
    padding: 0.25rem 0.75rem;
    border-radius: 16px;
    font-size: 0.75rem;
    font-weight: 500;
}

/* Archive controls */
.archive-controls {
    background: #fff;
    padding: 1.5rem;
    border-radius: 12px;
    margin-bottom: 2rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.search-form {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    align-items: center;
}

.search-form input,
.search-form select {
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 1rem;
}

.search-form button {
    background: #1a73e8;
    color: #fff;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: background-color 0.2s;
}

.search-form button:hover {
    background: #1557b0;
}

/* Edition cards */
.editions-list {
    display: grid;
    gap: 1.5rem;
}

.edition-card {
    background: #fff;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.edition-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.edition-header h3 {
    font-size: 1.25rem;
    font-weight: 600;
}

.edition-header a {
    color: #1a73e8;
    text-decoration: none;
}

.article-count {
    background: #f1f3f4;
    color: #5f6368;
    padding: 0.25rem 0.75rem;
    border-radius: 16px;
    font-size: 0.875rem;
    font-weight: 500;
}

.top-stories ul {
    list-style: none;
    margin-top: 0.5rem;
}

.top-stories li {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
}

.top-stories a {
    color: #1a73e8;
    text-decoration: none;
    flex: 1;
}

.top-stories .score {
    background: #e8f5e8;
    color: #2e7d32;
    padding: 0.125rem 0.5rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
}

/* Search results */
.search-results {
    margin-top: 2rem;
}

.search-result {
    background: #fff;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.result-date {
    color: #666;
    font-size: 0.875rem;
    margin-bottom: 0.5rem;
}

.search-result h4 {
    margin-bottom: 0.5rem;
}

.search-result h4 a {
    color: #1a1a1a;
    text-decoration: none;
}

.search-result h4 a:hover {
    color: #1a73e8;
}

.result-meta {
    display: flex;
    gap: 1rem;
    margin-top: 0.5rem;
}

.result-meta .category,
.result-meta .score {
    font-size: 0.875rem;
    padding: 0.25rem 0.75rem;
    border-radius: 16px;
}

.result-meta .category {
    background: #e3f2fd;
    color: #1565c0;
}

.result-meta .score {
    background: #e8f5e8;
    color: #2e7d32;
}

/* Footer */
.footer {
    background: #fff;
    border-top: 1px solid #e1e5e9;
    padding: 2rem 0;
    margin-top: 4rem;
    text-align: center;
    color: #666;
}

/* Responsive design */
@media (max-width: 768px) {
    .container {
        padding: 0 15px;
    }
    
    .header .container {
        flex-direction: column;
        gap: 1rem;
    }
    
    .nav {
        gap: 1rem;
    }
    
    .page-header h2 {
        font-size: 1.5rem;
    }
    
    .article-header {
        flex-direction: column;
        gap: 0.5rem;
    }
    
    .article-scores {
        flex-direction: column;
        align-items: flex-start;
    }
    
    .search-form {
        flex-direction: column;
        align-items: stretch;
    }
    
    .edition-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.5rem;
    }
}"""
        
        css_path = self.static_dir / 'styles.css'
        if not css_path.exists():
            with open(css_path, 'w', encoding='utf-8') as f:
                f.write(css_content)
    
    def generate_today_page(self, date_obj: Optional[date] = None) -> bool:
        """Generate today's page"""
        try:
            edition_data = self.data_manager.load_daily_edition(date_obj)
            if not edition_data:
                logger.warning(f"No edition data found for {date_obj or 'today'}")
                return False
            
            template = self.env.get_template('today.html')
            
            context = {
                'site_title': SITE_CONFIG['title'],
                'site_description': SITE_CONFIG['description'],
                'current_year': datetime.now().year,
                'date': edition_data['date'],
                'total_articles': edition_data['total_articles'],
                'articles': edition_data['articles']
            }
            
            html_content = template.render(context)
            
            # Save to index.html
            output_path = Path('index.html')
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Generated today's page: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating today's page: {e}")
            return False
    
    def generate_archive_page(self, search_query: str = '', category_filter: str = '', 
                            min_score: float = 0) -> bool:
        """Generate archive page"""
        try:
            # Get available editions
            available_dates = self.data_manager.get_available_dates()
            editions = []
            
            for date_str in available_dates[:20]:  # Limit to last 20 editions
                summary = self.data_manager.get_edition_summary(date_str)
                if summary:
                    editions.append(summary)
            
            # Get search results if query provided
            search_results = []
            if search_query:
                search_results = self.data_manager.search_editions(
                    search_query, category_filter=category_filter, min_score=min_score
                )
            
            template = self.env.get_template('archive.html')
            
            context = {
                'site_title': SITE_CONFIG['title'],
                'site_description': SITE_CONFIG['description'],
                'current_year': datetime.now().year,
                'editions': editions,
                'search_query': search_query,
                'category_filter': category_filter,
                'min_score': min_score,
                'search_results': search_results
            }
            
            html_content = template.render(context)
            
            # Save to archive.html
            output_path = Path('archive.html')
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Generated archive page: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating archive page: {e}")
            return False
    
    def generate_edition_page(self, date_str: str) -> bool:
        """Generate a specific edition page"""
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            edition_data = self.data_manager.load_daily_edition(date_obj)
            
            if not edition_data:
                # Try archive
                edition_path = self.data_manager.archive_dir / f"edition_{date_str}.json"
                if edition_path.exists():
                    with open(edition_path, 'r', encoding='utf-8') as f:
                        import json
                        edition_data = json.load(f)
                else:
                    logger.warning(f"No edition data found for {date_str}")
                    return False
            
            template = self.env.get_template('today.html')
            
            context = {
                'site_title': SITE_CONFIG['title'],
                'site_description': SITE_CONFIG['description'],
                'current_year': datetime.now().year,
                'date': edition_data['date'],
                'total_articles': edition_data['total_articles'],
                'articles': edition_data['articles']
            }
            
            html_content = template.render(context)
            
            # Save to edition-specific file
            output_path = Path(f'edition_{date_str}.html')
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Generated edition page: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating edition page for {date_str}: {e}")
            return False
    
    def generate_stats_page(self) -> bool:
        """Generate statistics dashboard page"""
        try:
            # Get statistics
            stats = self.data_manager.get_statistics()
            
            # Get recent editions for activity feed
            available_dates = self.data_manager.get_available_dates()
            recent_editions = []
            
            for date_str in available_dates[:5]:  # Last 5 editions
                summary = self.data_manager.get_edition_summary(date_str)
                if summary:
                    recent_editions.append(summary)
            
            template = self.env.get_template('stats.html')
            
            context = {
                'site_title': SITE_CONFIG['title'],
                'site_description': SITE_CONFIG['description'],
                'current_year': datetime.now().year,
                'stats': stats,
                'recent_editions': recent_editions
            }
            
            html_content = template.render(context)
            
            # Save to stats.html
            output_path = Path('stats.html')
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Generated stats page: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating stats page: {e}")
            return False
    
    def generate_all_pages(self) -> bool:
        """Generate all website pages"""
        try:
            # Create CSS styles
            self._create_css_styles()
            
            # Generate today's page
            today_success = self.generate_today_page()
            
            # Generate archive page
            archive_success = self.generate_archive_page()
            
            # Generate stats page
            stats_success = self.generate_stats_page()
            
            # Generate individual edition pages for recent dates
            available_dates = self.data_manager.get_available_dates()
            edition_success = True
            
            for date_str in available_dates[:10]:  # Last 10 editions
                if not self.generate_edition_page(date_str):
                    edition_success = False
            
            return today_success and archive_success and stats_success and edition_success
            
        except Exception as e:
            logger.error(f"Error generating website pages: {e}")
            return False 