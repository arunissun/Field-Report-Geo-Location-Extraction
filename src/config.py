import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_result = load_dotenv(dotenv_path)

# If that fails, try current directory
if not load_result:
    load_result = load_dotenv('.env')

# Debug: Print load result (remove this in production)
print(f"dotenv load result: {load_result}")


class Config:
    """Configuration management for the field reports pipeline"""

    def __init__(self):
        # API Configuration
        self.GO_API_BASE_URL = "https://goadmin.ifrc.org/api/v2/"
        self.GO_AUTH_TOKEN = os.environ.get('GO_AUTH_TOKEN')

        # Debug: Print if token was found (remove this in production)
        if self.GO_AUTH_TOKEN:
            print(
                f"✅ Config loaded GO_AUTH_TOKEN: {self.GO_AUTH_TOKEN[:10]}...")
        else:
            print("❌ Config: GO_AUTH_TOKEN not found")

        # OpenAI Configuration (for future use)
        self.OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
        self.GEONAMES_USERNAME = os.environ.get('GEONAMES_USERNAME')

        # Pagination settings
        self.DEFAULT_LIMIT = 50
        self.MAX_RETRIES = 3
        self.REQUEST_TIMEOUT = 30

        # Date filtering - reports since January 1st, 2025
        self.START_DATE = "2025-06-01T00:00:00Z"

        # Required fields from API
        self.REQUIRED_FIELDS = ['id', 'title', 'description', 'summary']

        # File paths
        self.RAW_DATA_DIR = "data/raw"
        self.PROCESSED_DATA_DIR = "data/processed"
        self.LOGS_DIR = "data/logs"

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
