"""
GeoNames Enrichment Runner
Simple script to run the GeoNames enrichment process
"""

import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from geonames_enricher import GeoNamesEnricher
import logging

def main():
    """Run the GeoNames enrichment process"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('data/logs/geonames_enrichment.log'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    print("GEONAMES ENRICHMENT - Starting location data enhancement")
    print("=" * 60)
    
    # File paths
    input_file = "data/extracted/country_associations.json"
    output_file = "data/extracted/geonames_enriched_associations.json"
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"INPUT ERROR: File not found - {input_file}")
        print("REQUIREMENT: Run main.py first to generate location data")
        logger.error(f"Input file not found: {input_file}")
        return
    
    print(f"INPUT: Reading from {input_file}")
    print(f"OUTPUT: Writing to {output_file}")
    
    # Create enricher and run
    try:
        print("PROCESSING: Initializing GeoNames enricher")
        enricher = GeoNamesEnricher(username="user1")
        
        print("PROCESSING: Starting country associations enrichment")
        enricher.enrich_country_associations(input_file, output_file)
        
        print("SUCCESS: GeoNames enrichment completed")
        logger.info("GeoNames enrichment completed successfully!")
        
    except Exception as e:
        print(f"PROCESSING ERROR: {e}")
        logger.error(f"Error during enrichment: {e}")
        raise

if __name__ == "__main__":
    main()
