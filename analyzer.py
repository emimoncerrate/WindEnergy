#!/usr/bin/env python3
"""
Con Edison Strategic Investment Intelligence Platform - AI Analyzer

This script processes raw scraped data using OpenAI API to extract structured insights
and identify strategic investment opportunities for Con Edison's regulated utility business.
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

class ConEdisonStrategicAnalyzer:
    """
    AI-powered analyzer that evaluates opportunities for Con Edison's regulated utility business.
    Focuses on grid reliability, CLCPA compliance, and rate-based asset potential.
    """
    
    def __init__(self):
        """Initialize the analyzer with OpenAI API key."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Set API key for older OpenAI library
        openai.api_key = api_key
        
        self.data_dir = "data"
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Utility strategic investment schema
        self.schema = {
            "investment_thesis_tag": "str",  # Grid Reliability, Peak Load Reduction, etc.
            "technology_readiness_level": "int",  # 1-9 scale
            "regulated_asset_potential": "bool",  # Can it be rate-based?
            "ny_service_territory_relevance": "bool",  # NYC/Westchester impact
            "grid_impact_score": "int",  # 1-10 scale
            "clcpa_compliance_value": "str",  # How it helps meet CLCPA mandates
            "capital_investment_required": "str",  # Low/Medium/High
            "implementation_timeline": "str",  # Short/Medium/Long term
            "risk_assessment": "str",  # Low/Medium/High
            "strategic_priority": "str"  # High/Medium/Low based on Con Edison's strategic needs
        }
    
    def analyze_article(self, article_data: Dict) -> Dict:
        """
        Analyze a single article using AI to extract utility strategic investment insights.
        
        Args:
            article_data: Dictionary containing article information
            
        Returns:
            Dictionary with structured utility investment analysis
        """
        try:
            # Prepare content for analysis
            content = f"""
Title: {article_data.get('title', 'N/A')}
Content: {article_data.get('content', 'N/A')}
Source: {article_data.get('source', 'N/A')}
Date: {article_data.get('date', 'N/A')}
            """
            
            # Strategic investment analysis prompt
            prompt = f"""
Act as a strategic investment analyst for Con Edison, New York's largest utility company. 
Analyze the following document and evaluate it as a potential investment opportunity based on:

1. Ability to enhance grid reliability and resilience
2. Potential to meet New York CLCPA (Climate Leadership and Community Protection Act) mandates
3. Suitability as a rate-based asset for regulated utility investment
4. Relevance to Con Edison's NYC and Westchester County service territory

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

Return only valid JSON with the exact field names specified above.
            """
            
            # Get AI analysis using older API format
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a utility strategic investment analyst specializing in regulated utility investments and grid modernization."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse response
            analysis_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            try:
                # Find JSON in the response
                start_idx = analysis_text.find('{')
                end_idx = analysis_text.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = analysis_text[start_idx:end_idx]
                    analysis = json.loads(json_str)
                else:
                    raise ValueError("No JSON found in response")
                    
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse AI response: {e}")
                # Return default analysis
                analysis = self._get_default_analysis()
            
            # Add metadata
            analysis.update({
                'title': article_data.get('title', 'N/A'),
                'source': article_data.get('source', 'N/A'),
                'date': article_data.get('date', 'N/A'),
                'url': article_data.get('url', 'N/A'),
                'analysis_timestamp': pd.Timestamp.now().isoformat()
            })
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing article: {e}")
            return self._get_default_analysis()
    
    def _get_default_analysis(self) -> Dict:
        """Return default analysis when AI processing fails."""
        return {
            'investment_thesis_tag': 'Grid Reliability',
            'technology_readiness_level': 5,
            'regulated_asset_potential': False,
            'ny_service_territory_relevance': True,
            'grid_impact_score': 5,
            'clcpa_compliance_value': 'Requires further analysis',
            'capital_investment_required': 'Medium',
            'implementation_timeline': 'Medium',
            'risk_assessment': 'Medium',
            'strategic_priority': 'Medium',
            'title': 'N/A',
            'source': 'N/A',
            'date': 'N/A',
            'url': 'N/A',
            'analysis_timestamp': pd.Timestamp.now().isoformat()
        }
    
    def process_raw_data(self) -> None:
        """
        Process all raw scraped data and generate strategic investment analysis.
        """
        try:
            # Load raw data
            raw_data_file = os.path.join(self.data_dir, "raw_data.json")
            if not os.path.exists(raw_data_file):
                logger.error("Raw data file not found. Run scraper.py first.")
                return
            
            with open(raw_data_file, 'r') as f:
                raw_data = json.load(f)
            
            logger.info(f"Processing {len(raw_data)} articles for strategic investment analysis...")
            
            # Analyze each article
            analyzed_data = []
            for i, article in enumerate(raw_data):
                logger.info(f"Analyzing article {i+1}/{len(raw_data)}: {article.get('title', 'Unknown')[:50]}...")
                
                analysis = self.analyze_article(article)
                analyzed_data.append(analysis)
                
                # Rate limiting - pause between requests
                if i < len(raw_data) - 1:
                    import time
                    time.sleep(1)
            
            # Save analyzed data
            output_file = os.path.join(self.data_dir, "analyzed_data.csv")
            df = pd.DataFrame(analyzed_data)
            df.to_csv(output_file, index=False)
            
            # Save detailed analysis as JSON
            strategic_analysis_file = os.path.join(self.data_dir, "strategic_analysis.json")
            with open(strategic_analysis_file, 'w') as f:
                json.dump(analyzed_data, f, indent=2)
            
            logger.info(f"Strategic investment analysis complete. Results saved to:")
            logger.info(f"  - {output_file}")
            logger.info(f"  - {strategic_analysis_file}")
            
            # Generate summary statistics
            self._generate_summary_stats(analyzed_data)
            
        except Exception as e:
            logger.error(f"Error processing data: {e}")
    
    def _generate_summary_stats(self, analyzed_data: List[Dict]) -> None:
        """Generate summary statistics for strategic investment analysis."""
        try:
            df = pd.DataFrame(analyzed_data)
            
            # Investment thesis distribution
            thesis_counts = df['investment_thesis_tag'].value_counts()
            
            # TRL distribution
            trl_counts = df['technology_readiness_level'].value_counts().sort_index()
            
            # Regulated asset potential
            regulated_potential = df['regulated_asset_potential'].value_counts()
            
            # NY territory relevance
            ny_relevance = df['ny_service_territory_relevance'].value_counts()
            
            # Strategic priority distribution
            priority_counts = df['strategic_priority'].value_counts()
            
            # Save summary
            summary = {
                'total_opportunities': len(analyzed_data),
                'investment_thesis_distribution': thesis_counts.to_dict(),
                'technology_readiness_distribution': trl_counts.to_dict(),
                'regulated_asset_potential': regulated_potential.to_dict(),
                'ny_territory_relevance': ny_relevance.to_dict(),
                'strategic_priority_distribution': priority_counts.to_dict(),
                'high_priority_opportunities': len(df[df['strategic_priority'] == 'High']),
                'regulated_asset_opportunities': len(df[df['regulated_asset_potential'] == True]),
                'high_trl_opportunities': len(df[df['technology_readiness_level'] >= 7])
            }
            
            summary_file = os.path.join(self.data_dir, "strategic_summary.json")
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            logger.info("Strategic investment summary generated:")
            logger.info(f"  - Total opportunities analyzed: {summary['total_opportunities']}")
            logger.info(f"  - High priority opportunities: {summary['high_priority_opportunities']}")
            logger.info(f"  - Regulated asset opportunities: {summary['regulated_asset_opportunities']}")
            logger.info(f"  - High TRL opportunities (7+): {summary['high_trl_opportunities']}")
            
        except Exception as e:
            logger.error(f"Error generating summary stats: {e}")

def main():
    """Main execution function."""
    try:
        analyzer = ConEdisonStrategicAnalyzer()
        analyzer.process_raw_data()
        logger.info("Strategic investment analysis completed successfully!")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")

if __name__ == "__main__":
    main() 