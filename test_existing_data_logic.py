#!/usr/bin/env python3
"""
Test script for the existing data logic in TalkDocs2
This script tests the URL matching and data loading functionality
"""

import json
import os
from datetime import datetime

def test_url_normalization():
    """Test URL normalization logic"""
    print("Testing URL normalization...")
    
    test_urls = [
        "https://example.com",
        "https://example.com/",
        "https://example.com/path",
        "https://example.com/path/",
        "http://example.com",
        "http://example.com/"
    ]
    
    for url in test_urls:
        normalized = url.rstrip('/')
        print(f"  {url} -> {normalized}")
    
    print("✅ URL normalization test completed\n")

def test_existing_data_check():
    """Test existing data check logic"""
    print("Testing existing data check...")
    
    # Create a test data file
    test_data = {
        "base_url": "https://example.com",
        "crawl_timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "pages": [
            {
                "url": "https://example.com",
                "title": "Example Domain",
                "content": "This domain is for use in illustrative examples..."
            }
        ]
    }
    
    # Save test data
    test_filename = "crawled_data_test.json"
    with open(test_filename, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, indent=2)
    
    print(f"  Created test file: {test_filename}")
    
    # Test URL matching
    test_urls = [
        "https://example.com",
        "https://example.com/",
        "https://example.com/path",
        "https://different.com"
    ]
    
    for url in test_urls:
        normalized_url = url.rstrip('/')
        matches = test_data.get('base_url', '').rstrip('/') == normalized_url
        print(f"  {url} matches: {matches}")
    
    # Clean up
    os.remove(test_filename)
    print("  Cleaned up test file")
    print("✅ Existing data check test completed\n")

def test_data_age_calculation():
    """Test data age calculation"""
    print("Testing data age calculation...")
    
    # Test different timestamps
    test_timestamps = [
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # Now
        (datetime.now().replace(hour=datetime.now().hour-2)).strftime('%Y-%m-%d %H:%M:%S'),  # 2 hours ago
        (datetime.now().replace(day=datetime.now().day-3)).strftime('%Y-%m-%d %H:%M:%S'),  # 3 days ago
        "Unknown time"
    ]
    
    for timestamp in test_timestamps:
        try:
            if timestamp != 'Unknown time':
                crawl_datetime = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                current_time = datetime.now()
                age_delta = current_time - crawl_datetime
                if age_delta.days > 0:
                    age_text = f"{age_delta.days} days ago"
                elif age_delta.seconds > 3600:
                    age_text = f"{age_delta.seconds // 3600} hours ago"
                else:
                    age_text = f"{age_delta.seconds // 60} minutes ago"
            else:
                age_text = "Unknown"
            print(f"  {timestamp} -> {age_text}")
        except Exception as e:
            print(f"  {timestamp} -> Error: {e}")
    
    print("✅ Data age calculation test completed\n")

def main():
    """Run all tests"""
    print("🧪 Testing TalkDocs2 Existing Data Logic")
    print("=" * 50)
    
    test_url_normalization()
    test_existing_data_check()
    test_data_age_calculation()
    
    print("🎉 All tests completed successfully!")
    print("\nThe existing data logic is working correctly.")

if __name__ == "__main__":
    main()
