import re
import logging
from bs4 import BeautifulSoup
from typing import Dict, Optional
from datetime import datetime


class DataProcessor:
    """Handle HTML cleaning and data extraction from field reports"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def clean_html(self, text: Optional[str]) -> str:
        """Remove HTML tags and clean text content"""
        if not text or text.strip() == "":
            return ""

        try:
            # Use BeautifulSoup to parse and clean HTML
            soup = BeautifulSoup(text, 'html.parser')

            # Extract text content
            cleaned_text = soup.get_text()

            # Clean up whitespace
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
            cleaned_text = cleaned_text.strip()

            return cleaned_text

        except Exception as e:
            self.logger.warning(f"Error cleaning HTML content: {e}")
            # Fallback: simple regex-based cleaning
            return self._simple_html_clean(text)

    def _simple_html_clean(self, text: str) -> str:
        """Fallback HTML cleaning using regex"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Clean up HTML entities
        html_entities = {
            '&nbsp;': ' ',
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&hellip;': '...'
        }

        for entity, replacement in html_entities.items():
            text = text.replace(entity, replacement)

        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def extract_and_clean_report(self, report: Dict) -> Dict:
        """Extract and clean text content from field report - simplified version"""

        # Enhanced validation
        if not isinstance(report, dict):
            raise ValueError(f"Expected dict, got {type(report)}: {report}")

        if 'id' not in report:
            raise ValueError(f"Report missing required 'id' field: {report}")

        try:
            # Simplified cleaned report with only essential fields
            cleaned_report = {
                'id':
                report.get('id'),
                'country':
                self._safe_extracted_nested(report,
                                            ['country_details', 'name']),
                'event_name':
                self._safe_extracted_nested(report, ['event_details', 'name']),
                'disaster_type':
                self._safe_extracted_nested(report, ['dtype_details', 'name']),
                'title':
                self.clean_html(report.get('title', '')),
                'description':
                self.clean_html(report.get('description', '')),
                'summary':
                self.clean_html(report.get('summary', '')),
                'status':
                'fetched',  # Processing status
                'fetched_at':
                datetime.now().isoformat()
            }

            # Validate the result is a proper dictionary
            if not isinstance(cleaned_report, dict):
                raise ValueError(
                    f"Processed report is not a dict: {type(cleaned_report)}")

            return cleaned_report

        except Exception as e:
            self.logger.error(
                f"Error in extract_and_clean_report for report {report.get('id', 'unknown')}: {e}"
            )
            raise

    def validate_report_data(self, report: Dict) -> bool:
        """Validate that report contains required data"""

        # Enhanced validation
        if not isinstance(report, dict):
            self.logger.error(f"Report is not a dictionary: {type(report)}")
            return False

        required_fields = ['id', 'title', 'description', 'summary']

        for field in required_fields:
            if field not in report:
                self.logger.warning(
                    f"Report {report.get('id', 'unknown')} missing field: {field}"
                )
                return False

        # Check if at least one text field has actual content (not just empty/whitespace)
        text_fields = ['title', 'description', 'summary']
        has_content = False

        for field in text_fields:
            field_value = report.get(field, "")
            if field_value and str(field_value).strip():
                has_content = True
                break

        if not has_content:
            self.logger.warning(
                f"Report {report.get('id')} has no meaningful text content")
            return False

        return True

    def _safe_extracted_nested(self, data: Dict, keys: list) -> Optional[str]:
        """Safely extract nested value from dictionary"""

        try:
            current = data
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]

                else:
                    return None

            if current is not None:
                return str(current)

            return None

        except Exception as e:
            self.logger.debug(f"Error extractin nested keys {keys}: {e}")
            return None
