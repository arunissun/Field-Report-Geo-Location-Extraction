"""
Main entry point for the JSON-based Field Reports Pipeline
"""

import os
import sys
import logging

# Add src to Python path so we can import our modules
sys.path.append('src')


def main():
    """Main function to demonstrate JSON-based pipeline"""
    print("🌍 Field Reports Geolocation Pipeline (JSON Version)")
    print("=" * 60)

    # Check if authentication token is configured
    if not os.environ.get('GO_AUTH_TOKEN'):
        print("❌ Please set GO_AUTH_TOKEN in your Replit Secrets")
        print("   Go to the 🔒 Secrets tab and add your IFRC GO API token")

        return

    print("✅ Authentication token found")

    try:
        # Import and test your existing GO API code
        from go_api_client import GOAPIClient
        from json_manager import JSONManager
        from config import config

        # Initialize client
        client = GOAPIClient()
        json_manager = JSONManager(config)

        print("\n📊 Current Status:")
        existing_reports = json_manager.get_all_processed_reports()
        print(f"   Existing processed reports: {len(existing_reports)}")

        # Get API stats
        stats = client.get_api_stats()
        print(
            f"   Rate limit status: {stats['rate_limiting']['requests_last_minute']}/{stats['rate_limiting']['requests_per_minute_limit']} requests/minute"
        )

        # Ask user what they want to do
        print("\n🔧 What would you like to do?")
        print("   1. Fetch recent reports (last 7 days, max 50)")
        print("   2. Fetch all reports since January 1st, 2025 (max 100)")
        print("   3. Fetch specific number of reports")
        print("   4. Show existing processed reports")
        print("   5. Run tests")

        choice = input("\nEnter your choice (1-5): ").strip()

        if choice == "1":
            print("\n📥 Fetching recent reports...")
            summary = client.fetch_and_save_all_reports(max_reports=50,
                                                        created_at_gte=None)
            print_summary(summary)

        elif choice == "2":
            print("\n📥 Fetching all reports since January 1st, 2025...")
            summary = client.fetch_and_save_all_reports(max_reports=100)
            print_summary(summary)

        elif choice == "3":
            try:
                user_input = input(
                    "Enter maximum number of reports to fetch (or press Enter for all): "
                ).strip()

                if user_input == "":
                    max_reports = None  # No limit - fetch all available reports
                    print("\n📥 Fetching ALL available reports...")
                else:
                    max_reports = int(user_input)
                    print(f"\n📥 Fetching up to {max_reports} reports...")

                summary = client.fetch_and_save_all_reports(
                    max_reports=max_reports)
                print_summary(summary)
            except ValueError:
                print(
                    "❌ Please enter a valid number or press Enter for all reports"
                )

        elif choice == "4":
            show_existing_reports(json_manager)

        elif choice == "5":
            # Fixed test import - more robust approach
            try:
                # Try direct import first

                from tests.test_api_client import run_all_tests
                run_all_tests()
            except ImportError:
                # Fallback: run test file directly
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
                    print(f"❌ Could not run tests: {e}")
                    print(
                        "💡 Make sure test_api_client.py exists in the tests/ folder"
                    )

        else:
            print("❌ Invalid choice")

    except ImportError as e:
        print(f"⚠️  Module not found: {e}")
        print(
            "💡 Make sure you've copied all the code files to the src/ folder")
        print("💡 Also check that your .env file is properly configured")
    except Exception as e:
        print(f"❌ Error: {e}")
        logging.error(f"Main execution error: {e}", exc_info=True)


def print_summary(summary: dict):
    """Print processing summary with actual files created"""
    print("\n📋 Processing Summary:")
    print(f"   Total new reports: {summary['total_new_reports']}")
    print(f"   Total skipped (duplicates): {summary['total_skipped']}")
    print(f"   Batches created: {summary['batches_created']}")
    print(f"   Existing reports: {summary['existing_reports_count']}")

    print("\n📁 Files status:")
    if summary['total_new_reports'] > 0:
        print("   ✅ Raw data file: Updated with new reports")
        print("   ✅ Processed data file: Updated with new reports")
        print("   ✅ Processing log: Created")
    else:
        print("   📝 Raw data file: No changes (all reports were duplicates)")
        print("   📝 Processed data file: No changes (no new reports)")
        print("   ✅ Processing log: Created")

    print("\n📂 File locations:")
    print("   Raw data: data/raw/all_raw_reports.json")
    print("   Processed data: data/processed/all_processed_reports.json")
    print("   Logs: data/logs/")


def show_existing_reports(json_manager):
    """Show information about existing processed reports"""
    reports = json_manager.get_all_processed_reports()

    if not reports:
        print("📭 No processed reports found")
        return

    print(f"\n📚 Found {len(reports)} processed reports:")

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
