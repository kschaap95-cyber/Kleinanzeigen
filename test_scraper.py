from scraper import KleinanzeigenScraper

def test_scraper():
    scraper = KleinanzeigenScraper()
    print("Testing scraper...")
    # Use a very common term to ensure results
    results = scraper.search("iphone", "Berlin")
    
    if results:
        print(f"Success! Found {len(results)} ads.")
        print("First ad:")
        print(results[0])
    else:
        print("No results found or scraping failed.")

if __name__ == "__main__":
    test_scraper()
