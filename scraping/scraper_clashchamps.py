import os
import time
import random
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc

BASE_URL = "https://www.clashchamps.com/i-need-a-base/"
SAVE_DIR = "data/raw"
TOWN_HALL = 18
PAGE_DELAY = (2.0, 4.0)   
IMG_DELAY  = (0.5, 1.5)   
MAX_EMPTY_PAGES = 3

ARCHETYPES = {
    "anti_3star": 1,
    "box":        2,
    "diamond":    3,
    "ring":       4,
}


def build_url(archetype_id, page):
    return (
        f"{BASE_URL}?search_keyword=&search_village="
        f"&search_player_townhalls={TOWN_HALL}"
        f"&base_style%5B0%5D={archetype_id}"
        f"&my_bases=0&order_by=1&submit=SEARCH&pag={page}"
    )


def make_driver():
    options = uc.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    driver = uc.Chrome(options=options, headless=False, version_main=145)
    return driver


def get_image_urls(driver, archetype_id, page):
    url = build_url(archetype_id, page)
    driver.get(url)
    time.sleep(5)  

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[data-rel*='lightbox']"))
        )
    except Exception:
        return []

    soup = BeautifulSoup(driver.page_source, "html.parser")
    anchors = soup.find_all("a", attrs={"data-rel": lambda v: v and "lightbox" in v})

    urls = []
    for a in anchors:
        href = a.get("href", "")
        if "imagedelivery" in href and "image1920" in href:
            urls.append(href)

    return urls


def download_image(url, save_path):
    import subprocess
    result = subprocess.run([
        "curl", "-L", "-o", save_path,
        "-H", "Referer: https://www.clashchamps.com/",
        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "--silent", "--show-error",
        url
    ], capture_output=True, text=True)
    
    if result.returncode == 0 and os.path.exists(save_path) and os.path.getsize(save_path) > 0:
        return True
    else:
        print(f"  [!] curl failed: {result.stderr}")
        return False

def scrape_archetype(driver, archetype_name, archetype_id):
    save_dir = os.path.join(SAVE_DIR, archetype_name)
    os.makedirs(save_dir, exist_ok=True)

    print(f"\n{'='*50}")
    print(f"Scraping: {archetype_name} (id={archetype_id})")
    print(f"{'='*50}")

    img_count = 0
    empty_streak = 0
    page = 1

    while empty_streak < MAX_EMPTY_PAGES:
        print(f"  Page {page}...", end=" ", flush=True)

        urls = get_image_urls(driver, archetype_id, page)

        if not urls:
            empty_streak += 1
            print(f"empty ({empty_streak}/{MAX_EMPTY_PAGES})")
        else:
            empty_streak = 0
            print(f"{len(urls)} images found")

            for url in tqdm(urls, desc="    Downloading", leave=False):
                filename = f"{archetype_name}_{img_count:04d}.jpg"
                save_path = os.path.join(save_dir, filename)

                if os.path.exists(save_path):
                    img_count += 1
                    continue

                success = download_image(url, save_path)
                if success:
                    img_count += 1

                time.sleep(random.uniform(*IMG_DELAY))

        page += 1
        time.sleep(random.uniform(*PAGE_DELAY))

    print(f"  Done. Total downloaded: {img_count} images")
    return img_count


def main():
    print("Clash Champs Base Scraper (Selenium)")
    print(f"Town Hall: {TOWN_HALL}")
    print(f"Saving to: {os.path.abspath(SAVE_DIR)}")

    driver = make_driver()

    try:
        total = 0
        for archetype_name, archetype_id in ARCHETYPES.items():
            count = scrape_archetype(driver, archetype_name, archetype_id)
            total += count
    finally:
        driver.quit()

    print(f"\n{'='*50}")
    print(f"All done! Total images scraped: {total}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()