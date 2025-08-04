# 🌍 Field Reports Geolocation Extraction Pipeline

<div align="center">

![IFRC Logo](https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/IFRC_logo_2020.svg/369px-IFRC_logo_2020.svg.png?20220328112632)

**Automated extraction and enrichment of geographic locations from IFRC Field Reports**

[![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green?logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Replit](https://img.shields.io/badge/Deploy%20on-Any%20Platform-orange?logo=python&logoColor=white)](https://python.org)
[![OpenAI](https://img.shields.io/badge/AI-OpenAI%20GPT-purple?logo=openai&logoColor=white)](https://openai.com)
[![GeoNames](https://img.shields.io/badge/GeoData-GeoNames%20API-red?logo=globe&logoColor=white)](https://geonames.org)

</div>

## 📖 What This Does

This pipeline automatically processes IFRC Field Reports (from the past week) to extract and enrich geographic location data. It helps humanitarian organizations better understand where disasters are happening and what locations are affected.

1. **Fetches** field reports from IFRC GO API (one week old reports)
2. **Extracts** location mentions using AI (OpenAI GPT)
3. **Enriches** locations with detailed geographic data (GeoNames)
4. **Stores** everything in organized JSON files
5. **Provides** web interface for easy access

## 🚀 Quick Start

### 1. **Clone the Repository**
```bash
git clone https://github.com/arunissun/Field-Report-Geo-Location-Extraction.git
cd Field-Report-Geo-Location-Extraction
```

### 2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 3. **Set Up Environment**
Create a `.env` file in the project root:
```env
GO_AUTH_TOKEN=your_ifrc_go_api_token
AZURE_OPENAI_API_KEY=your_openai_api_key
AZURE_OPENAI_ENDPOINT=your_azure_endpoint
AUTO_MODE=true
```

### 4. **Run the Pipeline**
```bash
# Interactive mode (manual control)
python main.py

# Web service mode (HTTP endpoints)
python web_runner.py

# Direct enrichment (after main.py)
python final_run.py
```

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Web Framework** | ![Flask](https://img.shields.io/badge/-Flask-000000?logo=flask) | HTTP API and web interface |
| **AI Processing** | ![OpenAI](https://img.shields.io/badge/-OpenAI-412991?logo=openai) | Location extraction from text |
| **Geographic Data** | ![GeoNames](https://img.shields.io/badge/-GeoNames-4285F4?logo=globe) | Location enrichment and validation |
| **Data Source** | ![IFRC](https://img.shields.io/badge/-IFRC%20GO%20API-E31837) | Field reports and disaster data |
| **Deployment** | ![Python](https://img.shields.io/badge/-Self%20Hosted-blue?logo=python) | Local or cloud deployment |
| **Language** | ![Python](https://img.shields.io/badge/-Python-3776AB?logo=python) | Core programming language |

## 📊 Data Flow & Architecture

###  Core Files Explained

#### **Main Processing Scripts**
- **`main.py`** - Primary entry point that orchestrates the entire field reports processing
  - Fetches reports from IFRC GO API
  - Extracts location mentions using AI
  - Saves processed data to JSON files
  - Supports both interactive and automatic modes

- **`final_run.py`** - Geographic enrichment processor
  - Takes location extractions from main.py
  - Enriches locations with detailed GeoNames data
  - Adds coordinates, administrative boundaries, and geographic context

- **`web_runner.py`** - Web service interface
  - Provides HTTP endpoints for remote execution
  - Enables pipeline triggering via web requests
  - Serves processed data files for download
  - Includes health monitoring and logging endpoints

#### **Source Modules (`src/` folder)**
- **`go_api_client.py`** - IFRC GO API integration
  - Handles authentication and API communication with IFRC GO platform
  - Manages rate limiting and error handling for API requests
  - Fetches field reports with pagination support and data validation

- **`data_processor.py`** - AI-powered location extraction orchestrator
  - Coordinates the entire location extraction pipeline
  - Uses ChatGPT 3.5 Turbo for intelligent text analysis
  - Manages processing workflow and error handling

- **`location_extractor.py`** - Core AI location extraction engine
  - Implements ChatGPT 3.5 Turbo integration for location identification
  - Identifies geographic mentions in disaster reports with confidence scoring
  - Processes natural language text to extract structured location data

- **`json_manager.py`** - Data persistence and management
  - Handles JSON file operations for all data types
  - Manages data deduplication and integrity checks
  - Provides unified interface for data storage and retrieval

- **`geonames_enricher.py`** - Geographic data enrichment
  - Integrates with GeoNames API for detailed location information
  - Adds coordinates, administrative boundaries, and geographic context
  - Validates and standardizes location names with official geographic data

- **`config.py`** - Configuration management
  - Centralizes all application settings and API configurations
  - Manages environment variables and default values
  - Provides configuration validation and error handling

- **`rate_limiter.py`** - API rate limiting and throttling
  - Implements intelligent rate limiting for external API calls
  - Prevents API quota exhaustion and manages request timing
  - Supports different rate limits for different API endpoints

- **`country_manager.py`** - Country-specific data handling
  - Manages country codes, names, and administrative divisions
  - Provides country validation and standardization functions
  - Handles ISO country code conversions and mappings

- **`country_associator.py`** - Location-to-country association logic
  - Associates extracted locations with their respective countries
  - Uses ChatGPT 3.5 Turbo for intelligent country assignment
  - Handles multi-country scenarios and ambiguous location names

- **`location_manager.py`** - Location data structure management
  - Manages structured location data formats and schemas
  - Provides location data validation and transformation utilities
  - Handles location hierarchies (country → state → city)

- **`geographic_validator.py`** - Geographic data validation
  - Validates extracted locations against known geographic databases
  - Performs consistency checks and geographic relationship validation
  - Identifies and flags potentially incorrect location associations

### 📊 Data Structure & Flow

#### **Input Data (`data/raw/`)**
- **`all_raw_reports.json`** - Complete collection of field reports from IFRC GO API
  ```json
  {
    "go_api_id": 12345,
    "title": "Earthquake Response - Turkey",
    "summary": "Emergency response in affected regions...",
    "country_iso3": "TUR",
    "disaster_type": "Earthquake",
    "created_at": "2024-01-15T10:30:00Z",
    "raw_content": "Full report text with location mentions..."
  }
  ```

#### **Processed Data (`data/processed/`)**
- **`all_processed_reports.json`** - Cleaned and structured field reports
  ```json
  {
    "go_api_id": 12345,
    "title": "Earthquake Response - Turkey",
    "summary": "Emergency response in affected regions...",
    "country_iso3": "TUR",
    "locations_extracted": true,
    "processing_timestamp": "2024-01-15T11:00:00Z",
    "ai_processing_notes": "Successfully extracted 15 location mentions"
  }
  ```

#### **Extracted Data (`data/extracted/`)**
- **`location_extraction_results.json`** - AI-extracted location mentions
  ```json
  {
    "field_report_id": 12345,
    "extracted_locations": {
      "countries": ["Turkey"],
      "states": ["Hatay Province", "Kahramanmaras"],
      "cities": ["Antakya", "Kahramanmaras City", "Iskenderun"],
      "confidence_score": 0.95,
      "extraction_method": "Azure OpenAI GPT-3.5"
    }
  }
  ```

- **`country_associations.json`** - Location-to-country mappings
  ```json
  {
    "field_report_id": 12345,
    "countries": ["Turkey"],
    "turkey_states": ["Hatay Province", "Kahramanmaras"],
    "turkey_cities": ["Antakya", "Kahramanmaras City"],
    "confidence_notes": "High confidence based on administrative boundaries"
  }
  ```

- **`geonames_enriched_associations.json`** - Fully enriched geographic data
  ```json
  {
    "field_report_id": 12345,
    "locations": [
      {
        "name": "Antakya",
        "geonames_id": 323776,
        "country_code": "TR",
        "admin1": "Hatay Province",
        "latitude": 36.20895,
        "longitude": 36.15996,
        "population": 210000,
        "feature_class": "P",
        "feature_code": "PPLA"
      }
    ]
  }
  ```

#### **Processing Logs (`data/logs/`)**
- **`processing_log_YYYYMMDD_HHMMSS.json`** - Detailed execution logs
  ```json
  {
    "timestamp": "2024-01-15T10:30:00Z",
    "total_reports_processed": 25,
    "new_reports_added": 5,
    "locations_extracted": 48,
    "processing_duration": "00:05:23",
    "errors": [],
    "api_calls_made": 12
  }
  ```

## 🌐 Web Access

**Deployment URL:** https://a1bf29b1-e0c7-4497-be02-3a0e5d7f681e-00-3e1832oiqv2xk.janeway.replit.dev/

To run the program and access the data, go to the deployment URL and sign in with username and password.

**For username and password, IFRC staff should contact:** arun.gandhi@ifrc.org



## 📁 Project Structure

The pipeline processes IFRC field reports that are 15 days old, extracting geographic information and enriching it with detailed location data.

## 🌐 External API Endpoints

This pipeline integrates with two main external APIs:

### 🏥 IFRC GO API
- **Base URL**: `https://goadmin.ifrc.org/api/v2/`
- **Endpoint Used**: `field-reports/`
- **Purpose**: Fetches humanitarian field reports from the past 7 days
- **Authentication**: Bearer token via `GO_AUTH_TOKEN` environment variable
- **Data Retrieved**: Disaster reports, summaries, affected countries, timestamps
- **Rate Limiting**: Built-in delays to respect API limits

### 🗺️ GeoNames API
- **Base URL**: `http://api.geonames.org/searchJSON`
- **Purpose**: Enriches extracted locations with detailed geographic data
- **Authentication**: Username via `GEONAMES_USERNAME` environment variable
- **Data Retrieved**: Coordinates, population, administrative divisions, feature codes
- **Rate Limiting**: 1-second delay between requests to prevent overwhelming the service
- **Free Tier**: Up to 1,000 requests per hour

Both APIs are accessed using secure HTTP requests with proper error handling and retry mechanisms.

## 🔧 Configuration

### Execution Modes

**Automatic Mode** (Default for web service):
```bash
export AUTO_MODE=true
python main.py  # Runs without user interaction
```

**Interactive Mode** (For development):
```bash
python main.py  # Shows menu with options
```

### Environment Variables

Create a `.env` file in the project root with these variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `GO_AUTH_TOKEN` | ✅ | IFRC GO API authentication token |
| `AZURE_OPENAI_API_KEY` | ✅ | OpenAI API key for location extraction |
| `AZURE_OPENAI_ENDPOINT` | ✅ | Azure OpenAI service endpoint |
| `GEONAMES_USERNAME` | ✅ | GeoNames API username for geographic enrichment |
| `FLASK_SECRET_KEY` | 🔒 | Secret key for web session security |
| `ADMIN_PASSWORD` | 🔒 | Password for admin user web access |
| `IFRC_PASSWORD` | 🔒 | Password for IFRC staff web access |
| `AUTO_MODE` | ⚙️ | Set to 'true' for automated execution |

## 📈 Features

### ✨ Core Capabilities

- 🧠 **AI-Powered**: Uses ChatGPT 3.5 turbo for intelligent location extraction
- 🌍 **Geographic Enrichment**: Detailed location data from GeoNames
- 📊 **Web Dashboard**: Easy-to-use interface for monitoring
- 💾 **Data Persistence**: All results saved and downloadable
- 🔄 **Real-time Processing**: Process reports as they become available

### 🛡️ Reliability Features
- ⚡ **Rate Limiting**: Respects API limits
- 🔁 **Error Handling**: Graceful failure recovery
- 📝 **Comprehensive Logging**: Detailed execution logs
- 🏥 **Health Monitoring**: Service status endpoints

## 🤝 Contributing

This project supports humanitarian efforts by the International Federation of Red Cross and Red Crescent Societies (IFRC). 

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/arunissun/Field-Report-Geo-Location-Extraction.git
   cd Field-Report-Geo-Location-Extraction
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   - Create a `.env` file in the project root
   - Add your API keys and configuration

4. **Run the pipeline**
   ```bash
   # First, run main.py to process field reports
   python main.py
   
   # Then run final_run.py to enrich with GeoNames data
   python final_run.py
   ```

## 📄 License

This project is developed to support humanitarian operations and disaster response efforts.

## 🆘 Support

For questions or issues:

- **Check Processing Logs**: Review files in `data/logs/` folder
- **Monitor Service Health**: Use `/status` endpoint when running web service
- **Examine Console Output**: Check terminal output for real-time processing information
- **Validate Environment**: Ensure all required API keys are set in `.env` file

### Common Issues

- **API Authentication**: Verify `GO_AUTH_TOKEN` and `AZURE_OPENAI_API_KEY` are valid
- **Missing Dependencies**: Run `pip install -r requirements.txt`
- **Data Folder Permissions**: Ensure write access to `data/` directory
- **Network Connectivity**: Check internet connection for API access

---

<div align="center">

**Built with ❤️ for humanitarian response**

*Helping IFRC and humanitarian organizations better understand disaster-affected locations*

</div>
