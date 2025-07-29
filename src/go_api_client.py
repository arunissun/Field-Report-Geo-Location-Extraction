import requests
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime

from config import config
from rate_limiter import RateLimiter
from data_processor import DataProcessor
from json_manager import JSONManager


class GOAPIClient:
    """Client for fetching field reports from IFRC GO API and saving to JSON"""

    def __init__(self):
        self.base_url = config.GO_API_BASE_URL
        self.auth_token = config.GO_AUTH_TOKEN
        self.rate_limiter = RateLimiter(requests_per_minute=40)
        self.data_processor = DataProcessor()
        self.json_manager = JSONManager(config)

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'{config.LOGS_DIR}/pipeline.log'),
                logging.StreamHandler()
            ])
        self.logger = logging.getLogger(__name__)

        # Setup session with authentication
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization':
            f'Token {self.auth_token}',
            'Content-Type':
            'application/json',
            'User-Agent':
            'Field-Reports-Geo-Pipeline/1.0'
        })

        # Validate configuration
        config.validate_config()

    def fetch_field_reports_page(self,
                                 limit: int = 50,
                                 offset: int = 0,
                                 created_at_gte: Optional[str] = None) -> Dict:
        """Fetch a single page of field reports"""

        # Apply rate limiting
        self.rate_limiter.wait_if_needed()

        endpoint = f"{self.base_url}field-report/"

        params = {
            'limit': limit,
            'offset': offset,
            'format': 'json',
            'ordering': '-created_at'
        }

        # Add date filter if provided
        if created_at_gte:
            params['created_at__gte'] = created_at_gte

        try:
            self.logger.info(
                f"Fetching field reports: offset={offset}, limit={limit}")

            response = self.session.get(endpoint,
                                        params=params,
                                        timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()

            data = response.json()

            self.logger.info(
                f"Successfully fetched {len(data.get('results', []))} reports")
            return data

        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise

    def fetch_and_save_all_reports(
            self,
            max_reports: Optional[int] = None,
            created_at_gte: Optional[str] = None) -> Dict:
        """Fetch all field reports and save them to JSON files with duplicate prevention"""

        if created_at_gte is None:
            created_at_gte = config.START_DATE

        # Get existing processed report IDs to avoid duplicates
        existing_ids = self.json_manager.get_processed_report_ids()

        offset = 0
        total_fetched = 0
        total_new = 0
        batch_number = 0
        processing_log = {
            'start_time': datetime.now().isoformat(),
            'parameters': {
                'max_reports': max_reports,
                'created_at_gte': created_at_gte,
                'existing_reports_count': len(existing_ids)
            },
            'batches': [],
            'summary': {}
        }

        self.logger.info(
            f"Starting to fetch field reports since {created_at_gte}")
        self.logger.info(f"Found {len(existing_ids)} existing reports to skip")

        while True:
            try:
                # Fetch page
                page_data = self.fetch_field_reports_page(
                    limit=config.DEFAULT_LIMIT,
                    offset=offset,
                    created_at_gte=created_at_gte)

                results = page_data.get('results', [])

                # If no results, we're done
                if not results:
                    self.logger.info("No more results found")
                    break

                # Save raw response (with duplicate checking)
                raw_file = self.json_manager.save_raw_response(
                    page_data, offset // config.DEFAULT_LIMIT)

                # Process reports with enhanced error handling and duplicate prevention
                processed_reports = []
                page_new_count = 0
                page_skipped_count = 0

                for report in results:
                    total_fetched += 1

                    # Enhanced validation: Check if report is actually a dictionary
                    if not isinstance(report, dict):
                        self.logger.error(
                            f"Expected dict, got {type(report)}: {report}")
                        continue

                    # Get report ID
                    report_id = report.get('id')
                    if report_id is None:
                        self.logger.warning(
                            f"Report missing ID, skipping: {report}")
                        continue

                    # Skip if already processed (duplicate prevention)
                    if report_id in existing_ids:
                        page_skipped_count += 1
                        self.logger.debug(
                            f"Skipping existing report ID: {report_id}")
                        continue

                    # Validate report data
                    if not self.data_processor.validate_report_data(report):
                        continue

                    # Extract and clean text content with error handling
                    try:
                        processed_report = self.data_processor.extract_and_clean_report(
                            report)

                        # Validate the processed report is a dictionary
                        if not isinstance(processed_report, dict):
                            self.logger.error(
                                f"Processed report is not a dict: {type(processed_report)}"
                            )
                            continue

                        processed_reports.append(processed_report)
                        existing_ids.add(
                            report_id
                        )  # Add to existing IDs to prevent duplicates in same run
                        page_new_count += 1
                        total_new += 1

                        self.logger.debug(
                            f"Successfully processed new report ID: {report_id}"
                        )

                    except Exception as e:
                        self.logger.error(
                            f"Error processing report {report_id}: {e}")
                        continue

                    # Check max_reports limit
                    if max_reports and total_new >= max_reports:
                        self.logger.info(
                            f"Reached maximum new reports limit: {max_reports}"
                        )
                        break

                # Save processed reports if any new ones found
                if processed_reports:
                    processed_file = self.json_manager.save_processed_reports(
                        processed_reports, batch_number)

                    batch_info = {
                        'batch_number': batch_number,
                        'offset': offset,
                        'raw_file': raw_file,
                        'processed_file': processed_file,
                        'total_in_page': len(results),
                        'new_reports': len(processed_reports),
                        'skipped_existing': page_skipped_count
                    }
                    processing_log['batches'].append(batch_info)
                    batch_number += 1
                else:
                    self.logger.info(
                        f"No new reports found in page {offset // config.DEFAULT_LIMIT}"
                    )

                # Check if there are more pages
                next_url = page_data.get('next')
                if not next_url or (max_reports and total_new >= max_reports):
                    break

                # Update offset for next page
                offset += config.DEFAULT_LIMIT

                # Add small delay between pages
                time.sleep(1)

            except Exception as e:
                self.logger.error(
                    f"Error fetching reports at offset {offset}: {e}")
                processing_log['error'] = str(e)
                break

        # Complete processing log
        processing_log['end_time'] = datetime.now().isoformat()
        processing_log['summary'] = {
            'total_fetched':
            total_fetched,
            'total_new_reports':
            total_new,
            'total_skipped':
            total_fetched - total_new,
            'batches_created':
            batch_number,
            'initial_existing_reports':
            processing_log['parameters']['existing_reports_count'],
            'final_total_reports':
            processing_log['parameters']['existing_reports_count'] + total_new,
            'existing_reports_count':
            len(existing_ids)
        }

        # Save processing log
        log_file = self.json_manager.save_processing_log(processing_log)

        if total_new > 0:
            self.logger.info(
                f"Successfully added {total_new} new field reports out of {total_fetched} total fetched"
            )
        else:
            self.logger.info(
                f"No new reports found. All {total_fetched} fetched reports were duplicates"
            )

        self.logger.info(f"Processing log saved to {log_file}")

        return processing_log['summary']

    def get_recent_reports(self,
                           days: int = 7,
                           max_reports: int = 100) -> List[Dict]:
        """Get recent field reports and return as list"""
        from datetime import datetime, timedelta

        # Calculate date filter
        since_date = datetime.now() - timedelta(days=days)
        created_at_gte = since_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        self.fetch_and_save_all_reports(max_reports=max_reports,
                                        created_at_gte=created_at_gte)
        return self.json_manager.get_all_processed_reports()

    def get_api_stats(self) -> Dict:
        """Get current API usage statistics"""
        rate_stats = self.rate_limiter.get_stats()
        processed_ids = self.json_manager.get_processed_report_ids()

        return {
            'rate_limiting': rate_stats,
            'base_url': self.base_url,
            'auth_configured': bool(self.auth_token),
            'processed_reports_count': len(processed_ids),
            'last_request_time': datetime.now().isoformat()
        }

    def check_data_integrity(self) -> Dict:
        """Check for duplicates and data integrity"""
        return self.json_manager.check_for_duplicates()
