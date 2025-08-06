#!/usr/bin/env python3
"""
Con Edison Strategic Opportunities Matrix
A comprehensive dashboard for identifying and analyzing investment opportunities
aligned with Con Edison's strategic priorities.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="Con Edison Strategic Opportunities Matrix",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79 0%, #2980b9 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2980b9;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    .opportunity-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .sweet-spot {
        background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2980b9;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

class ConEdisonOpportunitiesMatrix:
    def __init__(self):
        """Initialize the dashboard with configuration."""
        self.data_dir = "data"
        self.analyzed_data_file = "raw_data.csv"
        
        # Investment thesis tags for Con Edison
        self.investment_thesis_tags = [
            "Grid Infrastructure & Transmission",
            "Energy Storage Solutions", 
            "Smart Grid Technologies",
            "Renewable Integration",
            "Demand Response & Load Management",
            "Microgrid Development",
            "EV Infrastructure"
        ]
        
        # TRL mapping for technology readiness
        self.trl_mapping = {
            'seed': 3,
            'series_a': 5, 
            'series_b': 6,
            'series_c': 7,
            'growth': 8,
            'other': 4
        }
        
        # Load data
        self.load_data()
    
    def load_data(self):
        """Load and process data with robust error handling."""
        try:
            analyzed_file = os.path.join(self.data_dir, self.analyzed_data_file)
            
            if not os.path.exists(analyzed_file):
                st.error(f"❌ Data file not found: {analyzed_file}")
                st.info("Please ensure the data file exists in the data/ directory.")
                st.stop()
            
            # Load CSV with explicit data types
            self.df = pd.read_csv(analyzed_file)
            
            # Ensure all required columns exist
            required_columns = ['title', 'content', 'source_name', 'funding_amount', 'funding_stage']
            missing_columns = [col for col in required_columns if col not in self.df.columns]
            
            if missing_columns:
                st.error(f"❌ Missing required columns: {missing_columns}")
                st.info("Available columns: " + ", ".join(self.df.columns.tolist()))
                st.stop()
            
            # Safely handle NaN values and convert to strings
            for col in ['funding_amount', 'funding_stage', 'title', 'source_name', 'content']:
                self.df[col] = self.df[col].fillna('').astype(str)
            
            # Convert funding amounts safely
            self.df['total_funding_amount_numeric'] = self.df['funding_amount'].apply(self._safe_funding_conversion)
            
            # Convert date safely
            self.df['date'] = pd.to_datetime(self.df['date'], errors='coerce')
            
            # Generate strategic scores
            self._generate_strategic_scores()
            
            st.success(f"✅ Successfully loaded {len(self.df)} opportunities")
            
        except Exception as e:
            st.error(f"❌ Error loading data: {str(e)}")
            st.info("Please check the data file format and try again.")
            st.stop()
    
    def _safe_funding_conversion(self, funding_str):
        """Safely convert funding amounts to numeric values."""
        if pd.isna(funding_str) or funding_str == '' or funding_str == 'nan':
            return 0
        try:
            # Handle common funding amount formats
            cleaned = str(funding_str).strip()
            if not cleaned:
                return 0
            
            # Replace common abbreviations
            cleaned = cleaned.replace('b', '000000000').replace('B', '000000000')
            cleaned = cleaned.replace('m', '000000').replace('M', '000000')
            cleaned = cleaned.replace('k', '000').replace('K', '000')
            
            # Remove any remaining non-numeric characters except decimal points
            cleaned = ''.join(c for c in cleaned if c.isdigit() or c == '.')
            
            if not cleaned:
                return 0
                
            result = pd.to_numeric(cleaned, errors='coerce')
            return result if pd.notna(result) else 0
            
        except Exception:
            return 0
    
    def _generate_strategic_scores(self):
        """Generate strategic fit scores and TRL levels."""
        try:
            # Calculate strategic fit scores
            self.df['strategic_fit_score'] = self.df.apply(self._calculate_strategic_fit, axis=1)
            
            # Calculate TRL levels
            self.df['trl_level'] = self.df.apply(self._calculate_trl, axis=1)
            
            # Assign investment thesis tags
            self.df['investment_thesis_tag'] = self.df.apply(self._assign_thesis_tag, axis=1)
            
        except Exception as e:
            st.error(f"❌ Error generating strategic scores: {str(e)}")
            st.stop()
    
    def _calculate_strategic_fit(self, row):
        """Calculate strategic fit score based on content analysis."""
        content = row['content'].lower()
        title = row['title'].lower()
        
        score = 30  # Base score
        
        # Grid infrastructure and transmission (highest priority)
        if any(term in content or term in title for term in ['grid', 'transmission', 'infrastructure', 'power line']):
            score += 40
        
        # Energy storage
        if any(term in content or term in title for term in ['storage', 'battery', 'energy storage', 'lithium']):
            score += 35
        
        # Smart grid
        if any(term in content or term in title for term in ['smart grid', 'digital', 'automation', 'iot']):
            score += 30
        
        # Renewable integration
        if any(term in content or term in title for term in ['renewable', 'solar', 'wind', 'integration']):
            score += 25
        
        # Demand response
        if any(term in content or term in title for term in ['demand', 'response', 'load', 'peak']):
            score += 20
        
        # Microgrid
        if any(term in content or term in title for term in ['microgrid', 'distributed', 'local']):
            score += 20
        
        # EV infrastructure
        if any(term in content or term in title for term in ['ev', 'electric vehicle', 'charging', 'electric car']):
            score += 15
        
        return min(score, 100)
    
    def _calculate_trl(self, row):
        """Calculate Technology Readiness Level based on funding stage."""
        funding_stage = str(row['funding_stage']).lower()
        
        if 'seed' in funding_stage:
            return 3
        elif 'series a' in funding_stage:
            return 5
        elif 'series b' in funding_stage:
            return 6
        elif 'series c' in funding_stage:
            return 7
        elif 'growth' in funding_stage:
            return 8
        else:
            return 4
    
    def _assign_thesis_tag(self, row):
        """Assign investment thesis tag based on content analysis."""
        content = row['content'].lower()
        title = row['title'].lower()
        
        if any(term in content or term in title for term in ['grid', 'transmission', 'infrastructure']):
            return "Grid Infrastructure & Transmission"
        elif any(term in content or term in title for term in ['storage', 'battery', 'energy storage']):
            return "Energy Storage Solutions"
        elif any(term in content or term in title for term in ['smart grid', 'digital', 'automation']):
            return "Smart Grid Technologies"
        elif any(term in content or term in title for term in ['renewable', 'solar', 'wind', 'integration']):
            return "Renewable Integration"
        elif any(term in content or term in title for term in ['demand', 'response', 'load']):
            return "Demand Response & Load Management"
        elif any(term in content or term in title for term in ['microgrid', 'distributed']):
            return "Microgrid Development"
        elif any(term in content or term in title for term in ['ev', 'electric vehicle', 'charging']):
            return "EV Infrastructure"
        else:
            return "Other"
    
    def render_header(self):
        """Render the dashboard header with key metrics."""
        st.markdown("""
        <div class="main-header">
            <h1>⚡ Con Edison Strategic Opportunities Matrix</h1>
            <p>Identify and prioritize investment opportunities aligned with Con Edison's strategic priorities</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            high_fit = len(self.df[self.df['strategic_fit_score'] >= 70])
            st.metric("🎯 High Strategic Fit", f"{high_fit} opportunities", 
                     f"{high_fit - len(self.df[self.df['strategic_fit_score'] >= 70])}")
        
        with col2:
            commercial_ready = len(self.df[self.df['trl_level'] >= 7])
            st.metric("🚀 Commercial Ready (TRL 7-9)", f"{commercial_ready} opportunities")
        
        with col3:
            sweet_spot = len(self.df[(self.df['strategic_fit_score'] >= 70) & (self.df['trl_level'] >= 7)])
            st.metric("💎 Sweet Spot Opportunities", f"{sweet_spot} opportunities")
        
        with col4:
            total_opportunities = len(self.df)
            st.metric("📊 Total Opportunities", f"{total_opportunities} analyzed")
    
    def render_opportunities_quadrant(self):
        """Render the main opportunities quadrant visualization."""
        st.markdown("## 🎯 Strategic Opportunities Quadrant")
        st.markdown("**X-Axis:** Technology Readiness Level (TRL) | **Y-Axis:** Strategic Fit Score")
        
        # Filter by investment thesis
        selected_thesis = st.selectbox(
            "Filter by Investment Thesis:",
            ["All Areas"] + self.investment_thesis_tags,
            help="Select a specific investment area to focus on"
        )
        
        # Filter data
        if selected_thesis == "All Areas":
            filtered_df = self.df
        else:
            filtered_df = self.df[self.df['investment_thesis_tag'] == selected_thesis]
        
        if len(filtered_df) == 0:
            st.warning("No opportunities found for the selected criteria.")
            return
        
        # Create scatter plot
        fig = px.scatter(
            filtered_df,
            x='trl_level',
            y='strategic_fit_score',
            size='total_funding_amount_numeric',
            color='investment_thesis_tag',
            hover_data=['title', 'source_name', 'content'],
            title="Strategic Opportunities Matrix",
            labels={
                'trl_level': 'Technology Readiness Level (TRL)',
                'strategic_fit_score': 'Strategic Fit Score',
                'investment_thesis_tag': 'Investment Thesis'
            }
        )
        
        # Add quadrant lines and labels
        fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="High Strategic Fit")
        fig.add_vline(x=7, line_dash="dash", line_color="red", annotation_text="Commercial Ready")
        
        # Add quadrant labels
        fig.add_annotation(x=8.5, y=85, text="💎 Sweet Spot<br>(High Fit + Ready)", 
                          showarrow=False, font=dict(color="green", size=14))
        fig.add_annotation(x=8.5, y=35, text="🔬 Research<br>(High Fit + Early)", 
                          showarrow=False, font=dict(color="orange", size=14))
        fig.add_annotation(x=3, y=85, text="🚀 Emerging<br>(High Fit + Developing)", 
                          showarrow=False, font=dict(color="blue", size=14))
        fig.add_annotation(x=3, y=35, text="📊 Monitor<br>(Low Fit + Early)", 
                          showarrow=False, font=dict(color="gray", size=14))
        
        fig.update_layout(
            width=800,
            height=600,
            xaxis=dict(range=[1, 9]),
            yaxis=dict(range=[0, 100])
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Sweet spot opportunities
        sweet_spot_df = filtered_df[(filtered_df['strategic_fit_score'] >= 70) & (filtered_df['trl_level'] >= 7)]
        
        if len(sweet_spot_df) > 0:
            st.markdown("### 💎 Sweet Spot Opportunities")
            st.markdown("These opportunities have both high strategic fit and commercial readiness:")
            
            for idx, row in sweet_spot_df.head(5).iterrows():
                with st.expander(f"🎯 {row['title'][:60]}..."):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"**Strategic Fit:** {row['strategic_fit_score']}/100")
                        st.write(f"**TRL Level:** {row['trl_level']}/9")
                        st.write(f"**Investment Thesis:** {row['investment_thesis_tag']}")
                        st.write(f"**Source:** {row['source_name']}")
                    with col2:
                        st.write(f"**Funding:** ${row['total_funding_amount_numeric']:,.0f}" if row['total_funding_amount_numeric'] > 0 else "**Funding:** Not specified")
                    
                    st.markdown("**Strategic Summary:**")
                    st.write(row['content'][:300] + "..." if len(row['content']) > 300 else row['content'])
    
    def render_opportunity_details(self):
        """Render detailed opportunity analysis."""
        st.markdown("## 🔍 Opportunity Details")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            min_strategic_fit = st.slider("Minimum Strategic Fit Score:", 0, 100, 50)
        
        with col2:
            min_trl = st.slider("Minimum TRL Level:", 1, 9, 4)
        
        with col3:
            selected_theses = st.multiselect(
                "Investment Thesis Areas:",
                self.investment_thesis_tags,
                default=self.investment_thesis_tags[:3]
            )
        
        # Filter data
        filtered_df = self.df[
            (self.df['strategic_fit_score'] >= min_strategic_fit) &
            (self.df['trl_level'] >= min_trl) &
            (self.df['investment_thesis_tag'].isin(selected_theses))
        ]
        
        st.markdown(f"**Found {len(filtered_df)} opportunities matching your criteria**")
        
        # Display opportunities
        for idx, row in filtered_df.head(10).iterrows():
            with st.expander(f"📋 {row['title'][:80]}..."):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**{row['title']}**")
                    st.write(f"**Source:** {row['source_name']}")
                    st.write(f"**Investment Thesis:** {row['investment_thesis_tag']}")
                    
                    # Progress bars for scores
                    st.write("**Strategic Fit Score:**")
                    st.progress(row['strategic_fit_score'] / 100)
                    st.write(f"{row['strategic_fit_score']}/100")
                    
                    st.write("**Technology Readiness Level:**")
                    st.progress(row['trl_level'] / 9)
                    st.write(f"TRL {row['trl_level']}/9")
                
                with col2:
                    if row['total_funding_amount_numeric'] > 0:
                        st.metric("Funding", f"${row['total_funding_amount_numeric']:,.0f}")
                    else:
                        st.metric("Funding", "Not specified")
                    
                    # Color-coded priority
                    if row['strategic_fit_score'] >= 70 and row['trl_level'] >= 7:
                        st.markdown('<div class="sweet-spot">💎 Sweet Spot</div>', unsafe_allow_html=True)
                    elif row['strategic_fit_score'] >= 70:
                        st.markdown('<div style="background: #f39c12; color: white; padding: 0.5rem; border-radius: 5px; font-weight: bold;">🎯 High Priority</div>', unsafe_allow_html=True)
                    elif row['trl_level'] >= 7:
                        st.markdown('<div style="background: #3498db; color: white; padding: 0.5rem; border-radius: 5px; font-weight: bold;">🚀 Commercial Ready</div>', unsafe_allow_html=True)
                
                st.markdown("**Strategic Analysis:**")
                st.write(row['content'][:500] + "..." if len(row['content']) > 500 else row['content'])
    
    def render_strategic_insights(self):
        """Render strategic insights and analytics."""
        st.markdown("## 📈 Strategic Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Investment Thesis Distribution")
            thesis_counts = self.df['investment_thesis_tag'].value_counts()
            fig = px.pie(
                values=thesis_counts.values,
                names=thesis_counts.index,
                title="Opportunities by Investment Thesis"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### Strategic Fit Score Distribution")
            fig = px.histogram(
                self.df,
                x='strategic_fit_score',
                nbins=20,
                title="Distribution of Strategic Fit Scores"
            )
            fig.update_layout(xaxis_title="Strategic Fit Score", yaxis_title="Number of Opportunities")
            st.plotly_chart(fig, use_container_width=True)
        
        # Top opportunities
        st.markdown("### 🏆 Top 10 Opportunities by Strategic Fit")
        top_opportunities = self.df.nlargest(10, 'strategic_fit_score')
        
        for idx, row in top_opportunities.iterrows():
            with st.expander(f"#{idx+1} - {row['title'][:60]}..."):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Strategic Fit", f"{row['strategic_fit_score']}/100")
                
                with col2:
                    st.metric("TRL Level", f"{row['trl_level']}/9")
                
                with col3:
                    st.metric("Investment Thesis", row['investment_thesis_tag'])
                
                st.write(f"**Source:** {row['source_name']}")
                st.write(f"**Summary:** {row['content'][:200]}...")
    
    def render_heat_map(self):
        """Render investment opportunities heat map by region and strategic fit with interactive filtering."""
        st.markdown("## 🗺️ Investment Opportunities Heat Map")
        
        # Create geographic regions based on content analysis
        def extract_region(content, title):
            """Extract geographic region from content."""
            text = (content + " " + title).lower()
            
            # Northeast region (Con Edison's primary market)
            if any(term in text for term in ['new york', 'nyc', 'manhattan', 'brooklyn', 'queens', 'bronx', 'staten island', 'long island', 'upstate ny', 'new jersey', 'nj', 'connecticut', 'ct', 'massachusetts', 'ma', 'rhode island', 'ri', 'vermont', 'vt', 'maine', 'me', 'new hampshire', 'nh']):
                return 'Northeast'
            
            # Mid-Atlantic region
            elif any(term in text for term in ['pennsylvania', 'pa', 'delaware', 'de', 'maryland', 'md', 'virginia', 'va', 'west virginia', 'wv', 'washington dc', 'dc']):
                return 'Mid-Atlantic'
            
            # Southeast region
            elif any(term in text for term in ['florida', 'fl', 'georgia', 'ga', 'south carolina', 'sc', 'north carolina', 'nc', 'alabama', 'al', 'mississippi', 'ms', 'tennessee', 'tn', 'kentucky', 'ky']):
                return 'Southeast'
            
            # Midwest region
            elif any(term in text for term in ['illinois', 'il', 'indiana', 'in', 'michigan', 'mi', 'ohio', 'oh', 'wisconsin', 'wi', 'minnesota', 'mn', 'iowa', 'ia', 'missouri', 'mo']):
                return 'Midwest'
            
            # West Coast region
            elif any(term in text for term in ['california', 'ca', 'oregon', 'or', 'washington', 'wa', 'nevada', 'nv', 'alaska', 'ak', 'hawaii', 'hi']):
                return 'West Coast'
            
            # Texas region (major energy market)
            elif any(term in text for term in ['texas', 'tx', 'austin', 'houston', 'dallas', 'san antonio']):
                return 'Texas'
            
            # National/Global (default)
            else:
                return 'National/Global'
        
        # Add region column
        self.df['region'] = self.df.apply(lambda row: extract_region(row['content'], row['title']), axis=1)
        
        # Interactive Filter Controls
        st.markdown("### 🎛️ Filter Controls")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Strategic fit score filter
            min_score, max_score = st.slider(
                "Strategic Fit Score Range",
                min_value=0,
                max_value=100,
                value=(30, 100),
                help="Filter opportunities by strategic fit score"
            )
            
            # Time period filter
            time_period = st.selectbox(
                "Time Period",
                options=["All time", "Last 30 days", "Last 90 days", "Last 6 months", "Last year"],
                help="Filter by when opportunities were identified"
            )
        
        with col2:
            # Investment thesis filter
            available_theses = sorted(self.df['investment_thesis_tag'].unique())
            selected_theses = st.multiselect(
                "Investment Theses",
                options=available_theses,
                default=available_theses,
                help="Select which investment theses to include"
            )
            
            # TRL level filter
            trl_options = ["All", "Early Stage (1-3)", "Mid Stage (4-6)", "Late Stage (7-9)"]
            trl_filter = st.selectbox(
                "TRL Level",
                options=trl_options,
                help="Filter by technology readiness level"
            )
        
        with col3:
            # Funding amount filter
            min_funding = st.number_input(
                "Minimum Funding ($M)",
                min_value=0,
                max_value=1000,
                value=0,
                help="Filter by minimum funding amount in millions"
            )
            
            # Region filter
            available_regions = sorted(self.df['region'].unique())
            selected_regions = st.multiselect(
                "Regions",
                options=available_regions,
                default=available_regions,
                help="Select which regions to include"
            )
        
        # Apply filters
        filtered_df = self.apply_heat_map_filters(
            min_score, max_score, time_period, selected_theses, 
            trl_filter, min_funding, selected_regions
        )
        
        # Show filter summary
        st.markdown(f"**📊 Showing {len(filtered_df)} opportunities after filtering**")
        
        if len(filtered_df) == 0:
            st.warning("⚠️ No opportunities match the current filters. Try adjusting your criteria.")
            return
        
        # Create heat map data from filtered data
        heat_data = filtered_df.groupby(['region', 'investment_thesis_tag']).agg({
            'strategic_fit_score': 'mean',
            'total_funding_amount_numeric': 'sum',
            'title': 'count'
        }).reset_index()
        
        heat_data.columns = ['Region', 'Investment Thesis', 'Avg Strategic Fit', 'Total Funding', 'Opportunity Count']
        
        # Create the heat map
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 📊 Strategic Fit by Region & Investment Thesis")
            
            # Create pivot table for heat map
            pivot_data = heat_data.pivot(index='Region', columns='Investment Thesis', values='Avg Strategic Fit').fillna(0)
            
            # Create heat map using plotly
            fig = px.imshow(
                pivot_data,
                title="Strategic Fit Heat Map by Region and Investment Thesis",
                color_continuous_scale='RdYlGn',
                aspect='auto'
            )
            
            fig.update_layout(
                xaxis_title="Investment Thesis",
                yaxis_title="Region",
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 📈 Key Insights")
            
            # Top regions by strategic fit
            top_regions = heat_data.groupby('Region')['Avg Strategic Fit'].mean().sort_values(ascending=False)
            
            st.markdown("**Top Regions by Strategic Fit:**")
            for region, score in top_regions.head(3).items():
                st.markdown(f"• **{region}**: {score:.1f}/100")
            
            # Top investment theses
            top_theses = heat_data.groupby('Investment Thesis')['Avg Strategic Fit'].mean().sort_values(ascending=False)
            
            st.markdown("**Top Investment Theses:**")
            for thesis, score in top_theses.head(3).items():
                st.markdown(f"• **{thesis}**: {score:.1f}/100")
        
        # Regional breakdown
        st.markdown("### 🎯 Regional Investment Opportunities")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Regional funding distribution
            regional_funding = heat_data.groupby('Region')['Total Funding'].sum().sort_values(ascending=False)
            
            fig = px.bar(
                x=regional_funding.index,
                y=regional_funding.values,
                title="Total Investment by Region",
                labels={'x': 'Region', 'y': 'Total Funding ($)'}
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Regional opportunity count
            regional_opportunities = heat_data.groupby('Region')['Opportunity Count'].sum().sort_values(ascending=False)
            
            fig = px.bar(
                x=regional_opportunities.index,
                y=regional_opportunities.values,
                title="Number of Opportunities by Region",
                labels={'x': 'Region', 'y': 'Number of Opportunities'}
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed regional analysis
        st.markdown("### 🔍 Regional Deep Dive")
        
        selected_region = st.selectbox(
            "Select a region for detailed analysis:",
            options=sorted(heat_data['Region'].unique())
        )
        
        region_data = heat_data[heat_data['Region'] == selected_region]
        
        if not region_data.empty:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_fit = region_data['Avg Strategic Fit'].mean()
                st.metric("Average Strategic Fit", f"{avg_fit:.1f}/100")
            
            with col2:
                total_funding = region_data['Total Funding'].sum()
                st.metric("Total Investment", f"${total_funding:,.0f}")
            
            with col3:
                opportunity_count = region_data['Opportunity Count'].sum()
                st.metric("Opportunities", f"{opportunity_count}")
            
            # Show top opportunities in this region
            region_opportunities = self.df[self.df['region'] == selected_region].nlargest(5, 'strategic_fit_score')
            
            st.markdown(f"**Top 5 Opportunities in {selected_region}:**")
            for idx, row in region_opportunities.iterrows():
                with st.expander(f"#{idx+1} - {row['title'][:50]}..."):
                    st.write(f"**Strategic Fit:** {row['strategic_fit_score']}/100")
                    st.write(f"**Investment Thesis:** {row['investment_thesis_tag']}")
                    st.write(f"**Source:** {row['source_name']}")
                    st.write(f"**Summary:** {row['content'][:150]}...")

    def apply_heat_map_filters(self, min_score, max_score, time_period, selected_theses, trl_filter, min_funding, selected_regions):
        """Apply filters to the dataset for heat map visualization."""
        filtered_df = self.df.copy()
        
        # Filter by strategic fit score
        filtered_df = filtered_df[
            (filtered_df['strategic_fit_score'] >= min_score) & 
            (filtered_df['strategic_fit_score'] <= max_score)
        ]
        
        # Filter by investment thesis
        if selected_theses:
            filtered_df = filtered_df[filtered_df['investment_thesis_tag'].isin(selected_theses)]
        
        # Filter by region
        if selected_regions:
            filtered_df = filtered_df[filtered_df['region'].isin(selected_regions)]
        
        # Filter by funding amount
        if min_funding > 0:
            filtered_df = filtered_df[filtered_df['total_funding_amount_numeric'] >= (min_funding * 1000000)]
        
        # Filter by TRL level
        if trl_filter != "All":
            if trl_filter == "Early Stage (1-3)":
                filtered_df = filtered_df[filtered_df['trl_level'].isin([1, 2, 3])]
            elif trl_filter == "Mid Stage (4-6)":
                filtered_df = filtered_df[filtered_df['trl_level'].isin([4, 5, 6])]
            elif trl_filter == "Late Stage (7-9)":
                filtered_df = filtered_df[filtered_df['trl_level'].isin([7, 8, 9])]
        
        # Filter by time period (if date column exists and is valid)
        if time_period != "All time" and 'date' in filtered_df.columns:
            try:
                from datetime import datetime, timedelta
                now = datetime.now()
                
                if time_period == "Last 30 days":
                    cutoff_date = now - timedelta(days=30)
                elif time_period == "Last 90 days":
                    cutoff_date = now - timedelta(days=90)
                elif time_period == "Last 6 months":
                    cutoff_date = now - timedelta(days=180)
                elif time_period == "Last year":
                    cutoff_date = now - timedelta(days=365)
                else:
                    cutoff_date = None
                
                if cutoff_date:
                    # Convert date column to datetime if it's not already
                    filtered_df['date'] = pd.to_datetime(filtered_df['date'], errors='coerce')
                    filtered_df = filtered_df[filtered_df['date'] >= cutoff_date]
                    
            except Exception as e:
                st.warning(f"⚠️ Date filtering not available: {str(e)}")
        
        return filtered_df

    def render_methodology(self):
        """Render methodology and explanation."""
        st.markdown("## 🔬 Methodology")
        
        st.markdown("""
        ### Strategic Fit Score (0-100)
        Opportunities are scored based on their alignment with Con Edison's strategic priorities:
        
        - **Grid Infrastructure & Transmission (40 pts)** - Direct alignment with core business
        - **Energy Storage (35 pts)** - High strategic value for grid stability
        - **Smart Grid Technologies (30 pts)** - Digital transformation focus
        - **Renewable Integration (25 pts)** - Strong alignment with clean energy goals
        - **Demand Response (20 pts)** - Load management capabilities
        - **Microgrid Development (20 pts)** - Distributed energy solutions
        - **EV Infrastructure (15 pts)** - Transportation electrification
        
        ### Technology Readiness Level (TRL 1-9)
        - **TRL 1-3:** Basic Research (Early stage, high risk)
        - **TRL 4-6:** Development & Testing (Mid-stage, moderate risk)
        - **TRL 7-9:** Commercial Ready (Proven technology, lower risk)
        
        ### Sweet Spot Definition
        Opportunities with **Strategic Fit ≥ 70** and **TRL ≥ 7** are considered "Sweet Spot" 
        opportunities - high strategic value with proven, de-risked technology.
        
        ### Geographic Analysis
        The heat map analyzes opportunities by geographic regions to identify:
        - **Regional investment hotspots** for strategic expansion
        - **Market gaps** where Con Edison could establish presence
        - **Competitive intelligence** on regional market dynamics
        """)
    
    def run(self):
        """Run the dashboard."""
        try:
            self.render_header()
            
            # Create tabs
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "🎯 Opportunities Quadrant", 
                "🗺️ Heat Map", 
                "🔍 Opportunity Details", 
                "📈 Strategic Insights", 
                "🔬 Methodology"
            ])
            
            with tab1:
                self.render_opportunities_quadrant()
            
            with tab2:
                self.render_heat_map()
            
            with tab3:
                self.render_opportunity_details()
            
            with tab4:
                self.render_strategic_insights()
            
            with tab5:
                self.render_methodology()
                
        except Exception as e:
            st.error(f"❌ Error running dashboard: {str(e)}")
            st.info("Please check the data and try again.")

def main():
    """Main function to run the dashboard."""
    try:
        dashboard = ConEdisonOpportunitiesMatrix()
        dashboard.run()
    except Exception as e:
        st.error(f"❌ Application error: {str(e)}")
        st.info("Please ensure all dependencies are installed and data files are available.")

if __name__ == "__main__":
    main() 