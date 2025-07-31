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
    print("Field Reports Geolocation Pipeline (JSON Version)")
    print("=" * 60)

    # Check if authentication token is configured
    if not os.environ.get('GO_AUTH_TOKEN'):
        print("ERROR: Please set GO_AUTH_TOKEN in your environment variables")
        return

    # Check if running in automatic mode (for scheduled execution)
    auto_mode = os.environ.get('AUTO_MODE', 'false').lower() == 'true'
    
    if auto_mode:
        print("Running in AUTOMATIC MODE (scheduled execution)")
        run_automatic_mode()
    else:
        print("Running in INTERACTIVE MODE")
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

        print("\nCurrent Status:")
        existing_reports = json_manager.get_all_processed_reports()
        print(f"   Existing processed reports: {len(existing_reports)}")

        # Run automatically - fetch all available reports
        print("\nRunning automatic field report processing...")
        print("   Fetching ALL available reports...")
        
        summary = client.fetch_and_save_all_reports(max_reports=None)
        print_summary(summary)

    except ImportError as e:
        print(f"WARNING: Module not found: {e}")
        print("HINT: Make sure you've copied all the code files to the src/ folder")
        print("HINT: Also check that your .env file is properly configured")
    except Exception as e:
        print(f"ERROR: {e}")
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

        print("\nCurrent Status:")
        existing_reports = json_manager.get_all_processed_reports()
        print(f"   Existing processed reports: {len(existing_reports)}")

        # Ask user what they want to do (only options 3, 4, 5)
        print("\nWhat would you like to do?")
        print("   3. Fetch specific number of reports [DEFAULT]")
        print("   4. Show existing processed reports")
        print("   5. Run tests")

        choice = input("\nEnter your choice (3-5, or press Enter for default): ").strip()
        
        # Set default to option 3 if no input provided
        if choice == "":
            choice = "3"

        if choice == "3":
            try:
                user_input = input(
                    "Enter maximum number of reports to fetch (or press Enter for all): "
                ).strip()

                if user_input == "":
                    max_reports = None  # No limit - fetch all available reports
                    print("\nFetching ALL available reports...")
                else:
                    max_reports = int(user_input)
                    print(f"\nFetching up to {max_reports} reports...")

                summary = client.fetch_and_save_all_reports(max_reports=max_reports)
                print_summary(summary)
            except ValueError:
                print("ERROR: Please enter a valid number or press Enter for all reports")

        elif choice == "4":
            show_existing_reports(json_manager)

        elif choice == "5":
            run_tests()

        else:
            print("ERROR: Invalid choice. Please choose 3, 4, or 5.")

    except ImportError as e:
        print(f"WARNING: Module not found: {e}")
        print("HINT: Make sure you've copied all the code files to the src/ folder")
        print("HINT: Also check that your .env file is properly configured")
    except Exception as e:
        print(f"ERROR: {e}")
        logging.error(f"Main execution error: {e}", exc_info=True)


def run_tests():
    """Run tests"""
    try:
        from tests.test_api_client import run_all_tests
        run_all_tests()
    except ImportError:
        import subprocess
        try:
            print("Running tests directly...")
            result = subprocess.run(
                ['python', 'tests/test_api_client.py'],
                capture_output=True,
                text=True)
            print(result.stdout)
            if result.stderr:
                print("Errors:", result.stderr)
        except Exception as e:
            print(f"ERROR: Could not run tests: {e}")
            print("HINT: Make sure test_api_client.py exists in the tests/ folder")


def print_summary(summary: dict):
    """Print processing summary with location extraction results"""
    print("\nProcessing Summary:")
    print(f"   Total new reports: {summary['total_new_reports']}")
    print(f"   Total skipped (duplicates): {summary['total_skipped']}")
    print(f"   Batches created: {summary['batches_created']}")
    print(f"   Existing reports: {summary['existing_reports_count']}")
    
    # Add location extraction summary
    location_info = summary.get('location_extraction', {})
    if location_info:
        print(f"\nLocation Extraction Summary:")
        print(f"   Reports processed for locations: {location_info.get('total_processed', 0)}")
        print(f"   Successful extractions: {location_info.get('total_new_extractions', 0)}")
        print(f"   Total locations found: {location_info.get('total_locations_extracted', 0)}")
        if location_info.get('failed_extractions', 0) > 0:
            print(f"   Failed extractions: {location_info['failed_extractions']}")
        if location_info.get('error'):
            print(f"   WARNING: {location_info['error']}")

    print("\nFiles status:")
    if summary['total_new_reports'] > 0:
        print("   SUCCESS: Raw data file: Updated with new reports")
        print("   SUCCESS: Processed data file: Updated with new reports")
        if location_info.get('total_new_extractions', 0) > 0:
            print("   SUCCESS: Location extraction file: Updated with new extractions")
        print("   SUCCESS: Processing log: Created")
    else:
        print("   INFO: Raw data file: No changes (all reports were duplicates)")
        print("   INFO: Processed data file: No changes (no new reports)")
        print("   SUCCESS: Processing log: Created")

    print("\nFile locations:")
    print("   Raw data: data/raw/all_raw_reports.json")
    print("   Processed data: data/processed/all_processed_reports.json")
    if location_info.get('total_new_extractions', 0) > 0:
        print("   Location extractions: data/extracted/location_extraction_results.json")
    print("   Logs: data/logs/")



def show_existing_reports(json_manager):
    """Show information about existing processed reports"""
    reports = json_manager.get_all_processed_reports()

    if not reports:
        print("No processed reports found")
        return

    print(f"\nFound {len(reports)} processed reports:")

    # Show first 5 reports as examples
    for i, report in enumerate(reports[:5], 1):
        print(f"\n{i}. Report ID: {report.get('go_api_id')}")
        print(f"   Title: {report.get('title', '')[:60]}...")
        if report.get('summary'):
            print(f"   Summary: {report.get('summary', '')[:60]}...")
        print(f"   Country: {report.get('country_iso3', 'Unknown')}")
        print(f"   Disaster: {report.get('disaster_type', 'Unknown')}")

    if len(reports) > 5:
        print(f"\n... and {len(reports) - 5} more reports")


if __name__ == "__main__":
    main()
