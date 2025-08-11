#!/usr/bin/env python3
"""
Main pipeline for daily news aggregation
"""

import argparse
import logging
import sys
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
import time

from scrapers import scrape_all_sources, fetch_article_content
from processor import NewsProcessor
from social_reactions import SocialReactionsScraper
from data_manager import DataManager
from website_generator import WebsiteGenerator
from config import SITE_CONFIG

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('news_pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class NewsPipeline:
    """Main pipeline for news aggregation"""
    
    def __init__(self):
        self.processor = NewsProcessor()
        self.social_scraper = SocialReactionsScraper()
        self.data_manager = DataManager()
        self.website_generator = WebsiteGenerator()
    
    def run_daily_pipeline(self, target_date: Optional[date] = None) -> bool:
        """Run the complete daily pipeline"""
        if target_date is None:
            target_date = date.today()
        
        logger.info(f"Starting daily pipeline for {target_date}")
        
        try:
            # Step 1: Scrape articles from all sources
            logger.info("Step 1: Scraping articles from sources...")
            articles = scrape_all_sources()
            logger.info(f"Scraped {len(articles)} articles from all sources")
            
            if not articles:
                logger.warning("No articles found. Pipeline cannot continue.")
                return False
            
            # Step 2: Fetch article content for deduplication and processing
            logger.info("Step 2: Fetching article content...")
            successful_fetches = 0
            for i, article in enumerate(articles):
                if i % 10 == 0:
                    logger.info(f"Processing article {i+1}/{len(articles)}")
                
                url = article.get('url', '')
                source_id = article.get('source_id', '')
                
                if url and source_id:
                    try:
                        content = fetch_article_content(url, source_id)
                        if content:
                            article.update(content)
                            successful_fetches += 1
                    except Exception as e:
                        logger.warning(f"Failed to fetch content for {url}: {e}")
                        # Continue with other articles
                
                # Rate limiting
                time.sleep(0.5)
            
            logger.info(f"Successfully fetched content for {successful_fetches}/{len(articles)} articles")
            
            # Step 3: Process and rank articles
            logger.info("Step 3: Processing and ranking articles...")
            processed_articles = self.processor.process_articles(articles)
            logger.info(f"Processed and ranked {len(processed_articles)} articles")
            
            if not processed_articles:
                logger.warning("No articles processed successfully. Pipeline cannot continue.")
                return False
            
            # Step 4: Scrape enhanced social reactions for top 15 stories
            logger.info("Step 4: Scraping enhanced social reactions for top stories...")
            try:
                # Get more reactions for top stories (up to 5 per story)
                reactions = {}
                for i, article in enumerate(processed_articles):
                    if i < 15:  # Only top 15 stories get enhanced reactions
                        logger.info(f"Getting enhanced reactions for story {i+1}: {article['title'][:50]}...")
                        article_reactions = self.social_scraper.get_top_reactions(article, max_reactions=5)
                        reactions[article.get('url', '')] = article_reactions
                        logger.info(f"Found {len(article_reactions)} reactions for: {article['title'][:50]}...")
                    else:
                        # Basic reactions for remaining stories
                        article_reactions = self.social_scraper.get_top_reactions(article, max_reactions=2)
                        reactions[article.get('url', '')] = article_reactions
                
                logger.info(f"Found social reactions for {len(reactions)} articles")
            except Exception as e:
                logger.error(f"Social reactions scraping failed: {e}")
                reactions = {}  # Continue without social reactions
            
            # Add reactions to articles
            for article in processed_articles:
                url = article.get('url', '')
                if url in reactions:
                    article['reactions'] = reactions[url]
                    reaction_count = len(reactions[url])
                    logger.info(f"Added {reaction_count} reactions for: {article['title'][:50]}...")
                else:
                    article['reactions'] = []
                    logger.info(f"No social reactions found for: {article['title'][:50]}...")
            
            # Step 5: Save daily edition
            logger.info("Step 5: Saving daily edition...")
            try:
                success = self.data_manager.save_daily_edition(processed_articles, target_date)
                if not success:
                    logger.error("Failed to save daily edition")
                    return False
                logger.info("Daily edition saved successfully")
            except Exception as e:
                logger.error(f"Failed to save daily edition: {e}")
                return False
            
            # Step 6: Generate website pages
            logger.info("Step 6: Generating website pages...")
            try:
                success = self.website_generator.generate_all_pages()
                if not success:
                    logger.error("Failed to generate website pages")
                    return False
                logger.info("Website pages generated successfully")
            except Exception as e:
                logger.error(f"Website generation failed: {e}")
                return False
            
            logger.info(f"Daily pipeline completed successfully for {target_date}")
            return True
            
        except Exception as e:
            logger.error(f"Pipeline failed with error: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False
    
    def run_backfill(self, days: int = 7) -> bool:
        """Run backfill for the last N days"""
        logger.info(f"Starting backfill for last {days} days")
        
        success_count = 0
        for i in range(days):
            target_date = date.today() - timedelta(days=i+1)
            logger.info(f"Backfilling for {target_date}")
            
            if self.run_daily_pipeline(target_date):
                success_count += 1
            else:
                logger.warning(f"Backfill failed for {target_date}")
        
        logger.info(f"Backfill completed: {success_count}/{days} days successful")
        return success_count == days
    
    def generate_website_only(self) -> bool:
        """Generate website pages from existing data"""
        logger.info("Generating website pages from existing data...")
        return self.website_generator.generate_all_pages()
    
    def get_statistics(self) -> Dict:
        """Get pipeline statistics"""
        return self.data_manager.get_statistics()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='News aggregation pipeline')
    parser.add_argument('--mode', choices=['daily', 'backfill', 'website-only'], 
                       default='daily', help='Pipeline mode')
    parser.add_argument('--date', type=str, help='Target date (YYYY-MM-DD) for daily mode')
    parser.add_argument('--days', type=int, default=7, help='Number of days for backfill')
    parser.add_argument('--stats', action='store_true', help='Show statistics only')
    
    args = parser.parse_args()
    
    pipeline = NewsPipeline()
    
    if args.stats:
        stats = pipeline.get_statistics()
        print("\n=== Pipeline Statistics ===")
        print(f"Total editions: {stats['total_editions']}")
        print(f"Total articles: {stats['total_articles']}")
        if stats['date_range']:
            print(f"Date range: {stats['date_range'][0]} to {stats['date_range'][1]}")
        
        if stats['top_categories']:
            print("\nTop categories:")
            for category, count in stats['top_categories'].items():
                print(f"  {category}: {count}")
        
        if stats['top_sources']:
            print("\nTop sources:")
            for source, count in list(stats['top_sources'].items())[:5]:
                print(f"  {source}: {count}")
        return
    
    if args.mode == 'daily':
        target_date = None
        if args.date:
            try:
                target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
            except ValueError:
                logger.error(f"Invalid date format: {args.date}. Use YYYY-MM-DD")
                return 1
        
        success = pipeline.run_daily_pipeline(target_date)
        return 0 if success else 1
    
    elif args.mode == 'backfill':
        success = pipeline.run_backfill(args.days)
        return 0 if success else 1
    
    elif args.mode == 'website-only':
        success = pipeline.generate_website_only()
        return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main()) 