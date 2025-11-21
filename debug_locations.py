"""
Quick debug script to check location strings in found_ads
"""
import json

try:
    with open('config.json', 'r') as f:
        data = json.load(f)
        
    print("Sample location strings from config:")
    print("-" * 50)
    
    # Check if there are any seen ads or searches with location info
    if 'searches' in data:
        for search in data['searches'][:3]:  # First 3 searches
            print(f"Search location: {search.get('location', 'N/A')}")
    
    print("\nNote: Location strings from actual ads are stored in memory during runtime.")
    print("To see actual ad locations, check the console output when the bot runs.")
    
except FileNotFoundError:
    print("config.json not found")
except Exception as e:
    print(f"Error: {e}")
