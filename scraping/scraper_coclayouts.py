import os
import time
import random
import subprocess
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

# --- Config ---
BASE_URL = "https://clashofclans-layouts.com/plans/th_18/"
SAVE_DIR = "data/raw/coclayouts/unlabeled"
IMG_BASE = "https://clashofclans-layouts.com"
TOTAL_PAGES = 13
DELAY = (1.0, 2.5)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def get_page_url(page):
    if page == 1:
        return BASE_URL
    return f"{BASE_URL}page_{page}/"


def get_image_urls(page):
    url = get_page_url(page)
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"  [!] Failed to load page {page}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    imgs = soup.find_all("img", class_="base_grid_img")

    urls = []
    for img in imgs:
        src = img.get("src", "")
        if "preview" in src:
            src = src.replace("preview", "thumb")
        if src:
            urls.append(IMG_BASE + src)

    return urls


def download_image(url, save_path):
    result = subprocess.run([
        "curl", "-L", "-o", save_path,
        "-H", f"Referer: {BASE_URL}",
        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "--silent", "--show-error",
        url
    ], capture_output=True, text=True)

    if result.returncode == 0 and os.path.exists(save_path) and os.path.getsize(save_path) > 0:
        return True
    else:
        print(f"  [!] curl failed for {url}: {result.stderr}")
        return False


def main():
    os.makedirs(SAVE_DIR, exist_ok=True)
    print("COC Layouts Scraper")
    print(f"Saving to: {os.path.abspath(SAVE_DIR)}")
    print(f"Total pages: {TOTAL_PAGES}")

    img_count = 0

    for page in range(1, TOTAL_PAGES + 1):
        print(f"\nPage {page}/{TOTAL_PAGES}...", end=" ", flush=True)
        urls = get_image_urls(page)

        if not urls:
            print("no images found, skipping")
            continue

        print(f"{len(urls)} images found")

        for url in tqdm(urls, desc="  Downloading", leave=False):
            filename = f"coclayouts_{img_count:04d}.jpg"
            save_path = os.path.join(SAVE_DIR, filename)

            if os.path.exists(save_path):
                img_count += 1
                continue

            success = download_image(url, save_path)
            if success:
                img_count += 1

            time.sleep(random.uniform(*DELAY))

        time.sleep(random.uniform(*DELAY))

    print(f"\n{'='*50}")
    print(f"Done! Total images scraped: {img_count}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()