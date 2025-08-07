# Real Data Setup Guide for Con Edison Strategic Intelligence Platform

This guide explains how to configure and use real data sources in the Con Edison Strategic Intelligence Platform.

## Current Real Data Status

The application is already configured with real data sources and contains:
- **124 articles** from Renewable Energy World about offshore wind developments
- **Con Edison investment criteria** from `config/conedison_projects.json`
- **Strategic analysis data** from multiple sources

## Data Sources Configuration

### 1. **News Sources** (Already Configured)

The application scrapes real-time data from:

- **Renewable Energy World**: Offshore wind industry news
- **NYSERDA**: New York State Energy Research and Development Authority
- **BOEM**: Bureau of Ocean Energy Management
- **Con Edison Transmission**: Utility-specific news
- **Equinor US**: Offshore wind developer news
- **Ørsted US**: Offshore wind developer news

### 2. **Investment Databases** (Configured)

- **OpenVC**: Climate tech investors database
- **FindFunding.vc**: Funding opportunities database

### 3. **API Sources** (Optional)

- **PitchBook**: Investment data (requires API key)
- **Crunchbase**: Company data (requires API key)

## How to Enable Real Data Collection

### Step 1: Run the Enhanced Scraper

```bash
# Run the enhanced scraper to collect real data
python3 enhanced_scraper.py
```

### Step 2: Process the Data

```bash
# Run the analyzer to process collected data
python3 analyzer.py
```

### Step 3: Launch the Dashboard

```bash
# Start the Streamlit dashboard with real data
streamlit run app.py
```

## Adding New Data Sources

### 1. **Add News Sources**

Edit `config/sources.json` and add new sources to the `news_sources` array:

```json
{
  "name": "Your Source Name",
  "url": "https://your-source-url.com",
  "category": "industry_news",
  "selectors": {
    "articles": ".article, .news-item",
    "title": "h1, h2, h3, .title",
    "link": "a",
    "content": ".content, .body, p",
    "date": ".date, .published"
  }
}
```

### 2. **Add API Sources**

For API-based sources, add to the `api_sources` array:

```json
{
  "name": "Your API Source",
  "url": "https://api.your-source.com/v1/endpoint",
  "category": "investment_data",
  "requires_auth": true,
  "api_key_env": "YOUR_API_KEY_ENV"
}
```

Then set the environment variable:
```bash
export YOUR_API_KEY_ENV="your_api_key_here"
```

## Data Quality and Validation

### 1. **Check Data Quality**

The application includes data quality checks:
- Duplicate detection
- Content relevance filtering
- Funding amount extraction
- Utility content detection

### 2. **Monitor Data Collection**

Check the logs for data collection status:
```bash
tail -f enhanced_scraper.log
```

### 3. **Validate Data**

Review collected data in the dashboard:
- Navigate to the "Data Overview" section
- Check data freshness and completeness
- Verify source attribution

## Environment Variables

Set these environment variables for optimal data collection:

```bash
# Data directory
export DATA_DIR="./data"

# Raw data file
export RAW_DATA_FILE="raw_data.csv"

# API keys (if using API sources)
export PITCHBOOK_API_KEY="your_pitchbook_key"
export CRUNCHBASE_API_KEY="your_crunchbase_key"

# OpenAI API key (for AI analysis)
export OPENAI_API_KEY="your_openai_key"
```

## Troubleshooting

### Common Issues

1. **No Data Collected**
   - Check internet connectivity
   - Verify source URLs are accessible
   - Review website structure changes

2. **Rate Limiting**
   - The enhanced scraper includes rate limiting
   - Adjust `min_delay` and `max_delay` in the scraper

3. **API Authentication**
   - Ensure API keys are set correctly
   - Check API rate limits and quotas

### Debug Mode

Enable debug logging:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Data Refresh Schedule

### Recommended Schedule

- **News Sources**: Daily
- **Investment Data**: Weekly
- **Strategic Analysis**: Monthly

### Automated Refresh

Set up a cron job for automated data collection:

```bash
# Add to crontab
0 6 * * * cd /path/to/windenergy && python3 enhanced_scraper.py
```

## Data Sources by Category

### Government Sources
- **NYSERDA**: New York state energy programs
- **BOEM**: Federal offshore wind regulations
- **DOE**: Department of Energy announcements

### Industry News
- **Renewable Energy World**: Offshore wind industry
- **Utility Dive**: Utility industry news
- **Greentech Media**: Clean energy technology

### Developer Sources
- **Equinor**: Offshore wind developer
- **Ørsted**: Offshore wind developer
- **Vineyard Wind**: Offshore wind developer

### Investment Sources
- **PitchBook**: Investment data
- **Crunchbase**: Company data
- **OpenVC**: Climate tech investors

## Best Practices

1. **Respect Rate Limits**: Always implement rate limiting
2. **Validate Data**: Check data quality before analysis
3. **Monitor Sources**: Regularly verify source accessibility
4. **Backup Data**: Keep historical data for trend analysis
5. **Document Changes**: Track source configuration changes

## Support

For issues with data collection or configuration:
1. Check the logs in `enhanced_scraper.log`
2. Verify source URLs are accessible
3. Review website structure changes
4. Test individual sources manually

The application is designed to work with real data sources and provides comprehensive tools for data collection, analysis, and visualization. 