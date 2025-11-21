import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import urllib.parse
import time
import random

class KleinanzeigenScraper:
    def __init__(self):
        self.base_url = "https://www.kleinanzeigen.de"
        self.ua = UserAgent()
        self.session = requests.Session()

    def get_headers(self):
        return {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "de,en-US;q=0.7,en;q=0.3",
            "Referer": "https://www.kleinanzeigen.de/",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

    def search(self, query, location=None, radius=None, category_id="0"):
        """
        Führt eine Suche durch.
        """
        # Use the explicit search endpoint to avoid path issues
        base_search_url = "https://www.kleinanzeigen.de/s-suchanfrage.html"
        
        params = {
            "keywords": query,
            "locationStr": location,
            "categoryId": category_id if category_id != "0" else "",
            "radius": radius if radius and str(radius) != "0" else ""
        }
        
        # Remove empty params
        params = {k: v for k, v in params.items() if v}
        
        print(f"Scraping Search: {params}")
        
        try:
            time.sleep(random.uniform(1, 3)) # Be nice
            response = self.session.get(base_search_url, params=params, headers=self.get_headers())
            print(f"Status Code: {response.status_code}")
            # print(f"Final URL: {response.url}") # Debug
            response.raise_for_status()
            
            results = self.parse_results(response.text)
            print(f"Parsed {len(results)} results.")
            
            if len(results) == 0:
                with open("debug_last_response.html", "w", encoding="utf-8") as f:
                    f.write(response.text)
                print("Saved HTML to debug_last_response.html")
                
            return results
        except Exception as e:
            print(f"Error scraping: {e}")
            return []

    def get_ad_details(self, url):
        """
        Lädt die Detailseite einer Anzeige und gibt die Beschreibung zurück.
        """
        try:
            time.sleep(random.uniform(0.5, 1.5)) # Delay to avoid blocking
            response = self.session.get(url, headers=self.get_headers())
            if response.status_code != 200:
                return ""
            
            soup = BeautifulSoup(response.text, 'html.parser')
            desc_elem = soup.find('div', id='viewad-description-text')
            if desc_elem:
                return desc_elem.get_text().strip()
            return ""
        except Exception as e:
            print(f"Error fetching details {url}: {e}")
            return ""

    def parse_results(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # Try Desktop structure first
        ad_list = soup.find('ul', id='srchrslt-adtable')
        if ad_list:
            for ad in ad_list.find_all('li', class_='ad-listitem'):
                if 'is-topad' in ad.get('class', []):
                    continue 

                article = ad.find('article')
                if not article:
                    continue

                ad_id = article.get('data-adid')
                link_elem = article.find('a', class_='ellipsis')
                
                if not link_elem:
                    continue
                    
                title = link_elem.get_text().strip()
                link = self.base_url + link_elem.get('href')
                
                price_elem = article.find('p', class_='aditem-main--middle--price-shipping--price')
                price = price_elem.get_text().strip() if price_elem else "VB"
                
                location_elem = article.find('div', class_='aditem-main--top--left')
                location = location_elem.get_text().strip() if location_elem else ""

                img_elem = article.find('img')
                image_url = img_elem.get('src') if img_elem else None

                results.append({
                    'id': ad_id,
                    'title': title,
                    'price': price,
                    'link': link,
                    'location': location,
                    'image': image_url
                })
            return results

        # Try Mobile/Alternative structure
        ad_list_alt = soup.find('ul', id='srp-results')
        if ad_list_alt:
            for ad in ad_list_alt.find_all('li', class_='adlist--item'):
                ad_id = ad.get('data-adid')
                if not ad_id:
                    continue
                    
                # Title & Link
                title_elem = ad.find('strong', class_='adlist--item--boldtitle')
                if title_elem and title_elem.find('a'):
                    link_a = title_elem.find('a')
                    title = link_a.get_text().strip()
                    link = self.base_url + link_a.get('href')
                else:
                    # Fallback
                    link_path = ad.get('data-href')
                    link = self.base_url + link_path if link_path else ""
                    title = "Unbekannt"

                # Price
                price_elem = ad.find('div', class_='adlist--item--price')
                price = price_elem.get_text().strip() if price_elem else "VB"
                
                # Location
                location_elem = ad.find('div', class_='adlist--item--info--location')
                location = location_elem.get_text().strip() if location_elem else ""
                
                # Image
                img_elem = ad.find('img')
                image_url = img_elem.get('src') if img_elem else None

                results.append({
                    'id': ad_id,
                    'title': title,
                    'price': price,
                    'link': link,
                    'location': location,
                    'image': image_url
                })
            return results
            
        return results

if __name__ == "__main__":
    # Test run
    scraper = KleinanzeigenScraper()
    results = scraper.search("iphone 13", "Berlin")
    for res in results:
        print(res)
