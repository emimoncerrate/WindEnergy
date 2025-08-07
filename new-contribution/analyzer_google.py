#!/usr/bin/env python3
"""
Con Edison Strategic Investment Intelligence Platform - Google AI 
Analyzer
"""

import os
import json
import pandas as pd
import google.generativeai as genai
from typing import Dict, List, Optional
from dotenv import load_dotenv
import logging
import time

# Load environment variables from a .env file
load_dotenv()

# Configure logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('analyzer_google.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ConEdisonStrategicAnalyzerGoogle:
    """
    Analyzes raw text data using Google's Gemini AI to identify 
strategic investment opportunities
    for Con Edison based on utility-specific criteria.
    """
    def __init__(self):
        """Initializes the AI model and sets up the project 
directory."""
        api_key = os.getenv('GOOGLE_AI_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_AI_API_KEY environment variable is required")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        self.data_dir = "data"
        os.makedirs(self.data_dir, exist_ok=True)
        
        # This schema is used for internal reference and is defined in the prompt.
        self.schema = {
            "investment_thesis_tag": "str",
            "technology_readiness_level": "int",
            "regulated_asset_potential": "bool",
            "ny_service_territory_relevance": "bool",
            "grid_impact_score": "int",
            "clcpa_compliance_value": "str",
            "capital_investment_required": "str",
            "implementation_timeline": "str",
            "risk_assessment": "str",
            "strategic_priority": "str"
        }

    def _get_analysis_prompt(self, article_data: Dict) -> str:
        """Constructs the complete AI prompt for a given article."""
        content = f"""Title: {article_data.get('title', 'N/A')}
Source: {article_data.get('source', 'N/A')}
Date: {article_data.get('date', 'N/A')}
Content: {article_data.get('content', 'N/A')}"""

        prompt = f"""Act as a strategic investment analyst for Con 
Edison, New York's largest utility company. Analyze the following 
document and evaluate it as a potential investment opportunity based 
on:

1. Ability to enhance grid reliability and resilience
2. Potential to meet New York CLCPA (Climate Leadership and Community 
Protection Act) mandates
3. Suitability as a rate-based asset for regulated utility investment
4. Relevance to Con Edison's NYC and Westchester County service 
territory

Extract the following information and return as JSON:

{{
    "investment_thesis_tag": "Primary reason Con Edison should care (e.g., 'Grid Reliability', 'Peak Load Reduction', 'Transmission Decongestion', 'Electrification of Heat/Transport', 'Storm Hardening', 'Regulatory Compliance (CLCPA)', 'Demand Response', 'Energy Storage', 'Smart Grid Technology')", 
    "technology_readiness_level": "Score 1-9 (1-3=concept, 4-6=prototype, 7-9=commercial)",
    "regulated_asset_potential": "true/false - can this become a rate-based asset?",
    "ny_service_territory_relevance": "true/false - does this impact NYC/Westchester?",
    "grid_impact_score": "Score 1-10 for potential grid improvement",
    "clcpa_compliance_value": "How this helps meet CLCPA mandates (specific benefits)",
    "capital_investment_required": "Low/Medium/High",
    "implementation_timeline": "Short/Medium/Long term",
    "risk_assessment": "Low/Medium/High",
    "strategic_priority": "High/Medium/Low based on Con Edison's strategic needs"
}}

Document to analyze:
{content}

Return only valid JSON with the exact field names specified above. Do not include any text before or after the JSON object."""
        return prompt

    def analyze_article(self, article_data: Dict) -> Dict:
        """Sends a single article's content to the AI for analysis."""
        try:
            prompt = self._get_analysis_prompt(article_data)
            
            # The model is often more reliable with a short intro.
            response = self.model.generate_content(prompt)
            analysis_text = response.text.strip()
            
            try:
                # Robustly find and parse the JSON object
                start_idx = analysis_text.find('{')
                end_idx = analysis_text.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = analysis_text[start_idx:end_idx]
                    analysis = json.loads(json_str)
                else:
                    raise ValueError("No valid JSON found in AI response")
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse AI response for '{article_data.get('title', 'N/A')}': {e}")
                analysis = self._get_default_analysis()
            
            # Add original article metadata to the analysis output
            analysis.update({
                'title': article_data.get('title', 'N/A'),
                'source': article_data.get('source', 'N/A'),
                'date': article_data.get('date', 'N/A'),
                'url': article_data.get('url', 'N/A'),
                'analysis_timestamp': pd.Timestamp.now().isoformat()
            })
            
            return analysis
            
        except Exception as e:
            logger.error(f"Critical error analyzing article '{article_data.get('title', 'N/A')}': {e}")
            return self._get_default_analysis()
    
    def _get_default_analysis(self) -> Dict:
        """Returns a default analysis dictionary for failed requests."""
        return {
            'investment_thesis_tag': 'Uncategorized',
            'technology_readiness_level': 0, # Use 0 for unrated
            'regulated_asset_potential': False,
            'ny_service_territory_relevance': False,
            'grid_impact_score': 0,
            'clcpa_compliance_value': 'N/A',
            'capital_investment_required': 'N/A',
            'implementation_timeline': 'N/A',
            'risk_assessment': 'N/A',
            'strategic_priority': 'Low',
            'title': 'N/A',
            'source': 'N/A',
            'date': 'N/A',
            'url': 'N/A',
            'analysis_timestamp': pd.Timestamp.now().isoformat()
        }

    def process_raw_data(self) -> None:
        """Loads raw data, analyzes it, and saves the results."""
        try:
            raw_data_file = os.path.join(self.data_dir, 
"raw_data.json")
            if not os.path.exists(raw_data_file):
                logger.error(f"Raw data file '{raw_data_file}' not found. Run scraper first.")
                return
            
            with open(raw_data_file, 'r') as f:
                raw_data = json.load(f)
            
            logger.info(f"Processing {len(raw_data)} articles for strategic investment analysis...")
            
            analyzed_data = []
            for i, article in enumerate(raw_data):
                logger.info(f"Analyzing article {i+1}/{len(raw_data)}: {article.get('title', 'Unknown')[:50]}...")
                
                analysis = self.analyze_article(article)
                analyzed_data.append(analysis)
                
                # Introduce a small delay to avoid hitting API rate limits
                time.sleep(1)
            
            analyzed_json_file = os.path.join(self.data_dir, "analyzed_data.json")
            with open(analyzed_json_file, 'w') as f:
                json.dump(analyzed_data, f, indent=2)
            
            df = pd.DataFrame(analyzed_data)
            csv_file = os.path.join(self.data_dir, 
"analyzed_data.csv")
            df.to_csv(csv_file, index=False)
            
            logger.info(f"✅ Analysis completed! Processed {len(analyzed_data)} articles.")
            logger.info(f"📁 Data saved to: {analyzed_json_file} and {csv_file}")
            
            self._generate_summary_stats(analyzed_data)
            
        except Exception as e:
            logger.error(f"Error processing raw data: {e}")

    def _generate_summary_stats(self, analyzed_data: List[Dict]) -> None:
        """Generates and logs summary statistics from the analyzed data."""
        try:
            df = pd.DataFrame(analyzed_data)
            
            logger.info("\n--- Analysis Summary ---")
            
            thesis_counts = df['investment_thesis_tag'].value_counts()
            logger.info("📊 Investment Thesis Distribution:")
            for thesis, count in thesis_counts.head(10).items():
                logger.info(f"  - {thesis}: {count}")
            
            priority_counts = df['strategic_priority'].value_counts()
            logger.info("\n⭐ Strategic Priority Distribution:")
            for priority, count in priority_counts.items():
                logger.info(f"  - {priority}: {count}")
            
            high_priority_count = len(df[df['strategic_priority'] == 'High'])
            logger.info(f"\n🚀 Total High Priority Opportunities: {high_priority_count}")
            
            regulated_assets_count = len(df[df['regulated_asset_potential'] == True])
            logger.info(f"💰 Total Regulated Asset Opportunities: {regulated_assets_count}")
            
        except Exception as e:
            logger.error(f"Error generating summary stats: {e}")

def main():
    """Main function to run the analyzer."""
    try:
        analyzer = ConEdisonStrategicAnalyzerGoogle()
        analyzer.process_raw_data()
        logger.info("✅ Google AI analysis completed successfully!")
    except Exception as e:
        logger.error(f"Error in main execution: {e}")

if __name__ == "__main__":
    main()
