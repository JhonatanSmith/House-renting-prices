import requests
from bs4 import BeautifulSoup
import re
import time
import pandas as pd

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def extract_ad_info(url):
    """Fetch and parse a single ad URL, returning a dict of extracted fields or None on failure."""
    url = requests.utils.requote_uri(url)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed for {url}: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    info = {}

    # 1) Features (operation type, property type, rooms, bathrooms, area, year, estrato)
    features_section = soup.find("section", class_="features")
    if features_section:
        for item in features_section.find_all("li", class_="main-features__item"):
            key_tag = item.find("div", class_="key")
            val_tag = item.find("div", class_="value")
            if key_tag and val_tag:
                info[key_tag.get_text(strip=True)] = val_tag.get_text(strip=True)

    # 2) mapData from <script>
    script = next((t for t in soup.find_all("script") if t.string and "mapData" in t.string), None)
    if script:
        text = script.string
        info.update({
            "latitude":      re.search(r'latitude:\s*"([^"]+)"', text).group(1)   if re.search(r'latitude:\s*"([^"]+)"', text) else None,
            "longitude":     re.search(r'longitude:\s*"([^"]+)"', text).group(1)  if re.search(r'longitude:\s*"([^"]+)"', text) else None,
            "departament": re.search(r'province:\s*"([^"]+)"', text).group(1)   if re.search(r'province:\s*"([^"]+)"', text) else None,
            "city":       re.search(r'locality:\s*"([^"]+)"', text).group(1)   if re.search(r'locality:\s*"([^"]+)"', text) else None,
            "address":    re.search(r'address:\s*`([^`]+)`', text).group(1)     if re.search(r'address:\s*`([^`]+)`', text) else None,
        })

    # 3) Price
    price_tag = soup.find("span", class_="price__actual")
    if price_tag:
        raw = price_tag.get_text(strip=True)
        num = raw.replace("$","").replace(".","").replace("/mes","").strip()
        info["price"] = int(num) if num.isdigit() else None
    else:
        info["price"] = None

    # 4) Description
    desc_tag = soup.find("div", class_="content")
    info["description"] = desc_tag.get_text(strip=True) if desc_tag else None

    # 5) Parking
    park_tag = soup.find("span", class_="features__list__item__name")
    info["parking"] = 1 if park_tag and "aparcadero" in park_tag.get_text(strip=True).lower() else 0

    return info

def extract_all_ads(ad_urls, delay=0.5):
    """Given a list of ad URLs, returns a list of info dicts, pausing between requests."""
    results = []
    for url in ad_urls:
        data = extract_ad_info(url)
        if data:
            results.append(data)
        time.sleep(delay)
    return results

# 1) Collect all ad links from pages 1–100
all_ads = []
for i in range(1, 101):
    page_url = f"https://casas.trovit.com.co/arriendo-valle-aburra/?page={i}"
    try:
        r = requests.get(page_url, headers=HEADERS, timeout=8)
        r.raise_for_status()
    except Exception as e:
        print(f"⚠️ Skipping page {i}: {e}")
        continue

    soup = BeautifulSoup(r.text, "html.parser")
    page_links = [a['href'] for a in soup.select('.snippet-listing a[href]')]
    all_ads.extend(page_links)

# 2) Remove duplicates while preserving order
unique_ads = list(dict.fromkeys(all_ads))
#print(f"Total raw ads: {len(all_ads)}")
#print(f"Unique ads:    {len(unique_ads)}")

# 3) Scrape each ad and build DataFrame
ads_data = extract_all_ads(unique_ads)
df = pd.DataFrame(ads_data)

df.to_csv("trovit_casas.csv", index=False, encoding='utf-8')
print("DataFrame saved to CSV file successfully.")

