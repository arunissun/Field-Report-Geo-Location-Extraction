"""
Test functions for the GO API client with JSON storage
"""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.go_api_client import GOAPIClient
from src.json_manager import JSONManager
from src.config import config


def test_api_connection():
    """Test basic API connection and authentication"""
    print("🧪 Testing API Connection...")

    try:
        client = GOAPIClient()
        print("✅ Client initialized successfully")

        # Test single page fetch
        data = client.fetch_field_reports_page(limit=5, offset=0)

        if data and 'results' in data:
            print(
                f"✅ API connection successful! Found {len(data['results'])} reports"
            )
            print(f"📊 Total available: {data.get('count', 'unknown')}")
            return True
        else:
            print("❌ API returned unexpected data format")
            return False

    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False


def test_json_storage():
    """Test JSON file operations"""
    print("\n🧪 Testing JSON Storage...")

    try:
        json_manager = JSONManager(config)

        # Test saving sample data
        sample_reports = [{
            'id': 12345,
            'go_api_id': 12345,
            'title': 'Test Report',
            'description': 'Test description',
            'summary': 'Test summary',
            'status': 'fetched'
        }]

        filepath = json_manager.save_processed_reports(sample_reports, 999)
        print(f"✅ Successfully saved test data to {filepath}")

        # Test loading data
        loaded_reports = json_manager.load_processed_reports(filepath)
        if len(loaded_reports) == 1:
            print("✅ Successfully loaded test data")
            return True
        else:
            print("❌ Failed to load test data correctly")
            return False

    except Exception as e:
        print(f"❌ JSON storage test failed: {e}")
        return False


def test_data_fetching():
    """Test actual data fetching and processing"""
    print("\n🧪 Testing Data Fetching and Processing...")

    try:
        client = GOAPIClient()

        # Fetch a small batch
        summary = client.fetch_and_save_all_reports(max_reports=10)

        print("\n📄 Sample processed report:")
        print(f"   Total new reports: {summary['total_new_reports']}")
        print(f"   Batches created: {summary['batches_created']}")

        # Show sample processed data
        json_manager = JSONManager(config)
        all_reports = json_manager.get_all_processed_reports()

        if all_reports:
            sample = all_reports[0]
            print("\n📄 Sample processed report:")
            print(f"   ID: {sample.get('go_api_id')}")
            print(f"   Title: {sample.get('title', '')[:80]}...")
            print(f"   Summary: {sample.get('summary', '')[:80]}...")

        return True

    except Exception as e:
        print(f"❌ Data fetching test failed: {e}")
        return False


def run_all_tests():
    """Run all tests and provide summary"""
    print("🚀 Starting Field Reports JSON Pipeline Tests...\n")

    tests = [("API Connection", test_api_connection),
             ("JSON Storage", test_json_storage),
             ("Data Fetching", test_data_fetching)]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))

    # Print summary
    print("\n" + "=" * 50)
    print("🏁 TEST SUMMARY")
    print("=" * 50)

    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1

    print(f"\n📊 Results: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("🎉 All tests passed! Your JSON-based pipeline is ready!")
    else:
        print(
            "⚠️ Some tests failed. Please check your configuration and network connection."
        )


if __name__ == "__main__":
    run_all_tests()
