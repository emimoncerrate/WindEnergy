#!/usr/bin/env python3
"""
Test script for the Climate Tech Funding Analyzer
"""

import pandas as pd
import os
from analyzer import ClimateTechFundingAnalyzer

def test_analyzer():
    """Test the analyzer with a small subset of data."""
    
    # Initialize analyzer
    analyzer = ClimateTechFundingAnalyzer()
    
    # Load raw data
    df = analyzer.load_raw_data()
    
    # Take only the first 3 articles for testing
    test_df = df.head(3)
    
    print(f"Testing analyzer with {len(test_df)} articles...")
    
    # Analyze the test articles
    analyzed_df = analyzer.analyze_all_articles(test_df)
    
    # Save test results
    test_file = os.path.join(analyzer.data_dir, 'test_analyzed_data.csv')
    analyzed_df.to_csv(test_file, index=False)
    
    print(f"Test analysis completed. Results saved to {test_file}")
    
    # Show results
    for idx, row in analyzed_df.iterrows():
        print(f"\nArticle {idx + 1}:")
        print(f"Title: {row.get('title', 'No title')[:50]}...")
        print(f"Company: {row.get('company_name', 'N/A')}")
        print(f"Funding: {row.get('total_funding_amount', 'N/A')}")
        print(f"Investor: {row.get('lead_investor', 'N/A')}")
        print(f"Summary: {row.get('strategic_summary', 'N/A')[:100]}...")

if __name__ == "__main__":
    test_analyzer() 