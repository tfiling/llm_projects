# LLM Projects

## analyze_sponsors

A Python-based tool for analyzing companies' likelihood of hiring software engineers by scanning their career pages and job postings.

### Features

- Searches for company career pages using Oxylabs web scraping service
- Extracts job listings and analyzes positions
- Evaluates companies' likelihood of hiring software engineers
- Categorizes companies by industry using ML analysis
- Re-categorizes failed company analysis attempts using Claude
- Caches search results and analysis for efficiency
- Stores results in CSV format for further analysis

### Dependencies

- Python 3.11+
- Anthropic Claude API for text analysis
- Oxylabs for web scraping
- aiohttp for async HTTP requests
- Beautiful Soup for HTML parsing
- diskcache for caching results

### Project Structure

- `main.py` - Entry point and orchestration
- `careers_page.py` - Career page discovery and scraping
- `open_positions.py` - Job listing extraction
- `hiring_developers_probability.py` - Hiring likelihood analysis
- `keywords.py` - Relevant technology keyword definitions
- `utils/` - Helper functions for CSV/JSON handling
- `prompts/` - Claude API prompt templates
- `log_analysis/` - Analysis and classification tools

Results are stored in:
- `analyze_sponsors/run_outputs/<execution iteration>/positions/` - Individual CSV files with job listings
- `analyze_sponsors/run_outputs/<execution iteration>/hiring_probability/` - Analysis of hiring likelihood
- `analyze_sponsors/log_analysis/categorize_by_name_results.json` - Company categorizations

### Logging

Detailed logs are stored in `analyze_sponsors/run_outputs/logs/` with timestamp-based filenames.