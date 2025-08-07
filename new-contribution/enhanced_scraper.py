#!/usr/bin/env python3
"""
Enhanced Con Edison Strategic Investment Intelligence Platform - Data Scraper

This script scrapes data from multiple high-priority sources for Con Edison strategic investment intelligence,
focusing on utility infrastructure, grid modernization, and regulatory compliance opportunities.
"""

import os
import json
import time
import requests
import pandas as pd
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import logging
import random

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedConEdisonScraper:
    """Enhanced scraper class for collecting Con Edison strategic investment intelligence."""
    
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
        
        # Load keywords for detection
        self.funding_keywords = self.config.get('analysis_categories', {}).get('funding_keywords', [])
        self.utility_keywords = self.config.get('analysis_categories', {}).get('utility_keywords', [])
        self.investment_thesis_tags = self.config.get('analysis_categories', {}).get('investment_thesis_tags', [])
        
        # Rate limiting settings
        self.min_delay = 2
        self.max_delay = 5
        
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
    
    def _rate_limit(self):
        """Apply rate limiting between requests."""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)
    
    def _make_request(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """Make HTTP request with retry logic and rate limiting."""
        for attempt in range(max_retries):
            try:
                self._rate_limit()
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                    return None
                time.sleep(2 ** attempt)  # Exponential backoff
        return None
    
    def _detect_funding_content(self, text: str) -> bool:
        """Detect if text contains funding-related content."""
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Check for funding keywords
        for keyword in self.funding_keywords:
            if keyword.lower() in text_lower:
                return True
        
        # Check for dollar amounts (e.g., $10M, $100 million, etc.)
        dollar_patterns = [
            r'\$\d+[KMB]?',  # $10M, $100K, $1B
            r'\$\d+\.?\d*\s*(million|billion|thousand)',  # $10 million
            r'\d+\s*(million|billion|thousand)\s*dollars'  # 10 million dollars
        ]
        
        for pattern in dollar_patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    def _detect_utility_content(self, text: str) -> bool:
        """Detect if text contains utility-related content."""
        if not text:
            return False
        
        text_lower = text.lower()
        
        utility_keywords = [
            "grid", "transmission", "distribution", "substation", "utility",
            "infrastructure", "power line", "electrical", "energy storage",
            "smart grid", "microgrid", "load", "demand", "voltage"
        ]
        
        for keyword in utility_keywords:
            if keyword.lower() in text_lower:
                return True
        
        return False
    
    def _extract_funding_amount(self, text: str) -> Optional[str]:
        """Extract funding amount from text."""
        if not text:
            return None
        
        # Look for dollar amounts
        patterns = [
            r'\$(\d+[KMB]?)',  # $10M, $100K, $1B
            r'\$(\d+\.?\d*)\s*(million|billion|thousand)',  # $10 million
            r'(\d+)\s*(million|billion|thousand)\s*dollars'  # 10 million dollars
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def _extract_funding_stage(self, text: str) -> Optional[str]:
        """Extract funding stage from text."""
        if not text:
            return None
        
        text_lower = text.lower()
        stages = ["seed", "series a", "series b", "series c", "growth", "ipo"]
        
        for stage in stages:
            if stage in text_lower:
                return stage
        
        return None
    
    def _extract_article_data(self, article_element, source_name: str, source_url: str, selectors: Dict) -> Optional[Dict]:
        """Extract data from an article element."""
        try:
            # Extract title
            title_elem = article_element.select_one(selectors.get('title', 'h1, h2, h3'))
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Extract link
            link_elem = article_element.select_one(selectors.get('link', 'a'))
            link = link_elem.get('href') if link_elem else ""
            if link and not link.startswith('http'):
                link = source_url.rstrip('/') + '/' + link.lstrip('/')
            
            # Extract content
            content_elem = article_element.select_one(selectors.get('content', '.content, .body, p'))
            content = content_elem.get_text(strip=True) if content_elem else ""
            
            # Extract date
            date_elem = article_element.select_one(selectors.get('date', '.date, .published, time'))
            date = date_elem.get_text(strip=True) if date_elem else ""
            
            if not title and not content:
                return None
            
            # Detect content types
            has_funding = self._detect_funding_content(title + " " + content)
            has_utility = self._detect_utility_content(title + " " + content)
            
            # Extract additional data
            funding_amount = self._extract_funding_amount(title + " " + content)
            funding_stage = self._extract_funding_stage(title + " " + content)
            
            return {
                'source_name': source_name,
                'source_url': source_url,
                'title': title,
                'link': link,
                'date': date,
                'content': content,
                'category': 'industry_news',
                'has_funding_content': has_funding,
                'has_utility_content': has_utility,
                'has_investment_thesis_content': False,  # Would need AI analysis
                'funding_amount': funding_amount,
                'funding_stage': funding_stage,
                'investment_thesis': None,
                'regulated_asset_potential': None,
                'ny_service_territory_relevance': None,
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error extracting article data: {e}")
            return None
    
    def scrape_news_source(self, source_config: Dict) -> List[Dict]:
        """Scrape a single news source."""
        source_name = source_config['name']
        source_url = source_config['url']
        selectors = source_config['selectors']
        
        logger.info(f"Scraping {source_name} from {source_url}")
        
        try:
            response = self._make_request(source_url)
            if not response:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = soup.select(selectors.get('articles', 'article, .article-item, .news-item'))
            
            collected_articles = []
            for article in articles[:20]:  # Limit to 20 articles per source
                article_data = self._extract_article_data(article, source_name, source_url, selectors)
                if article_data:
                    collected_articles.append(article_data)
            
            logger.info(f"Collected {len(collected_articles)} articles from {source_name}")
            return collected_articles
            
        except Exception as e:
            logger.error(f"Error scraping {source_name}: {e}")
            return []
    
    def scrape_all_sources(self) -> List[Dict]:
        """Scrape all configured sources."""
        all_articles = []
        
        # Scrape news sources
        news_sources = self.config.get('news_sources', [])
        for source in news_sources:
            articles = self.scrape_news_source(source)
            all_articles.extend(articles)
        
        # Scrape investor lists
        investor_sources = self.config.get('investor_lists', [])
        for source in investor_sources:
            articles = self.scrape_news_source(source)
            all_articles.extend(articles)
        
        return all_articles
    
    def save_data(self, articles: List[Dict]) -> str:
        """Save collected data to CSV file."""
        if not articles:
            logger.warning("No articles to save")
            return ""
        
        df = pd.DataFrame(articles)
        filepath = os.path.join(self.data_dir, self.raw_data_file)
        df.to_csv(filepath, index=False)
        
        logger.info(f"Saved {len(articles)} articles to {filepath}")
        return filepath
    
    def run(self) -> str:
        """Run the enhanced scraper."""
        logger.info("Starting enhanced Con Edison strategic investment intelligence scraper")
        
        try:
            # Scrape all sources
            articles = self.scrape_all_sources()
            
            # Save data
            if articles:
                filepath = self.save_data(articles)
                logger.info(f"Scraping completed. Collected {len(articles)} articles")
                return filepath
            else:
                logger.warning("No articles collected")
                return ""
                
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            return ""

def main():
    """Main function to run the enhanced scraper."""
    scraper = EnhancedConEdisonScraper()
    result = scraper.run()
    
    if result:
        print(f"✅ Enhanced scraping completed successfully. Data saved to: {result}")
    else:
        print("❌ Enhanced scraping failed")

if __name__ == "__main__":
    main() 