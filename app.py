#!/usr/bin/env python3
"""
Offshore Wind Strategic Intelligence Platform - Dashboard

Streamlit dashboard for visualizing offshore wind intelligence data and strategic insights.
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Offshore Wind Strategic Intelligence Platform",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

class OffshoreWindDashboard:
    """Streamlit dashboard for offshore wind intelligence."""
    
    def __init__(self):
        """Initialize the dashboard."""
        self.data_dir = os.getenv('DATA_DIR', './data')
        self.analyzed_data_file = os.getenv('ANALYZED_DATA_FILE', 'analyzed_data.csv')
        self.gap_analysis_file = os.path.join(self.data_dir, 'gap_analysis.json')
        
    def load_data(self):
        """Load analyzed data and gap analysis."""
        analyzed_file = os.path.join(self.data_dir, self.analyzed_data_file)
        
        if os.path.exists(analyzed_file):
            self.df = pd.read_csv(analyzed_file)
        else:
            st.error("Analyzed data file not found. Please run the analyzer first.")
            st.stop()
        
        # Load gap analysis
        if os.path.exists(self.gap_analysis_file):
            with open(self.gap_analysis_file, 'r') as f:
                self.gap_analysis = json.load(f)
        else:
            self.gap_analysis = {}
    
    def render_header(self):
        """Render the main header."""
        st.title("🌊 Offshore Wind Strategic Intelligence Platform MVP")
        st.markdown("---")
        
        # Key insight headline
        st.header("📊 Analysis: Funding & Project Distribution by Technology Type")
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Articles", len(self.df))
        
        with col2:
            high_relevance = len(self.df[self.df['strategic_relevance'] == 'High'])
            st.metric("High Relevance", high_relevance)
        
        with col3:
            grid_mentions = len(self.df[self.df['grid_infrastructure_keywords'].apply(
                lambda x: len(x) > 0 if isinstance(x, list) else False
            )])
            st.metric("Grid Infrastructure Mentions", grid_mentions)
        
        with col4:
            unique_sources = self.df['source_name'].nunique()
            st.metric("Data Sources", unique_sources)
    
    def render_technology_analysis(self):
        """Render technology type analysis."""
        st.subheader("🔧 Technology Type Distribution")
        
        # Create technology type chart
        tech_counts = self.df['technology_type'].value_counts()
        
        # Create a bar chart
        st.bar_chart(tech_counts)
        
        # Display the data
        st.write("**Technology Type Breakdown:**")
        for tech, count in tech_counts.items():
            st.write(f"• {tech}: {count} articles")
        
        # Identify gaps
        gaps = tech_counts[tech_counts <= 1]
        if len(gaps) > 0:
            st.warning(f"⚠️ **Strategic Gaps Identified:** {', '.join(gaps.index)} have limited coverage")
    
    def render_location_analysis(self):
        """Render location analysis."""
        st.subheader("📍 Geographic Distribution")
        
        # Create location chart
        location_counts = self.df['location'].value_counts()
        
        # Filter out "not specified" for better visualization
        location_counts_filtered = location_counts[location_counts.index != 'not specified']
        
        if len(location_counts_filtered) > 0:
            st.bar_chart(location_counts_filtered)
            
            st.write("**Geographic Breakdown:**")
            for location, count in location_counts_filtered.items():
                st.write(f"• {location}: {count} articles")
        else:
            st.info("No specific geographic data available in current dataset")
    
    def render_strategic_insights(self):
        """Render strategic insights summary."""
        st.subheader("💡 Strategic Insights Summary")
        
        # Find high relevance articles
        high_relevance_df = self.df[self.df['strategic_relevance'] == 'High']
        
        if len(high_relevance_df) > 0:
            st.success(f"🎯 **{len(high_relevance_df)} High-Impact Articles Identified**")
            
            for idx, row in high_relevance_df.iterrows():
                with st.expander(f"📰 {row['title'][:100]}..."):
                    st.write(f"**Source:** {row['source_name']}")
                    st.write(f"**Technology Type:** {row['technology_type']}")
                    st.write(f"**Location:** {row['location']}")
                    st.write(f"**Key Insights:** {row['key_insights']}")
                    if row['link'] and row['link'] != 'not specified':
                        st.write(f"**Link:** [{row['link']}]({row['link']})")
        else:
            st.info("No high-relevance articles found in current dataset")
    
    def render_grid_infrastructure_analysis(self):
        """Render grid infrastructure analysis."""
        st.subheader("⚡ Grid Infrastructure Analysis")
        
        # Find articles with grid infrastructure keywords
        grid_articles = self.df[self.df['grid_infrastructure_keywords'].apply(
            lambda x: len(x) > 0 if isinstance(x, list) else False
        )]
        
        if len(grid_articles) > 0:
            st.success(f"🔌 **{len(grid_articles)} Grid Infrastructure Articles Found**")
            
            for idx, row in grid_articles.iterrows():
                with st.expander(f"🔌 {row['title'][:100]}..."):
                    st.write(f"**Source:** {row['source_name']}")
                    st.write(f"**Grid Keywords:** {', '.join(row['grid_infrastructure_keywords'])}")
                    st.write(f"**Strategic Relevance:** {row['strategic_relevance']}")
                    st.write(f"**Key Insights:** {row['key_insights']}")
        else:
            st.info("No grid infrastructure mentions found in current dataset")
    
    def render_raw_data(self):
        """Render raw data table."""
        st.subheader("📋 Raw Data Table")
        
        # Create a filtered view
        st.write("**Filtered Data View:**")
        
        # Add filters
        col1, col2 = st.columns(2)
        
        with col1:
            relevance_filter = st.selectbox(
                "Filter by Strategic Relevance:",
                ['All', 'High', 'Medium', 'Low']
            )
        
        with col2:
            tech_filter = st.selectbox(
                "Filter by Technology Type:",
                ['All'] + list(self.df['technology_type'].unique())
            )
        
        # Apply filters
        filtered_df = self.df.copy()
        
        if relevance_filter != 'All':
            filtered_df = filtered_df[filtered_df['strategic_relevance'] == relevance_filter]
        
        if tech_filter != 'All':
            filtered_df = filtered_df[filtered_df['technology_type'] == tech_filter]
        
        # Display the data
        st.dataframe(
            filtered_df[['title', 'source_name', 'technology_type', 'location', 'strategic_relevance']],
            use_container_width=True
        )
    
    def render_methodology(self):
        """Render methodology section."""
        st.subheader("🔬 Methodology")
        
        st.markdown("""
        **Data Collection:**
        - Automated scraping from high-priority sources including NYSERDA, BOEM, Con Edison Transmission, and major developers
        - Focus on Northeast offshore wind developments
        - Real-time data collection with error handling and rate limiting
        
        **AI-Powered Analysis:**
        - Custom OpenAI GPT-4 prompts designed for utility business needs
        - Structured extraction of technology types, locations, and strategic relevance
        - Gap analysis to identify underserved areas and opportunities
        
        **Strategic Focus:**
        - Grid infrastructure and transmission developments
        - Cable landing sites and interconnection projects
        - Substation and converter station developments
        - Port infrastructure for offshore wind
        - Regulatory and policy developments affecting utilities
        
        **Data Sources:**
        - NYSERDA: New York-specific project solicitations and contract awards
        - BOEM: Federal-level news on lease auctions and project approvals
        - Con Edison Transmission: Direct project and grid integration news
        - Developer Sources: Equinor and Ørsted project updates
        - Industry News: Renewable Energy World offshore wind coverage
        """)
    
    def run(self):
        """Run the dashboard."""
        # Load data
        self.load_data()
        
        # Render header
        self.render_header()
        
        # Create tabs for different views
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 Technology Analysis", 
            "📍 Geographic Analysis", 
            "💡 Strategic Insights",
            "⚡ Grid Infrastructure",
            "📋 Raw Data",
            "🔬 Methodology"
        ])
        
        with tab1:
            self.render_technology_analysis()
        
        with tab2:
            self.render_location_analysis()
        
        with tab3:
            self.render_strategic_insights()
        
        with tab4:
            self.render_grid_infrastructure_analysis()
        
        with tab5:
            self.render_raw_data()
        
        with tab6:
            self.render_methodology()

def main():
    """Main function to run the dashboard."""
    try:
        dashboard = OffshoreWindDashboard()
        dashboard.run()
    except Exception as e:
        st.error(f"Error running dashboard: {e}")

if __name__ == "__main__":
    main() 