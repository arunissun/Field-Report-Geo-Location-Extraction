import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import logging


class JSONManager:
    """Manage JSON file operations for field reports - Single file with duplicate prevention"""

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Single file paths
        self.raw_data_file = os.path.join(self.config.RAW_DATA_DIR,
                                          "all_raw_reports.json")
        self.processed_data_file = os.path.join(self.config.PROCESSED_DATA_DIR,
                                                "all_processed_reports.json")

        # Ensure directories exist
        os.makedirs(self.config.RAW_DATA_DIR, exist_ok=True)
        os.makedirs(self.config.PROCESSED_DATA_DIR, exist_ok=True)
        os.makedirs(self.config.LOGS_DIR, exist_ok=True)

    def load_existing_raw_data(self) -> Dict:
        """Load existing raw data from single file"""
        if os.path.exists(self.raw_data_file):
            try:
                with open(self.raw_data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {"reports": [], "metadata": {"total_count": 0}}
        return {"reports": [], "metadata": {"total_count": 0}}

    def save_raw_response(self, new_data: Dict, page_number: int = 0) -> str:
        """Append new raw data to single file, avoiding duplicates"""
        existing_data = self.load_existing_raw_data()

        # Get existing IDs to avoid duplicates
        existing_ids = {
            report.get('id')
            for report in existing_data["reports"]
        }

        # Add only new reports from the API response
        new_reports = new_data.get('results', [])
        added_count = 0

        for report in new_reports:
            report_id = report.get('id')
            if report_id not in existing_ids:
                existing_data["reports"].append(report)
                existing_ids.add(report_id)
                added_count += 1

        # Update metadata
        existing_data["metadata"] = {
            "total_count": len(existing_data["reports"]),
            "last_updated": datetime.now().isoformat(),
            "api_total_count": new_data.get('count', 0),
            "new_reports_added": added_count
        }

        with open(self.raw_data_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)

        self.logger.info(
            f"Updated raw data file. Added {added_count} new reports. Total: {existing_data['metadata']['total_count']}"
        )
        return self.raw_data_file

    def load_existing_processed_reports(self) -> List[Dict]:
        """Load existing processed reports from single file"""
        if os.path.exists(self.processed_data_file):
            try:
                with open(self.processed_data_file, 'r',
                          encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('reports', [])
            except (json.JSONDecodeError, FileNotFoundError):
                return []
        return []

    def save_processed_reports(self,
                               new_reports: List[Dict],
                               batch_number: int = 0) -> str:
        """Add new processed reports to single file, checking for duplicates by ID"""
        existing_reports = self.load_existing_processed_reports()

        # Get existing IDs to avoid duplicates
        existing_ids = {report.get('id') for report in existing_reports}

        # Add only new reports (check by ID)
        added_count = 0
        updated_count = 0

        for report in new_reports:
            report_id = report.get('id')

            if report_id not in existing_ids:
                # New report - add it
                existing_reports.append(report)
                existing_ids.add(report_id)
                added_count += 1
                self.logger.debug(f"Added new report ID: {report_id}")
            else:
                # Report exists - optionally update it (uncomment if you want updates)
                # for i, existing_report in enumerate(existing_reports):
                #     if existing_report.get('id') == report_id:
                #         existing_reports[i] = report  # Update existing report
                #         updated_count += 1
                #         break
                self.logger.debug(f"Skipped duplicate report ID: {report_id}")

        # Prepare final data structure
        output_data = {
            'metadata': {
                'total_reports': len(existing_reports),
                'last_updated': datetime.now().isoformat(),
                'new_reports_added': added_count,
                'updated_reports': updated_count,
                'processing_info': {
                    'html_cleaned': True,
                    'fields_extracted': self.config.REQUIRED_FIELDS,
                    'processing_date': datetime.now().isoformat()
                }
            },
            'reports': existing_reports
        }

        with open(self.processed_data_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        if added_count > 0:
            self.logger.info(
                f"Updated processed data file. Added {added_count} new reports. Total: {len(existing_reports)}"
            )
        else:
            self.logger.info(
                f"No new reports to add. Total reports remain: {len(existing_reports)}"
            )

        return self.processed_data_file

    def get_all_processed_reports(self) -> List[Dict]:
        """Load all processed reports from single file"""
        reports = self.load_existing_processed_reports()
        self.logger.info(f"Loaded {len(reports)} total processed reports")
        return reports

    def get_processed_report_ids(self) -> set:
        """Get set of all processed report IDs to avoid duplicates"""
        all_reports = self.get_all_processed_reports()
        return {report['id'] for report in all_reports if 'id' in report}

    def save_processing_log(self, log_data: Dict) -> str:
        """Save processing log with timestamp"""
        timestamp = self.config.get_current_timestamp()
        filename = f"processing_log_{timestamp}.json"
        filepath = os.path.join(self.config.LOGS_DIR, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        return filepath

    def get_data_summary(self) -> Dict:
        """Get summary of current data state"""
        processed_reports = self.get_all_processed_reports()
        raw_data = self.load_existing_raw_data()

        return {
            "processed_reports_count": len(processed_reports),
            "raw_reports_count": len(raw_data.get("reports", [])),
            "processed_file_exists": os.path.exists(self.processed_data_file),
            "raw_file_exists": os.path.exists(self.raw_data_file),
            "processed_file_path": self.processed_data_file,
            "raw_file_path": self.raw_data_file
        }

    def check_for_duplicates(self) -> Dict:
        """Check for and report any duplicate IDs in the processed data"""
        reports = self.get_all_processed_reports()
        ids = [report.get('id') for report in reports]

        # Find duplicates
        seen = set()
        duplicates = set()

        for report_id in ids:
            if report_id in seen:
                duplicates.add(report_id)
            else:
                seen.add(report_id)

        return {
            "total_reports": len(reports),
            "unique_ids": len(seen),
            "duplicate_ids": list(duplicates),
            "has_duplicates": len(duplicates) > 0
        }
