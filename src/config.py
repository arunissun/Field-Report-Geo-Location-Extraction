import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_result = load_dotenv(dotenv_path)


class Config:
    """Configuration management for the field reports pipeline"""

    def __init__(self):
        # API Configuration
        self.GO_API_BASE_URL = "https://goadmin.ifrc.org/api/v2/"
        self.GO_AUTH_TOKEN = os.environ.get('GO_AUTH_TOKEN')

        # OpenAI Configuration (for future use)
        self.OPENAI_API_KEY = os.environ.get('Key')
        self.GEONAMES_USERNAME = os.environ.get('GEONAMES_USERNAME')

        # Pagination settings
        self.DEFAULT_LIMIT = 50
        self.MAX_RETRIES = 3
        self.REQUEST_TIMEOUT = 30

        # Date filtering configuration
        self.DAYS_LOOKBACK = 15  # Number of days to look back for field reports
        
        # Calculate start date dynamically - reports from the last N days
        lookback_date = datetime.now() - timedelta(days=self.DAYS_LOOKBACK)
        self.START_DATE = lookback_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Required fields from API
        self.REQUIRED_FIELDS = [
            'id', 'title', 'description', 'summary', 'country_name',
            'event_name', 'disaster_type_name'
        ]

        # File paths
        self.RAW_DATA_DIR = "data/raw"
        self.PROCESSED_DATA_DIR = "data/processed"
        self.LOGS_DIR = "data/logs"
        # Add this line after self.LOGS_DIR:
        self.EXTRACTED_DATA_DIR = "data/extracted"


        # JSON file settings
        self.BATCH_SIZE = 50  # Number of reports per JSON file

    def validate_config(self):
        """Validate that required configuration is present"""
        if not self.GO_AUTH_TOKEN:
            raise ValueError(
                "GO_AUTH_TOKEN environment variable is required. Please add it to your .env file."
            )

        print("✅ Configuration validated successfully")
        return True

    def get_current_timestamp(self):
        """Get current timestamp for file naming"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")


# Global config instance
config = Config()
