"""
Country Association Manager - Integrates country association with the main pipeline
Handles the workflow of associating extracted locations with their correct countries
"""

import json
import os
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

from country_associator import CountryAssociator

class CountryManager:
    """Manage country association workflow and data storage for the pipeline"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.country_associator = CountryAssociator()
        
        # Ensure extraction directory exists
        os.makedirs(self.config.EXTRACTED_DATA_DIR, exist_ok=True)
        
        # File paths
        self.extraction_results_file = os.path.join(self.config.EXTRACTED_DATA_DIR, "location_extraction_results.json")
        self.association_results_file = os.path.join(self.config.EXTRACTED_DATA_DIR, "country_associations.json")
    
    def load_extraction_results(self) -> Dict[str, Any]:
        """Load location extraction results"""
        if not os.path.exists(self.extraction_results_file):
            self.logger.warning(f"Location extraction file not found: {self.extraction_results_file}")
            return {"extractions": []}
        
        try:
            with open(self.extraction_results_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.logger.debug(f"Loaded {len(data.get('extractions', []))} extractions from file")
                return data
        except Exception as e:
            self.logger.error(f"Error loading extraction results: {e}")
            return {"extractions": []}
    
    def load_existing_associations(self) -> Dict[str, Any]:
        """Load existing country association results"""
        if not os.path.exists(self.association_results_file):
            self.logger.debug(f"Country associations file not found: {self.association_results_file} (will be created)")
            return {"associations": []}
        
        try:
            with open(self.association_results_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.logger.debug(f"Loaded {len(data.get('associations', []))} existing associations")
                return data
        except Exception as e:
            self.logger.error(f"Error loading existing associations: {e}")
            return {"associations": []}
    
    def get_existing_association_ids(self) -> set:
        """Get set of report IDs that already have country associations"""
        existing_data = self.load_existing_associations()
        existing_ids = set()
        
        for assoc in existing_data.get('associations', []):
            field_report_id = assoc.get('field_report_id')
            if field_report_id:
                existing_ids.add(field_report_id)
        
        self.logger.debug(f"Found {len(existing_ids)} existing country association IDs")
        return existing_ids
    
    def filter_new_extractions(self, extractions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter extractions to only include those needing country association"""
        existing_association_ids = self.get_existing_association_ids()
        
        new_extractions = []
        skipped_unsuccessful = 0
        skipped_no_countries = 0
        skipped_already_processed = 0
        
        for extraction in extractions:
            extraction_id = extraction.get('id')
            
            # Check if extraction was successful
            if not extraction.get('success', False):
                skipped_unsuccessful += 1
                self.logger.debug(f"Skipping unsuccessful extraction for report {extraction_id}")
                continue
            
            # Check if extraction has countries (required for association)
            countries = extraction.get('countries', [])
            if not countries:
                skipped_no_countries += 1
                self.logger.debug(f"Skipping extraction {extraction_id} - no countries found")
                continue
            
            # Check if already processed for country association
            if extraction_id and extraction_id in existing_association_ids:
                skipped_already_processed += 1
                self.logger.debug(f"Skipping extraction {extraction_id} - already has country association")
                continue
            
            # This extraction needs country association
            new_extractions.append(extraction)
        
        self.logger.info(f"Filtered extractions: {len(new_extractions)} need processing, "
                        f"{skipped_unsuccessful} unsuccessful, {skipped_no_countries} no countries, "
                        f"{skipped_already_processed} already processed")
        
        return new_extractions
    
    async def process_country_associations_for_new_extractions(self) -> Dict[str, Any]:
        """
        Main method to process country associations for newly extracted locations
        Called automatically after location extraction in the pipeline
        """
        try:
            # Check if country associator is enabled
            if not self.country_associator.enabled:
                self.logger.warning("Azure OpenAI not configured for country association")
                return {
                    'total_processed': 0,
                    'successful': 0,
                    'failed': 0,
                    'skipped_existing': 0,
                    'error': 'Azure OpenAI not configured for country association'
                }
            
            # Load all extraction results
            extraction_data = self.load_extraction_results()
            all_extractions = extraction_data.get('extractions', [])
            
            if not all_extractions:
                self.logger.warning("No location extractions found")
                return {
                    'total_processed': 0,
                    'successful': 0,
                    'failed': 0,
                    'skipped_existing': 0,
                    'message': 'No location extractions found'
                }
            
            # Filter to only new extractions needing country association
            new_extractions = self.filter_new_extractions(all_extractions)
            
            if not new_extractions:
                total_existing = len(all_extractions)
                self.logger.info("All extractions already have country associations or lack countries")
                return {
                    'total_processed': 0,
                    'successful': 0,
                    'failed': 0,
                    'skipped_existing': total_existing,
                    'message': 'All extractions already have country associations or lack countries'
                }
            
            # Log the processing start
            total_existing = len(all_extractions) - len(new_extractions)
            self.logger.info(f"Processing country associations for {len(new_extractions)} new extractions (skipping {total_existing} existing)")
            
            # Process new extractions for country association
            association_results = []
            successful_count = 0
            failed_count = 0
            
            # Process in small batches to avoid overwhelming the API
            batch_size = 3
            for i in range(0, len(new_extractions), batch_size):
                batch = new_extractions[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(new_extractions) + batch_size - 1) // batch_size
                
                self.logger.info(f"Processing country association batch {batch_num}/{total_batches} ({len(batch)} extractions)")
                
                # Process batch
                for extraction in batch:
                    try:
                        result = await self.country_associator.associate_locations_for_report(extraction)
                        association_results.append(result)
                        
                        if result.get('success', False):
                            successful_count += 1
                            self.logger.debug(f"Successfully associated countries for report {extraction.get('id')}")
                        else:
                            failed_count += 1
                            self.logger.warning(f"Failed to associate countries for report {extraction.get('id')}: {result.get('error', 'Unknown error')}")
                            
                    except Exception as e:
                        extraction_id = extraction.get('id', 'unknown')
                        self.logger.error(f"Exception processing country association for report {extraction_id}: {e}")
                        
                        # Create error result
                        error_result = {
                            "field_report_id": extraction_id,
                            "success": False,
                            "error": f"Processing exception: {str(e)}",
                            "processed_at": datetime.now().isoformat()
                        }
                        association_results.append(error_result)
                        failed_count += 1
                
                # Rate limiting between batches
                if i + batch_size < len(new_extractions):
                    await asyncio.sleep(3)  # Wait 3 seconds between batches
            
            # Save results (append to existing associations)
            if association_results:
                self.save_association_results(association_results)
            
            # Return summary
            summary = {
                'total_processed': len(new_extractions),
                'successful': successful_count,
                'failed': failed_count,
                'skipped_existing': total_existing
            }
            
            self.logger.info(f"Country association completed: {successful_count} successful, {failed_count} failed")
            return summary
            
        except Exception as e:
            self.logger.error(f"Country association process failed: {e}")
            return {
                'total_processed': 0,
                'successful': 0,
                'failed': 0,
                'skipped_existing': 0,
                'error': str(e)
            }
    
    def save_association_results(self, new_associations: List[Dict[str, Any]]):
        """Save new association results to file (append to existing)"""
        if not new_associations:
            self.logger.debug("No new associations to save")
            return
        
        # Load existing associations
        existing_data = self.load_existing_associations()
        all_associations = existing_data.get('associations', [])
        
        # Get existing IDs to prevent duplicates
        existing_ids = {assoc.get('field_report_id') for assoc in all_associations}
        
        # Add new associations (avoiding duplicates)
        added_count = 0
        for new_assoc in new_associations:
            field_report_id = new_assoc.get('field_report_id')
            if field_report_id and field_report_id not in existing_ids:
                all_associations.append(new_assoc)
                existing_ids.add(field_report_id)
                added_count += 1
            else:
                self.logger.debug(f"Skipping duplicate association for report {field_report_id}")
        
        # Calculate statistics
        successful_count = sum(1 for assoc in all_associations if assoc.get('success', False))
        failed_count = len(all_associations) - successful_count
        
        # Prepare output data
        output_data = {
            'metadata': {
                'total_associations': len(all_associations),
                'successful_associations': successful_count,
                'failed_associations': failed_count,
                'last_updated': datetime.now().isoformat(),
                'new_associations_added': added_count,
                'model_used': 'Azure OpenAI GPT-3.5 Turbo',
                'output_format': 'simplified_flat_structure'
            },
            'associations': all_associations
        }
        
        # Save to file
        with open(self.association_results_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved {added_count} new country associations. Total: {len(all_associations)}")
    
    def get_association_statistics(self) -> Dict[str, Any]:
        """Get statistics about country associations"""
        existing_data = self.load_existing_associations()
        associations = existing_data.get('associations', [])
        
        if not associations:
            return {
                'total_associations': 0,
                'successful_associations': 0,
                'failed_associations': 0,
                'message': 'No country associations found'
            }
        
        successful_count = sum(1 for assoc in associations if assoc.get('success', False))
        failed_count = len(associations) - successful_count
        
        return {
            'total_associations': len(associations),
            'successful_associations': successful_count,
            'failed_associations': failed_count,
            'last_updated': existing_data.get('metadata', {}).get('last_updated'),
            'association_file': self.association_results_file
        }
