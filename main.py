"""
Main entry point for the JSON-based Field Reports Pipeline
"""

import os
import sys
import logging

from dotenv import load_dotenv

load_dotenv()

# Add src to Python path so we can import our modules
src_dir = os.path.join(os.path.dirname(__file__), 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)


def main():
    """Main function with automatic and interactive modes"""
    print("FIELD REPORTS PIPELINE - Starting geolocation processing")
    print("=" * 60)

    # Check if authentication token is configured
    if not os.environ.get('GO_AUTH_TOKEN'):
        print("ERROR: Missing GO_AUTH_TOKEN environment variable")
        print("SETUP: Please configure your GO API authentication token")
        return

    # Check if running in automatic mode (for scheduled execution)
    auto_mode = os.environ.get('AUTO_MODE', 'false').lower() == 'true'
    
    if auto_mode:
        print("MODE: Automatic execution (scheduled run)")
        run_automatic_mode()
    else:
        print("MODE: Interactive execution (manual run)")
        run_interactive_mode()


def run_automatic_mode():
    """Run automatically without user input - for scheduled execution"""
    try:
        # Import and test your existing GO API code
        from go_api_client import GOAPIClient
        from json_manager import JSONManager
        from config import config

        # Initialize client
        client = GOAPIClient()
        json_manager = JSONManager(config)

        print("STATUS: Checking current data state")
        existing_reports = json_manager.get_all_processed_reports()
        print(f"EXISTING: {len(existing_reports)} processed reports found")

        # Run automatically - fetch all available reports
        print("PROCESSING: Starting automatic field report fetch")
        print("SCOPE: Fetching ALL available reports from GO API")
        
        summary = client.fetch_and_save_all_reports(max_reports=None)
        print_summary(summary)

    except ImportError as e:
        print(f"IMPORT ERROR: {e}")
        print("SETUP: Ensure all code files are in the src/ folder")
        print("SETUP: Check that .env file is properly configured")
    except Exception as e:
        print(f"EXECUTION ERROR: {e}")
        logging.error(f"Main execution error: {e}", exc_info=True)


def run_interactive_mode():
    """Run with user interaction - for manual execution"""
    try:
        # Import and test your existing GO API code
        from go_api_client import GOAPIClient
        from json_manager import JSONManager
        from config import config

        # Initialize client
        client = GOAPIClient()
        json_manager = JSONManager(config)

        print("STATUS: Checking current data state")
        existing_reports = json_manager.get_all_processed_reports()
        print(f"EXISTING: {len(existing_reports)} processed reports found")

        # Ask user what they want to do (only options 3, 4, 5)
        print("\nOPTIONS: Choose your action")
        print("   3. Fetch specific number of reports [DEFAULT]")
        print("   4. Show existing processed reports")
        print("   5. Run tests")

        choice = input("\nINPUT: Enter choice (3-5, or press Enter for default): ").strip()
        
        # Set default to option 3 if no input provided
        if choice == "":
            choice = "3"

        if choice == "3":
            try:
                user_input = input(
                    "INPUT: Enter max reports to fetch (or press Enter for all): "
                ).strip()

                if user_input == "":
                    max_reports = None  # No limit - fetch all available reports
                    print("SCOPE: Fetching ALL available reports from GO API")
                else:
                    max_reports = int(user_input)
                    print(f"SCOPE: Fetching up to {max_reports} reports from GO API")

                summary = client.fetch_and_save_all_reports(max_reports=max_reports)
                print_summary(summary)
            except ValueError:
                print("INPUT ERROR: Please enter a valid number or press Enter for all reports")

        elif choice == "4":
            show_existing_reports(json_manager)

        elif choice == "5":
            run_tests()

        else:
            print("INPUT ERROR: Invalid choice. Please choose 3, 4, or 5.")

    except ImportError as e:
        print(f"IMPORT ERROR: {e}")
        print("SETUP: Ensure all code files are in the src/ folder")
        print("SETUP: Check that .env file is properly configured")
    except Exception as e:
        print(f"EXECUTION ERROR: {e}")
        logging.error(f"Main execution error: {e}", exc_info=True)


def run_tests():
    """Run tests"""
    try:
        print("TESTING: Running test suite")
        from tests.test_api_client import run_all_tests
        run_all_tests()
    except ImportError:
        import subprocess
        try:
            print("TESTING: Running tests directly via subprocess")
            result = subprocess.run(
                ['python', 'tests/test_api_client.py'],
                capture_output=True,
                text=True)
            print(result.stdout)
            if result.stderr:
                print(f"TEST ERRORS: {result.stderr}")
        except Exception as e:
            print(f"TEST ERROR: Could not run tests - {e}")
            print("SETUP: Ensure test_api_client.py exists in the tests/ folder")


def print_summary(summary: dict):
    """Print processing summary with location extraction results"""
    print("\nPROCESSING SUMMARY:")
    print(f"NEW REPORTS: {summary['total_new_reports']}")
    print(f"SKIPPED (duplicates): {summary['total_skipped']}")
    print(f"BATCHES CREATED: {summary['batches_created']}")
    print(f"EXISTING REPORTS: {summary['existing_reports_count']}")
    
    # Add location extraction summary
    location_info = summary.get('location_extraction', {})
    if location_info:
        print("\nLOCATION EXTRACTION SUMMARY:")
        print(f"PROCESSED: {location_info.get('total_processed', 0)} reports")
        print(f"SUCCESSFUL: {location_info.get('total_new_extractions', 0)} extractions")
        print(f"LOCATIONS FOUND: {location_info.get('total_locations_extracted', 0)} total")
        if location_info.get('failed_extractions', 0) > 0:
            print(f"FAILED: {location_info['failed_extractions']} extractions")
        if location_info.get('error'):
            print(f"WARNING: {location_info['error']}")

    print("\nFILE STATUS:")
    if summary['total_new_reports'] > 0:
        print("RAW DATA: Updated with new reports")
        print("PROCESSED DATA: Updated with new reports")
        if location_info.get('total_new_extractions', 0) > 0:
            print("LOCATION DATA: Updated with new extractions")
        print("PROCESSING LOG: Created")
    else:
        print("RAW DATA: No changes (all reports were duplicates)")
        print("PROCESSED DATA: No changes (no new reports)")
        print("PROCESSING LOG: Created")

    print("\nFILE LOCATIONS:")
    print("Raw data: data/raw/all_raw_reports.json")
    print("Processed data: data/processed/all_processed_reports.json")
    if location_info.get('total_new_extractions', 0) > 0:
        print("Location extractions: data/extracted/location_extraction_results.json")
    print("Logs: data/logs/")



def show_existing_reports(json_manager):
    """Show information about existing processed reports"""
    reports = json_manager.get_all_processed_reports()

    if not reports:
        print("REPORTS: No processed reports found")
        return

    print(f"\nREPORTS FOUND: {len(reports)} processed reports")

    # Show first 5 reports as examples
    for i, report in enumerate(reports[:5], 1):
        print(f"\n{i}. ID: {report.get('go_api_id')}")
        print(f"   TITLE: {report.get('title', '')[:60]}...")
        if report.get('summary'):
            print(f"   SUMMARY: {report.get('summary', '')[:60]}...")
        print(f"   COUNTRY: {report.get('country_iso3', 'Unknown')}")
        print(f"   DISASTER: {report.get('disaster_type', 'Unknown')}")

    if len(reports) > 5:
        print(f"\nADDITIONAL: {len(reports) - 5} more reports available")


if __name__ == "__main__":
    main()
