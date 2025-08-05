# Offshore Wind Strategic Intelligence Platform MVP

## Project Overview

This AI-powered platform tracks and analyzes key strategic developments in the Northeast offshore wind sector. The MVP's core function is to identify market gaps and project-level bottlenecks that are most relevant to utility business needs, such as grid infrastructure and transmission.

## Key Features

- **Data Collection**: Automated scraping from high-priority sources including NYSERDA, BOEM, Con Edison Transmission, and major developers
- **AI-Powered Analysis**: Custom OpenAI prompts to extract structured data and identify strategic opportunities
- **Gap Analysis**: Identifies underserved areas and strategic opportunities for utilities
- **Interactive Dashboard**: Streamlit-based visualization of findings and insights

## Project Structure

```
WindEnergy/
├── README.md                 # Project documentation
├── PROGRESS.md              # Development progress tracking
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── scraper.py               # Data collection from target sources
├── analyzer.py              # AI-powered data analysis and tagging
├── app.py                   # Streamlit dashboard
├── data/                    # Data storage directory
│   ├── raw_data.csv        # Scraped raw data
│   └── analyzed_data.csv   # AI-processed and tagged data
└── config/                  # Configuration files
    └── sources.json         # Target URLs and metadata
```

## Setup Instructions

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your OpenAI API key
OPENAI_API_KEY=your_api_key_here
```

### 3. Data Collection

```bash
# Run the scraper to collect data
python scraper.py
```

### 4. Data Analysis

```bash
# Process and tag the collected data
python analyzer.py
```

### 5. Launch Dashboard

```bash
# Start the Streamlit dashboard
streamlit run app.py
```

## Target Data Sources

### Primary Sources
- **NYSERDA**: https://www.nyserda.ny.gov/All-Programs/Offshore-Wind/Announcements-and-Events
- **BOEM**: https://www.boem.gov/renewable-energy/state-activities/new-york-bight
- **Con Edison Transmission**: https://www.conedtransmission.com/es/news-and-media-center

### Developer Sources
- **Equinor**: https://www.equinor.com/where-we-are/us-news
- **Ørsted**: https://us.orsted.com/new-york and https://us.orsted.com/news-archive

### Industry News
- **Renewable Energy World**: https://www.renewableenergyworld.com/wind-power/offshore/

## Analysis Categories

The platform categorizes developments into:

- **Grid Infrastructure & Interconnection**
- **Subsea Cables**
- **Port Infrastructure**
- **Offshore Substation Platforms**
- **Operations & Maintenance (O&M) Services**

## Strategic Focus Areas

- Grid infrastructure gaps in New York City region
- Transmission upgrade opportunities
- Cable landing site development
- HVDC converter station projects
- Clean Energy Hub initiatives

## Development Phases

### Phase 1: Foundation & Data Collection (Days 1-2)
- Environment setup and dependency installation
- Development of targeted scraper for high-priority sources
- Raw data collection and storage

### Phase 2: Tagging & Basic Analysis (Days 3-4)
- AI integration for structured data extraction
- Custom prompts for utility-specific insights
- Gap analysis and strategic opportunity identification

### Phase 3: MVP Dashboard (Days 5-6)
- Streamlit dashboard development
- Visualization of findings and insights
- Strategic intelligence presentation

## Dependencies

- `requests`: HTTP requests for web scraping
- `beautifulsoup4`: HTML parsing
- `pandas`: Data manipulation and analysis
- `streamlit`: Web application framework
- `openai`: AI-powered text analysis
- `python-dotenv`: Environment variable management

## Contributing

This is an MVP development project focused on demonstrating the core value proposition of AI-powered strategic intelligence for the offshore wind sector.

## License

This project is for internal development and demonstration purposes. 