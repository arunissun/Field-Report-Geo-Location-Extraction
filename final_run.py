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
    logger.info("Starting GeoNames enrichment process...")
    
    # File paths
    input_file = "data/extracted/country_associations.json"
    output_file = "data/extracted/geonames_enriched_associations.json"
    
    # Check if input file exists
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        return
    
    # Create enricher and run
    try:
        enricher = GeoNamesEnricher(username="user1")
        enricher.enrich_country_associations(input_file, output_file)
        logger.info("GeoNames enrichment completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during enrichment: {e}")
        raise

if __name__ == "__main__":
    main()
