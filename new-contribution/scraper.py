#!/usr/bin/env python3
"""
Con Edison Strategic Investment Intelligence Platform - Data Scraper

This script scrapes data from high-priority sources for Con Edison strategic investment intelligence,
focusing on utility infrastructure, grid modernization, and regulatory compliance opportunities.
"""

import os
import json
import time
import requests
import pandas as pd
import re
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

class ConEdisonScraper:
    """Main scraper class for collecting Con Edison strategic investment intelligence."""
    
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
    
    def _detect_funding_content(self, text: str, source_keywords: List[str] = None) -> bool:
        """
        Detect if text contains funding-related content.
        
        Args:
            text: The text to analyze
            source_keywords: Optional source-specific funding keywords
            
        Returns:
            bool: True if funding content is detected
        """
        if not text:
            return False
        
        # Combine global and source-specific keywords
        keywords = self.funding_keywords.copy()
        if source_keywords:
            keywords.extend(source_keywords)
        
        # Convert to lowercase for case-insensitive matching
        text_lower = text.lower()
        
        # Check for funding keywords
        for keyword in keywords:
            if keyword.lower() in text_lower:
                return True
        
        # Check for dollar amounts (e.g., $10M, $100 million, etc.)
        dollar_patterns = [
            r'\$\d+\.?\d*\s*[mb]illion',
            r'\$\d+\.?\d*\s*[mk]',
            r'\d+\.?\d*\s*[mb]illion\s*dollars',
            r'\d+\.?\d*\s*[mk]\s*dollars'
        ]
        
        for pattern in dollar_patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    def _detect_utility_content(self, text: str, source_keywords: List[str] = None) -> bool:
        """
        Detect if text contains utility-related content.
        
        Args:
            text: The text to analyze
            source_keywords: Optional source-specific utility keywords
            
        Returns:
            bool: True if utility content is detected
        """
        if not text:
            return False
        
        # Utility-related keywords
        utility_keywords = [
            'grid', 'transmission', 'distribution', 'utility', 'power',
            'electricity', 'infrastructure', 'substation', 'smart grid',
            'reliability', 'resilience', 'modernization', 'upgrade',
            'con edison', 'coned', 'nyc', 'new york', 'westchester',
            'clcpa', 'climate', 'renewable', 'solar', 'wind', 'storage',
            'battery', 'microgrid', 'demand response', 'peak load'
        ]
        
        # Add source-specific keywords
        if source_keywords:
            utility_keywords.extend(source_keywords)
        
        # Convert to lowercase for case-insensitive matching
        text_lower = text.lower()
        
        # Check for utility keywords
        for keyword in utility_keywords:
            if keyword.lower() in text_lower:
                return True
        
        return False
    
    def _detect_investment_thesis_content(self, text: str) -> bool:
        """
        Detect if text contains investment thesis content.
        
        Args:
            text: The text to analyze
            
        Returns:
            bool: True if investment thesis content is detected
        """
        if not text:
            return False
        
        # Check for investment thesis tags
        text_lower = text.lower()
        for thesis in self.investment_thesis_tags:
            if thesis.lower() in text_lower:
                return True
        
        return False
    
    def _extract_funding_amount(self, text: str) -> Optional[str]:
        """Extract funding amount from text."""
        # Look for dollar amounts
        patterns = [
            r'\$(\d+\.?\d*)\s*([mb]illion)',
            r'\$(\d+\.?\d*)\s*([mk])',
            r'(\d+\.?\d*)\s*([mb]illion)\s*dollars',
            r'(\d+\.?\d*)\s*([mk])\s*dollars'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = match.group(1)
                unit = match.group(2).lower()
                if unit in ['m', 'million']:
                    return f"${amount}M"
                elif unit in ['b', 'billion']:
                    return f"${amount}B"
                elif unit in ['k', 'thousand']:
                    return f"${amount}K"
        
        return None
    
    def _extract_funding_stage(self, text: str) -> Optional[str]:
        """Extract funding stage from text."""
        stages = ['seed', 'series a', 'series b', 'series c', 'growth', 'ipo', 'grant', 'loan']
        text_lower = text.lower()
        
        for stage in stages:
            if stage in text_lower:
                return stage.title()
        
        return None
    
    def _extract_investment_thesis(self, text: str) -> Optional[str]:
        """Extract investment thesis from text."""
        text_lower = text.lower()
        
        for thesis in self.investment_thesis_tags:
            if thesis.lower() in text_lower:
                return thesis
        
        return None
    
    def _extract_utility_indicators(self, text: str) -> Dict[str, Optional[str]]:
        """Extract utility-specific indicators from text."""
        text_lower = text.lower()
        
        # Check for regulated asset potential
        regulated_keywords = ['infrastructure', 'grid asset', 'capital investment', 'long-term asset', 'rate base']
        regulated_asset_potential = any(keyword in text_lower for keyword in regulated_keywords)
        
        # Check for NY service territory relevance
        ny_keywords = ['nyc', 'new york', 'manhattan', 'brooklyn', 'queens', 'bronx', 'staten island', 'westchester']
        ny_relevance = any(keyword in text_lower for keyword in ny_keywords)
        
        return {
            'regulated_asset_potential': regulated_asset_potential,
            'ny_service_territory_relevance': ny_relevance
        }
    
    def _make_request(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """Make HTTP request with retry logic."""
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Requesting {url} (attempt {attempt}/{max_retries})")
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed for {url}: {e}")
                if attempt < max_retries:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                    return None
    
    def _extract_article_data(self, article_element, source_name: str, source_url: str, selectors: Dict, source_config: Dict) -> Optional[Dict]:
        """Extract article data from a BeautifulSoup element with comprehensive detection."""
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
            
            # Combine title and content for detection
            full_text = f"{title} {content}"
            
            # Get source configuration
            category = source_config.get('category', 'other')
            source_funding_keywords = source_config.get('funding_keywords', [])
            
            # Detect various content types
            has_funding_content = self._detect_funding_content(full_text, source_funding_keywords)
            has_utility_content = self._detect_utility_content(full_text)
            has_investment_thesis_content = self._detect_investment_thesis_content(full_text)
            
            # Extract funding information if detected
            funding_amount = None
            funding_stage = None
            
            if has_funding_content:
                funding_amount = self._extract_funding_amount(full_text)
                funding_stage = self._extract_funding_stage(full_text)
            
            # Extract investment thesis if detected
            investment_thesis = None
            if has_investment_thesis_content:
                investment_thesis = self._extract_investment_thesis(full_text)
            
            # Extract utility indicators
            utility_indicators = self._extract_utility_indicators(full_text)
            
            return {
                'source_name': source_name,
                'source_url': source_url,
                'title': title,
                'link': link,
                'date': date,
                'content': content,
                'category': category,
                'has_funding_content': has_funding_content,
                'has_utility_content': has_utility_content,
                'has_investment_thesis_content': has_investment_thesis_content,
                'funding_amount': funding_amount,
                'funding_stage': funding_stage,
                'investment_thesis': investment_thesis,
                'regulated_asset_potential': utility_indicators.get('regulated_asset_potential'),
                'ny_service_territory_relevance': utility_indicators.get('ny_service_territory_relevance'),
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
            
            # Find article elements with multiple selector strategies
            article_selectors = selectors.get('articles', 'article, .post, .news-item, .article')
            article_elements = soup.select(article_selectors)
            
            # If no articles found with primary selectors, try broader selectors
            if not article_elements:
                logger.info(f"No articles found with primary selectors, trying broader selectors")
                article_elements = soup.select('div, article, section')
                # Filter for elements that might be articles (have titles or links)
                article_elements = [elem for elem in article_elements if elem.select_one('h1, h2, h3, a')]
            
            logger.info(f"Found {len(article_elements)} potential articles")
            
            # Process each article element
            for i, article_element in enumerate(article_elements):
                try:
                    article_data = self._extract_article_data(article_element, source_name, source_url, selectors, source_config)
                    if article_data and article_data['title'] != "No title":
                        articles.append(article_data)
                        logger.debug(f"Extracted article {i+1}: {article_data['title'][:50]}...")
                except Exception as e:
                    logger.warning(f"Error processing article {i+1}: {e}")
                    continue
            
            # Log summary
            funding_count = sum(1 for a in articles if a.get('has_funding_content'))
            utility_count = sum(1 for a in articles if a.get('has_utility_content'))
            thesis_count = sum(1 for a in articles if a.get('has_investment_thesis_content'))
            
            logger.info(f"Successfully extracted {len(articles)} articles from {source_name} (Funding: {funding_count}, Utility: {utility_count}, Investment Thesis: {thesis_count})")
            
        except Exception as e:
            logger.error(f"Error scraping {source_name}: {e}")
        
        return articles
    
    def scrape_all_sources(self) -> List[Dict]:
        """Scrape all configured sources."""
        all_articles = []
        sources = self.config.get('sources', {})
        
        for source_key, source_config in sources.items():
            try:
                articles = self.scrape_source(source_key, source_config)
                all_articles.extend(articles)
                
                # Add delay between sources to be respectful
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error scraping source {source_key}: {e}")
                continue
        
        return all_articles
    
    def save_data(self, articles: List[Dict]) -> str:
        """Save scraped data to JSON file."""
        if not articles:
            logger.warning("No articles to save")
            return ""
        
        # Save as JSON for the analyzer
        json_file = os.path.join(self.data_dir, "raw_data.json")
        with open(json_file, 'w') as f:
            json.dump(articles, f, indent=2)
        
        # Also save as CSV for reference
        csv_file = os.path.join(self.data_dir, "raw_data.csv")
        df = pd.DataFrame(articles)
        df.to_csv(csv_file, index=False)
        
        logger.info(f"Saved {len(articles)} articles to {json_file} and {csv_file}")
        return json_file
    
    def run(self) -> str:
        """Main method to run the scraper."""
        logger.info("Starting Con Edison strategic investment intelligence scraper")
        
        try:
            # Scrape all sources
            articles = self.scrape_all_sources()
            
            # Log summary statistics
            total_articles = len(articles)
            funding_articles = sum(1 for a in articles if a.get('has_funding_content'))
            utility_articles = sum(1 for a in articles if a.get('has_utility_content'))
            thesis_articles = sum(1 for a in articles if a.get('has_investment_thesis_content'))
            offshore_wind_articles = sum(1 for a in articles if a.get('category') == 'offshore_wind')
            
            logger.info(f"Total articles collected: {total_articles}")
            logger.info(f"Funding-related articles: {funding_articles}")
            logger.info(f"Utility-related articles: {utility_articles}")
            logger.info(f"Investment thesis articles: {thesis_articles}")
            logger.info(f"Offshore wind articles: {offshore_wind_articles}")
            
            # Save data
            if articles:
                output_file = self.save_data(articles)
                logger.info(f"Scraping completed. Collected {total_articles} articles")
                return output_file
            else:
                logger.warning("No articles to save")
                logger.info("Scraping completed. Collected 0 articles")
                return ""
                
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            raise

def main():
    """Main function to run the scraper."""
    try:
        scraper = ConEdisonScraper()
        output_file = scraper.run()
        
        if output_file:
            print(f"✅ Scraping completed successfully!")
            print(f"📁 Data saved to: {output_file}")
        else:
            print("❌ Scraping failed")
            
    except Exception as e:
        print(f"❌ Error running scraper: {e}")
        logger.error(f"Scraper failed: {e}")

if __name__ == "__main__":
    main() 