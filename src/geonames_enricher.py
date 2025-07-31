"""
GeoNames Enricher - Enriches country associations with GeoNames API data
Focuses on: population, coordinates, official name, and geoname_id
"""

import json
import requests
import time
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import quote

class GeoNamesEnricher:
    """Enriches location data using GeoNames API"""
    
    def __init__(self, username: str = "user1"):
        self.username = username
        self.base_url = "http://api.geonames.org/searchJSON"
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting
        self.rate_limit_delay = 1.0  # 1 second between requests
        self.max_retries = 3
        
        # Statistics
        self.stats = {
            'total_api_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'locations_enriched': 0,
            'locations_not_found': 0,
            'skipped_reports': 0
        }
        
        # Load country codes from JSON file
        self.country_codes = self._load_country_codes()
        
        self.logger.info(f"GeoNamesEnricher initialized with username: {username}")
    
    def _load_country_codes(self) -> Dict[str, str]:
        """Load country codes from JSON file"""
        country_codes_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                         'data', 'reference', 'country_codes.json')
        
        try:
            with open(country_codes_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                country_codes = data.get('country_codes', {})
                self.logger.info(f"Loaded {len(country_codes)} country code mappings from {country_codes_file}")
                return country_codes
        except FileNotFoundError:
            self.logger.error(f"Country codes file not found: {country_codes_file}")
            # Fallback to basic mappings if file not found
            return {
                'usa': 'US', 'united states': 'US', 'chile': 'CL', 'russia': 'RU',
                'indonesia': 'ID', 'china': 'CN', 'japan': 'JP'
            }
        except Exception as e:
            self.logger.error(f"Error loading country codes: {e}")
            return {}
    
    def get_country_code(self, country_name: str) -> Optional[str]:
        """Get ISO country code for country name"""
        normalized = country_name.lower().strip()
        return self.country_codes.get(normalized)
    
    def make_geonames_request(self, location_name: str, country_code: str, 
                            is_state: bool = False) -> Optional[Dict[str, Any]]:
        """Make a request to GeoNames API"""
        
        # URL encode the location name
        encoded_location = quote(location_name)
        
        # Set feature parameters based on location type
        if is_state:
            # For states/regions: Administrative divisions
            feature_class = "A"
            feature_code = "ADM1"
        else:
            # For cities/towns: Populated places
            feature_class = "P"
            feature_code = ""  # Let GeoNames decide the best populated place type
        
        # Build URL
        url = f"{self.base_url}?q={encoded_location}&country={country_code}&featureClass={feature_class}"
        if feature_code:
            url += f"&featureCode={feature_code}"
        url += f"&maxRows=1&username={self.username}"
        
        self.stats['total_api_calls'] += 1
        
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"API call {self.stats['total_api_calls']}: {location_name} in {country_code}")
                
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                # Check for API errors
                if 'status' in data:
                    self.logger.error(f"GeoNames API error for {location_name}: {data['status']}")
                    self.stats['failed_calls'] += 1
                    return None
                
                # Check if we got results
                if 'geonames' in data and len(data['geonames']) > 0:
                    self.stats['successful_calls'] += 1
                    return data['geonames'][0]  # Return first (best) match
                else:
                    self.logger.warning(f"No results found for {location_name} in {country_code}")
                    self.stats['locations_not_found'] += 1
                    return None
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request failed for {location_name} (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    self.stats['failed_calls'] += 1
                    return None
                time.sleep(2)  # Wait before retry
            
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON decode error for {location_name}: {e}")
                self.stats['failed_calls'] += 1
                return None
        
        return None
    
    def extract_essential_data(self, geonames_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract only the essential fields we need"""
        return {
            'geoname_id': geonames_result.get('geonameId'),
            'official_name': geonames_result.get('name', ''),
            'population': geonames_result.get('population', 0),
            'coordinates': {
                'latitude': float(geonames_result.get('lat', 0)),
                'longitude': float(geonames_result.get('lng', 0))
            }
        }
    
    def enrich_locations(self, locations: List[str], country_code: str, 
                        is_state: bool = False) -> List[Dict[str, Any]]:
        """Enrich a list of locations with GeoNames data"""
        enriched_locations = []
        
        for location in locations:
            # Make API call with rate limiting
            time.sleep(self.rate_limit_delay)
            
            geonames_result = self.make_geonames_request(location, country_code, is_state)
            
            location_data = {
                'original_name': location,
                'geonames_data': None
            }
            
            if geonames_result:
                location_data['geonames_data'] = self.extract_essential_data(geonames_result)
                self.stats['locations_enriched'] += 1
                self.logger.info(f"Enriched: {location} -> {location_data['geonames_data']['official_name']}")
            else:
                self.logger.warning(f"Could not enrich: {location}")
            
            enriched_locations.append(location_data)
        
        return enriched_locations
    
    def enrich_field_report(self, association: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich a single field report association"""
        
        report_id = association.get('field_report_id', 'unknown')
        countries = association.get('countries', [])
        
        if not association.get('success', False) or not countries:
            self.logger.info(f"Skipping report {report_id}: no successful associations or countries")
            return {
                'field_report_id': report_id,
                'success': False,
                'error': 'No successful associations or countries found',
                'processing_status': {
                    'api_calls_made': 0,
                    'locations_enriched': 0,
                    'processed_at': datetime.now().isoformat()
                }
            }
        
        enriched_report = {
            'field_report_id': report_id,
            'countries': [],
            'unassigned_locations': {
                'states_regions': [],
                'cities_towns': []
            }
        }
        
        total_api_calls_before = self.stats['total_api_calls']
        total_enriched_before = self.stats['locations_enriched']
        
        # Process each country
        for country in countries:
            country_code = self.get_country_code(country)
            
            if not country_code:
                self.logger.warning(f"No country code found for: {country}")
                continue
            
            country_data = {
                'country_name': country,
                'country_code': country_code,
                'states_regions': [],
                'cities_towns': []
            }
            
            # Get normalized country name for field keys
            normalized_country = country.lower().replace(' ', '').replace('-', '').replace('\'', '').replace('.', '')
            
            # Find state/region fields for this country
            states_key = f"{normalized_country}_states"
            cities_key = f"{normalized_country}_cities"
            
            # Handle various country name formats
            possible_states_keys = [
                states_key,
                f"{country.lower().replace(' ', '')}_states",
                f"{country.replace(' ', '').lower()}_states"
            ]
            
            possible_cities_keys = [
                cities_key,
                f"{country.lower().replace(' ', '')}_cities", 
                f"{country.replace(' ', '').lower()}_cities"
            ]
            
            # Find the actual keys used in the data
            states_list = []
            cities_list = []
            
            for key in association.keys():
                if 'states' in key and any(country.lower().replace(' ', '') in key.lower() for country in [country]):
                    states_list.extend(association.get(key, []))
                elif 'cities' in key and any(country.lower().replace(' ', '') in key.lower() for country in [country]):
                    cities_list.extend(association.get(key, []))
            
            # Enrich states/regions
            if states_list:
                self.logger.info(f"Enriching {len(states_list)} states for {country}")
                country_data['states_regions'] = self.enrich_locations(states_list, country_code, is_state=True)
            
            # Enrich cities/towns
            if cities_list:
                self.logger.info(f"Enriching {len(cities_list)} cities for {country}")
                country_data['cities_towns'] = self.enrich_locations(cities_list, country_code, is_state=False)
            
            enriched_report['countries'].append(country_data)
        
        # Handle unassigned locations
        unassigned_states = association.get('unassigned_states', [])
        unassigned_cities = association.get('unassigned_cities', [])
        
        if unassigned_states:
            enriched_report['unassigned_locations']['states_regions'] = [
                {'original_name': state, 'geonames_data': None} for state in unassigned_states
            ]
        
        if unassigned_cities:
            enriched_report['unassigned_locations']['cities_towns'] = [
                {'original_name': city, 'geonames_data': None} for city in unassigned_cities
            ]
        
        # Add processing status
        api_calls_made = self.stats['total_api_calls'] - total_api_calls_before
        locations_enriched = self.stats['locations_enriched'] - total_enriched_before
        
        enriched_report['processing_status'] = {
            'success': True,
            'api_calls_made': api_calls_made,
            'locations_enriched': locations_enriched,
            'processed_at': datetime.now().isoformat()
        }
        
        self.logger.info(f"Completed report {report_id}: {api_calls_made} API calls, {locations_enriched} locations enriched")
        
        return enriched_report
    
    def load_existing_enriched_data(self, file_path: str) -> Tuple[Dict[str, Any], set]:
        """Load existing enriched data and return processed report IDs"""
        if not os.path.exists(file_path):
            return {
                'metadata': {
                    'total_field_reports': 0,
                    'enriched_reports': 0,
                    'geonames_api_calls': 0,
                    'last_updated': datetime.now().isoformat(),
                    'api_username': self.username,
                    'data_source': 'GeoNames API',
                    'format_version': '1.0'
                },
                'enriched_associations': []
            }, set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            
            # Extract processed report IDs
            processed_ids = set()
            for report in existing_data.get('enriched_associations', []):
                processed_ids.add(report.get('field_report_id'))
            
            self.logger.info(f"Loaded existing data: {len(processed_ids)} reports already processed")
            return existing_data, processed_ids
            
        except Exception as e:
            self.logger.error(f"Error loading existing data: {e}")
            return {
                'metadata': {
                    'total_field_reports': 0,
                    'enriched_reports': 0,
                    'geonames_api_calls': 0,
                    'last_updated': datetime.now().isoformat(),
                    'api_username': self.username,
                    'data_source': 'GeoNames API',
                    'format_version': '1.0'
                },
                'enriched_associations': []
            }, set()
    
    def save_enriched_data(self, enriched_data: Dict[str, Any], file_path: str):
        """Save enriched data to JSON file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(enriched_data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Saved enriched data to: {file_path}")
        except Exception as e:
            self.logger.error(f"Error saving enriched data: {e}")
            raise
    
    def enrich_country_associations(self, input_file: str, output_file: str):
        """Main method to enrich country associations with GeoNames data"""
        
        self.logger.info("Starting GeoNames enrichment process")
        
        # Load input data
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                input_data = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading input file {input_file}: {e}")
            return
        
        # Load existing enriched data
        enriched_data, processed_ids = self.load_existing_enriched_data(output_file)
        
        # Process associations
        associations = input_data.get('associations', [])
        new_enriched_reports = []
        
        self.logger.info(f"Processing {len(associations)} associations")
        
        for i, association in enumerate(associations, 1):
            report_id = association.get('field_report_id', 'unknown')
            
            # Skip if already processed
            if report_id in processed_ids:
                self.logger.info(f"Skipping report {report_id} (already processed)")
                self.stats['skipped_reports'] += 1
                continue
            
            self.logger.info(f"Processing report {report_id} ({i}/{len(associations)})")
            
            # Enrich the report
            enriched_report = self.enrich_field_report(association)
            new_enriched_reports.append(enriched_report)
            
            # Save progress every 10 reports
            if len(new_enriched_reports) % 10 == 0:
                temp_data = enriched_data.copy()
                temp_data['enriched_associations'].extend(new_enriched_reports)
                temp_data['metadata']['enriched_reports'] = len(temp_data['enriched_associations'])
                temp_data['metadata']['geonames_api_calls'] = self.stats['total_api_calls']
                temp_data['metadata']['last_updated'] = datetime.now().isoformat()
                
                self.save_enriched_data(temp_data, output_file)
                self.logger.info(f"Progress saved: {len(new_enriched_reports)} new reports processed")
        
        # Final save
        enriched_data['enriched_associations'].extend(new_enriched_reports)
        enriched_data['metadata'] = {
            'total_field_reports': len(input_data.get('associations', [])),
            'enriched_reports': len(enriched_data['enriched_associations']),
            'geonames_api_calls': self.stats['total_api_calls'],
            'last_updated': datetime.now().isoformat(),
            'api_username': self.username,
            'data_source': 'GeoNames API',
            'format_version': '1.0'
        }
        
        self.save_enriched_data(enriched_data, output_file)
        
        # Print final statistics
        self.logger.info("=== ENRICHMENT COMPLETED ===")
        self.logger.info(f"Total API calls: {self.stats['total_api_calls']}")
        self.logger.info(f"Successful calls: {self.stats['successful_calls']}")
        self.logger.info(f"Failed calls: {self.stats['failed_calls']}")
        self.logger.info(f"Locations enriched: {self.stats['locations_enriched']}")
        self.logger.info(f"Locations not found: {self.stats['locations_not_found']}")
        self.logger.info(f"Reports skipped (already processed): {self.stats['skipped_reports']}")
        self.logger.info(f"New reports processed: {len(new_enriched_reports)}")
        self.logger.info(f"Output file: {output_file}")


def main():
    """Main function to run the enrichment"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('geonames_enrichment.log'),
            logging.StreamHandler()
        ]
    )
    
    # File paths
    input_file = r"data\extracted\country_associations.json"
    output_file = r"data\extracted\geonames_enriched_associations.json"
    
    # Create enricher and run
    enricher = GeoNamesEnricher(username="user1")
    enricher.enrich_country_associations(input_file, output_file)


if __name__ == "__main__":
    main()
