import json
import threading
import time
import os
from plyer import notification
from scraper import KleinanzeigenScraper

CONFIG_FILE = "config.json"

class SearchManager:
    def __init__(self):
        self.scraper = KleinanzeigenScraper()
        self.searches = []
        self.seen_ads = set()
        self.running = False
        self.thread = None
        self.interval = 60 * 5  # 5 Minutes default
        self.load_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.searches = data.get('searches', [])
                    self.seen_ads = set(data.get('seen_ads', []))
                    self.interval = data.get('interval', 300)
            except Exception as e:
                print(f"Error loading config: {e}")
        self.found_ads = [] # Store found ads in memory for the session

    def save_config(self):
        data = {
            'searches': self.searches,
            'seen_ads': list(self.seen_ads),
            'interval': self.interval
        }
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def add_search(self, query, location, radius, category_id="0", filter_keywords=None, notifications=True):
        self.searches.append({
            'query': query,
            'location': location,
            'radius': radius,
            'category_id': category_id,
            'filter_keywords': filter_keywords or [], 
            'active': True,
            'notifications': notifications,
            'first_run': True # Suppress notifications on first run
        })
        self.save_config()

    def remove_search(self, index):
        if 0 <= index < len(self.searches):
            del self.searches[index]
            self.save_config()

    def toggle_notifications(self, index):
        if 0 <= index < len(self.searches):
            self.searches[index]['notifications'] = not self.searches[index].get('notifications', True)
            self.save_config()

    def start_monitoring(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        print("Monitoring started.")

    def stop_monitoring(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        print("Monitoring stopped.")

    def _loop(self):
        while self.running:
            print("Checking for new ads...")
            for search in self.searches:
                if not search.get('active', True):
                    continue
                
                query = search['query']
                location = search['location']
                radius = search['radius']
                category_id = search.get('category_id', "0")
                filter_keywords = search.get('filter_keywords', [])
                notifications_enabled = search.get('notifications', True)
                first_run = search.get('first_run', False)
                
                print(f"Searching for {query} in {location} (Cat: {category_id})")
                results = self.scraper.search(query, location, radius, category_id)
                
                print(f"Found {len(results)} ads for {query}")
                
                new_count = 0
                for ad in results:
                    # STRICT CHECK: The main query MUST be present in Title or Description
                    match_query = False
                    if query.lower() in ad['title'].lower():
                        match_query = True
                    else:
                        print(f"Query '{query}' not in title '{ad['title']}', checking description...")
                        desc = self.scraper.get_ad_details(ad['link'])
                        if query.lower() in desc.lower():
                            match_query = True
                    
                    if not match_query:
                        continue

                    # Check filter keywords if present
                    if filter_keywords:
                        match_filter = False
                        if any(k.lower() in ad['title'].lower() for k in filter_keywords):
                            match_filter = True
                        else:
                            print(f"Checking description for filter in {ad['title']}...")
                            desc = self.scraper.get_ad_details(ad['link'])
                            if any(k.lower() in desc.lower() for k in filter_keywords):
                                match_filter = True
                        
                        if not match_filter:
                            continue 

                    # Add to session results if not already present
                    if not any(existing['id'] == ad['id'] for existing in self.found_ads):
                        self.found_ads.append(ad)

                    ad_id = ad['id']
                    if ad_id not in self.seen_ads:
                        self.seen_ads.add(ad_id)
                        new_count += 1
                        
                        # Notify only if enabled and NOT first run
                        if notifications_enabled and not first_run:
                            self.notify_new_ad(ad)
                
                if new_count > 0:
                    print(f"Found {new_count} new ads for {query}")
                
                # After processing, disable first_run flag
                if first_run:
                    search['first_run'] = False
                    self.save_config() # Persist the change so we don't skip next time if restarted immediately (though first_run is usually transient)
                
                # Short pause between searches
                time.sleep(5)
            
            self.save_config()
            
            # Wait for interval
            for _ in range(self.interval):
                if not self.running:
                    break
                time.sleep(1)

    def notify_new_ad(self, ad):
        try:
            notification.notify(
                title=f"Neues Angebot: {ad['title'][:30]}...",
                message=f"{ad['price']} - {ad['location']}\n{ad['title']}",
                app_name="Kleinanzeigen Bot",
                timeout=10
            )
        except Exception as e:
            print(f"Notification error: {e}")

if __name__ == "__main__":
    # Test
    mgr = SearchManager()
    mgr.add_search("Test", "Berlin", 0)
    print(mgr.searches)
