#!/usr/bin/env python3
"""
Offshore Wind Strategic Intelligence Platform - Data Scraper

This script scrapes data from high-priority sources for offshore wind intelligence
in the Northeast region, focusing on utility-relevant developments.
"""

import os
import json
import time
import requests
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OffshoreWindScraper:
    """Main scraper class for collecting offshore wind intelligence data."""
    
    def __init__(self):
        """Initialize the scraper with configuration and session."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Load configuration
        self.config = self._load_config()
        self.data_dir = os.getenv('DATA_DIR', './data')
        self.raw_data_file = os.getenv('RAW_DATA_FILE', 'raw_data.csv')
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize data storage
        self.collected_data = []
        
    def _load_config(self) -> Dict:
        """Load configuration from sources.json."""
        try:
            with open('config/sources.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("Configuration file config/sources.json not found")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            raise
    
    def _make_request(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """Make HTTP request with retry logic and rate limiting."""
        delay = int(os.getenv('REQUEST_DELAY', 2))
        timeout = int(os.getenv('TIMEOUT', 30))
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Requesting {url} (attempt {attempt + 1}/{max_retries})")
                response = self.session.get(url, timeout=timeout)
                response.raise_for_status()
                
                # Rate limiting
                time.sleep(delay)
                return response
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed for {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(delay * (attempt + 1))  # Exponential backoff
                else:
                    logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                    return None
    
    def _extract_article_data(self, article_element, source_name: str, source_url: str, selectors: Dict) -> Optional[Dict]:
        """Extract article data from a BeautifulSoup element."""
        try:
            # Extract title
            title_element = article_element.select_one(selectors.get('title', 'h2, h3, .title'))
            title = title_element.get_text(strip=True) if title_element else "No title"
            
            # Extract link
            link_element = article_element.select_one(selectors.get('link', 'a'))
            link = link_element.get('href') if link_element else ""
            
            # Make link absolute if it's relative
            if link and not link.startswith('http'):
                link = f"{source_url.rstrip('/')}/{link.lstrip('/')}"
            
            # Extract date
            date_element = article_element.select_one(selectors.get('date', '.date, .published'))
            date = date_element.get_text(strip=True) if date_element else ""
            
            # Extract content/summary
            content_element = article_element.select_one(selectors.get('content', '.content, .description'))
            content = content_element.get_text(strip=True) if content_element else ""
            
            # If no content found, try to get text from the article element itself
            if not content:
                content = article_element.get_text(strip=True)
            
            return {
                'source_name': source_name,
                'source_url': source_url,
                'title': title,
                'link': link,
                'date': date,
                'content': content,
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error extracting article data: {e}")
            return None
    
    def scrape_source(self, source_key: str, source_config: Dict) -> List[Dict]:
        """Scrape a single source and return list of articles."""
        articles = []
        source_name = source_config['name']
        source_url = source_config['url']
        selectors = source_config.get('selectors', {})
        
        logger.info(f"Scraping {source_name} from {source_url}")
        
        response = self._make_request(source_url)
        if not response:
            return articles
        
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find article elements
            article_selectors = selectors.get('articles', '.news-item, .article, .announcement')
            article_elements = soup.select(article_selectors)
            
            logger.info(f"Found {len(article_elements)} potential articles")
            
            for element in article_elements:
                article_data = self._extract_article_data(
                    element, source_name, source_url, selectors
                )
                if article_data:
                    articles.append(article_data)
            
            logger.info(f"Successfully extracted {len(articles)} articles from {source_name}")
            
        except Exception as e:
            logger.error(f"Error scraping {source_name}: {e}")
        
        return articles
    
    def scrape_all_sources(self) -> List[Dict]:
        """Scrape all configured sources."""
        all_articles = []
        
        # Start with high priority sources
        priority_order = ['high', 'medium', 'low']
        
        for priority in priority_order:
            for source_key, source_config in self.config['sources'].items():
                if source_config.get('priority', 'medium') == priority:
                    articles = self.scrape_source(source_key, source_config)
                    all_articles.extend(articles)
        
        logger.info(f"Total articles collected: {len(all_articles)}")
        return all_articles
    
    def save_data(self, articles: List[Dict]) -> str:
        """Save collected data to CSV file."""
        if not articles:
            logger.warning("No articles to save")
            return ""
        
        df = pd.DataFrame(articles)
        filepath = os.path.join(self.data_dir, self.raw_data_file)
        
        try:
            df.to_csv(filepath, index=False)
            logger.info(f"Data saved to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            return ""
    
    def run(self) -> str:
        """Main method to run the scraper."""
        logger.info("Starting offshore wind intelligence scraper")
        
        try:
            # Scrape all sources
            articles = self.scrape_all_sources()
            
            # Save data
            filepath = self.save_data(articles)
            
            logger.info(f"Scraping completed. Collected {len(articles)} articles")
            return filepath
            
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            raise

def main():
    """Main function to run the scraper."""
    try:
        scraper = OffshoreWindScraper()
        output_file = scraper.run()
        
        if output_file:
            print(f"✅ Scraping completed successfully!")
            print(f"📁 Data saved to: {output_file}")
            print(f"📊 Total articles collected: {len(scraper.collected_data)}")
        else:
            print("❌ Scraping failed")
            
    except Exception as e:
        print(f"❌ Error running scraper: {e}")
        logger.error(f"Scraper failed: {e}")

if __name__ == "__main__":
    main() 