#!/usr/bin/env python3
"""
Offshore Wind Strategic Intelligence Platform - AI Analyzer

This script processes raw scraped data using OpenAI API to extract structured insights
and identify strategic opportunities for utilities in the Northeast offshore wind sector.
"""

import os
import json
import pandas as pd
import openai
from typing import Dict, List, Optional
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('analyzer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OffshoreWindAnalyzer:
    """AI-powered analyzer for offshore wind intelligence data."""
    
    def __init__(self):
        """Initialize the analyzer with OpenAI client and configuration."""
        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Set API key for older OpenAI library
        openai.api_key = api_key
        
        # Load configuration
        self.config = self._load_config()
        self.data_dir = os.getenv('DATA_DIR', './data')
        self.raw_data_file = os.getenv('RAW_DATA_FILE', 'raw_data.csv')
        self.analyzed_data_file = os.getenv('ANALYZED_DATA_FILE', 'analyzed_data.csv')
        
        # Load analysis categories
        self.analysis_categories = self.config.get('analysis_categories', {})
        
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
    
    def _create_analysis_prompt(self, article_text: str) -> str:
        """Create a detailed prompt for AI analysis of offshore wind articles."""
        
        technology_types = self.analysis_categories.get('technology_types', [])
        grid_keywords = self.analysis_categories.get('grid_infrastructure_keywords', [])
        priority_locations = self.analysis_categories.get('priority_locations', [])
        project_stages = self.analysis_categories.get('project_stages', [])
        
        prompt = f"""
You are an expert analyst specializing in offshore wind energy infrastructure and utility strategic intelligence. 
Analyze the following article text and extract structured data relevant to utility business needs.

Article Text:
{article_text}

Please analyze this content and provide a JSON response with the following structure:

{{
    "technology_type": "Choose from: {', '.join(technology_types)}",
    "grid_infrastructure_keywords": ["List any mentions of: {', '.join(grid_keywords)}"],
    "location": "Identify specific geographic mentions, prioritizing: {', '.join(priority_locations)}",
    "project_stage": "Choose from: {', '.join(project_stages)} or 'other'",
    "funding_stage": "Identify funding stage: 'announced', 'approved', 'construction', 'operational', or 'other'",
    "investment_amount": "Extract any mentioned dollar amounts or 'not specified'",
    "strategic_relevance": "High/Medium/Low - relevance to utility grid infrastructure needs",
    "key_insights": "Brief summary of most important strategic implications"
}}

Focus on:
1. Grid infrastructure and transmission developments
2. Cable landing sites and interconnection projects
3. Substation and converter station developments
4. Port infrastructure for offshore wind
5. Regulatory and policy developments affecting utilities

If information is not available in the text, use "not specified" or "other" as appropriate.
"""
        return prompt
    
    def analyze_article(self, article_data: Dict) -> Dict:
        """Analyze a single article using OpenAI API."""
        try:
            # Combine title and content for analysis
            article_text = f"Title: {article_data.get('title', '')}\n\nContent: {article_data.get('content', '')}"
            
            # Create analysis prompt
            prompt = self._create_analysis_prompt(article_text)
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",  # Using a cost-effective model
                messages=[
                    {"role": "system", "content": "You are an expert analyst specializing in offshore wind energy infrastructure and utility strategic intelligence."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent analysis
                max_tokens=1000
            )
            
            # Extract and parse the response
            analysis_text = response.choices[0].message.content
            
            # Try to parse JSON from the response
            try:
                # Find JSON in the response (sometimes it's wrapped in markdown)
                import re
                json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
                if json_match:
                    analysis_json = json.loads(json_match.group())
                else:
                    # If no JSON found, create a basic structure
                    analysis_json = {
                        "technology_type": "other",
                        "grid_infrastructure_keywords": [],
                        "location": "not specified",
                        "project_stage": "other",
                        "funding_stage": "other",
                        "investment_amount": "not specified",
                        "strategic_relevance": "Low",
                        "key_insights": "Analysis failed"
                    }
                
                # Combine original data with analysis
                analyzed_article = {**article_data, **analysis_json}
                return analyzed_article
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON from AI response: {e}")
                # Return basic structure with original data
                return {
                    **article_data,
                    "technology_type": "other",
                    "grid_infrastructure_keywords": [],
                    "location": "not specified",
                    "project_stage": "other",
                    "funding_stage": "other",
                    "investment_amount": "not specified",
                    "strategic_relevance": "Low",
                    "key_insights": "Analysis failed"
                }
                
        except Exception as e:
            logger.error(f"Error analyzing article: {e}")
            return {
                **article_data,
                "technology_type": "other",
                "grid_infrastructure_keywords": [],
                "location": "not specified",
                "project_stage": "other",
                "funding_stage": "other",
                "investment_amount": "not specified",
                "strategic_relevance": "Low",
                "key_insights": f"Analysis error: {str(e)}"
            }
    
    def load_raw_data(self) -> pd.DataFrame:
        """Load raw data from CSV file."""
        filepath = os.path.join(self.data_dir, self.raw_data_file)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Raw data file not found: {filepath}")
        
        try:
            df = pd.read_csv(filepath)
            logger.info(f"Loaded {len(df)} articles from {filepath}")
            return df
        except Exception as e:
            logger.error(f"Error loading raw data: {e}")
            raise
    
    def analyze_all_articles(self, df: pd.DataFrame) -> pd.DataFrame:
        """Analyze all articles in the dataset."""
        analyzed_articles = []
        
        logger.info(f"Starting analysis of {len(df)} articles")
        
        for index, row in df.iterrows():
            logger.info(f"Analyzing article {index + 1}/{len(df)}: {row.get('title', 'No title')[:50]}...")
            
            article_data = row.to_dict()
            analyzed_article = self.analyze_article(article_data)
            analyzed_articles.append(analyzed_article)
            
            # Add a small delay to avoid rate limiting
            import time
            time.sleep(0.5)
        
        analyzed_df = pd.DataFrame(analyzed_articles)
        logger.info(f"Analysis completed. Processed {len(analyzed_df)} articles")
        
        return analyzed_df
    
    def perform_gap_analysis(self, df: pd.DataFrame) -> Dict:
        """Perform gap analysis to identify strategic opportunities."""
        gap_analysis = {}
        
        # Analyze by technology type
        tech_counts = df['technology_type'].value_counts()
        gap_analysis['technology_gaps'] = {
            'counts': tech_counts.to_dict(),
            'gaps': tech_counts[tech_counts <= 1].index.tolist()
        }
        
        # Analyze by location
        location_counts = df['location'].value_counts()
        gap_analysis['location_gaps'] = {
            'counts': location_counts.to_dict(),
            'gaps': location_counts[location_counts <= 1].index.tolist()
        }
        
        # Analyze strategic relevance
        relevance_counts = df['strategic_relevance'].value_counts()
        gap_analysis['strategic_relevance'] = {
            'counts': relevance_counts.to_dict(),
            'high_relevance_count': len(df[df['strategic_relevance'] == 'High'])
        }
        
        # Find articles with grid infrastructure keywords
        grid_keyword_articles = df[df['grid_infrastructure_keywords'].apply(lambda x: len(x) > 0 if isinstance(x, list) else False)]
        gap_analysis['grid_infrastructure_mentions'] = {
            'count': len(grid_keyword_articles),
            'articles': grid_keyword_articles[['title', 'grid_infrastructure_keywords', 'strategic_relevance']].to_dict('records')
        }
        
        return gap_analysis
    
    def save_analyzed_data(self, df: pd.DataFrame) -> str:
        """Save analyzed data to CSV file."""
        filepath = os.path.join(self.data_dir, self.analyzed_data_file)
        
        try:
            df.to_csv(filepath, index=False)
            logger.info(f"Analyzed data saved to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving analyzed data: {e}")
            return ""
    
    def save_gap_analysis(self, gap_analysis: Dict) -> str:
        """Save gap analysis results to JSON file."""
        filepath = os.path.join(self.data_dir, 'gap_analysis.json')
        
        try:
            with open(filepath, 'w') as f:
                json.dump(gap_analysis, f, indent=2)
            logger.info(f"Gap analysis saved to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving gap analysis: {e}")
            return ""
    
    def run(self) -> Dict:
        """Main method to run the analyzer."""
        logger.info("Starting offshore wind intelligence analysis")
        
        try:
            # Load raw data
            raw_df = self.load_raw_data()
            
            # Analyze all articles
            analyzed_df = self.analyze_all_articles(raw_df)
            
            # Perform gap analysis
            gap_analysis = self.perform_gap_analysis(analyzed_df)
            
            # Save results
            analyzed_file = self.save_analyzed_data(analyzed_df)
            gap_file = self.save_gap_analysis(gap_analysis)
            
            results = {
                'analyzed_file': analyzed_file,
                'gap_analysis_file': gap_file,
                'total_articles': len(analyzed_df),
                'gap_analysis': gap_analysis
            }
            
            logger.info(f"Analysis completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise

def main():
    """Main function to run the analyzer."""
    try:
        analyzer = OffshoreWindAnalyzer()
        results = analyzer.run()
        
        print(f"✅ Analysis completed successfully!")
        print(f"📁 Analyzed data saved to: {results['analyzed_file']}")
        print(f"📊 Gap analysis saved to: {results['gap_analysis_file']}")
        print(f"📈 Total articles analyzed: {results['total_articles']}")
        
        # Print key findings
        gap_analysis = results['gap_analysis']
        print(f"\n🔍 Key Findings:")
        print(f"   • Technology gaps: {len(gap_analysis['technology_gaps']['gaps'])}")
        print(f"   • High relevance articles: {gap_analysis['strategic_relevance']['high_relevance_count']}")
        print(f"   • Grid infrastructure mentions: {gap_analysis['grid_infrastructure_mentions']['count']}")
        
    except Exception as e:
        print(f"❌ Error running analyzer: {e}")
        logger.error(f"Analyzer failed: {e}")

if __name__ == "__main__":
    main() 