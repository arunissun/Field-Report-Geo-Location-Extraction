"""
Location Extraction Manager - Integrates with the main pipeline
Azure OpenAI implementation
"""

import json
import os
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any

from location_extractor import LocationExtractor

class LocationManager:
    """Manage location extraction workflow and data storage"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.location_extractor = LocationExtractor()
        
        # Ensure extraction directory exists
        os.makedirs(self.config.EXTRACTED_DATA_DIR, exist_ok=True)
        
        # File paths for location extraction data
        self.extraction_results_file = os.path.join(self.config.EXTRACTED_DATA_DIR, "location_extraction_results.json")
    
    def load_existing_extractions(self) -> Dict[str, Any]:
        """Load existing location extraction results"""
        if os.path.exists(self.extraction_results_file):
            try:
                with open(self.extraction_results_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data
            except Exception as e:
                self.logger.error(f"Error loading existing extractions: {e}")
                return {"metadata": {}, "extractions": []}
        
        return {"metadata": {}, "extractions": []}
    
    def get_processed_report_ids(self) -> set:
        """Get set of report IDs that already have location extractions"""
        existing_data = self.load_existing_extractions()
        existing_ids = set()
        
        for extraction in existing_data.get('extractions', []):
            if 'id' in extraction:
                existing_ids.add(extraction['id'])
        
        return existing_ids
    
    def save_extraction_results(self, new_extractions: List[Dict[str, Any]]) -> str:
        """Save location extraction results to JSON file"""
        if not new_extractions:
            return self.extraction_results_file
        
        existing_data = self.load_existing_extractions()
        
        # Add new extractions to existing ones
        all_extractions = existing_data.get('extractions', [])
        
        # Remove duplicates by ID and add new extractions
        existing_ids = {ext.get('id') for ext in all_extractions}
        
        added_count = 0
        for extraction in new_extractions:
            if extraction.get('id') not in existing_ids:
                all_extractions.append(extraction)
                added_count += 1
        
        # Calculate summary statistics
        successful_extractions = [ext for ext in all_extractions if ext.get('success', False)]
        total_locations = sum(ext.get('total_locations_found', 0) for ext in successful_extractions)
        
        # Count by category
        category_counts = {
            'countries': 0,
            'states_regions': 0,
            'cities_towns': 0,
            'administrative_areas': 0
        }
        
        for extraction in successful_extractions:
            for category in category_counts.keys():
                if category in extraction and isinstance(extraction[category], list):
                    category_counts[category] += len(extraction[category])
        
        # Update metadata
        metadata = {
            'total_extractions': len(all_extractions),
            'successful_extractions': len(successful_extractions),
            'failed_extractions': len(all_extractions) - len(successful_extractions),
            'total_locations_extracted': total_locations,
            'locations_by_category': category_counts,
            'last_updated': datetime.now().isoformat(),
            'new_extractions_added': added_count,
            'extraction_info': {
                'model_used': 'Azure OpenAI GPT-3.5 Turbo',
                'extraction_fields': ['countries', 'states_regions', 'cities_towns', 'administrative_areas'],
                'processing_date': datetime.now().isoformat()
            }
        }
        
        # Prepare final data structure
        output_data = {
            'metadata': metadata,
            'extractions': all_extractions
        }
        
        # Save to file
        with open(self.extraction_results_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        if added_count > 0:
            self.logger.info(f"Saved location extraction results. Added {added_count} new extractions. Total: {len(all_extractions)}")
        
        return self.extraction_results_file
    
    async def extract_locations_from_new_reports(self, new_reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract locations from newly fetched reports using Azure OpenAI
        
        Args:
            new_reports: List of newly processed field reports
            
        Returns:
            Summary of extraction process
        """
        if not new_reports:
            return {
                'total_processed': 0,
                'total_new_extractions': 0,
                'total_locations_extracted': 0,
                'message': 'No new reports to process for location extraction'
            }
        
        # Filter out reports that already have extractions
        existing_extraction_ids = self.get_processed_report_ids()
        unprocessed_reports = []
        
        for report in new_reports:
            report_id = report.get('id')
            if report_id and report_id not in existing_extraction_ids:
                unprocessed_reports.append(report)
        
        if not unprocessed_reports:
            return {
                'total_processed': 0,
                'total_new_extractions': 0,
                'total_locations_extracted': 0,
                'message': 'All new reports already have location extractions'
            }
        
        self.logger.info(f"[LOCATION] Starting automatic location extraction for {len(unprocessed_reports)} new reports using Azure OpenAI")
        
        # Extract locations using the LocationExtractor
        extraction_results = await self.location_extractor.process_reports_batch(unprocessed_reports)
        
        # Save results
        if extraction_results:
            results_file = self.save_extraction_results(extraction_results)
        
        # Calculate summary statistics
        successful_extractions = sum(1 for result in extraction_results if result.get('success', False))
        total_locations_extracted = sum(result.get('total_locations_found', 0) for result in extraction_results)
        
        summary = {
            'total_processed': len(unprocessed_reports),
            'total_new_extractions': successful_extractions,
            'total_locations_extracted': total_locations_extracted,
            'failed_extractions': len(extraction_results) - successful_extractions
        }
        
        return summary
