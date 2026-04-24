from pathlib import Path
from urllib.parse import quote
from urllib.parse import quote_plus
from urllib.parse import urlparse
import time

import requests

from database import get_session
from models import Product


IMAGE_DIR = Path(__file__).resolve().parent / "static" / "product_images"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)
HEADERS = {
    "User-Agent": "mba-project-image-fetcher/1.0 (educational project)",
    "Accept": "application/json,image/*,*/*",
}

SKU_WIKIPEDIA_TITLES = {
    "SKU-001": ["Laptop", "Notebook_computer"],
    "SKU-002": ["Smartphone", "Mobile_phone"],
    "SKU-003": ["Headphones"],
    "SKU-004": ["Messenger_bag", "Backpack"],
    "SKU-005": ["USB_hub", "Universal_Serial_Bus"],
    "SKU-006": ["Computer_mouse"],
    "SKU-007": ["Computer_keyboard"],
    "SKU-008": ["Computer_monitor"],
    "SKU-009": ["Webcam"],
    "SKU-010": ["Mobile_phone_case", "Smartphone"],
    "SKU-011": ["Screen_protector", "Tempered_glass"],
    "SKU-012": ["Wireless_power_transfer", "Qi_(standard)"],
    "SKU-013": ["Battery_charger", "Lithium-ion_battery"],
    "SKU-014": ["Smartwatch"],
    "SKU-015": ["Earphone", "Headphones"],
    "SKU-016": ["HDMI"],
    "SKU-017": ["SD_card"],
    "SKU-018": ["Solid-state_drive", "Hard_disk_drive"],
    "SKU-019": ["Desk_lamp", "Lamp"],
    "SKU-020": ["Mousepad", "Computer_mouse"],
}

SKU_FALLBACK_KEYWORDS = {
    "SKU-001": "laptop computer",
    "SKU-002": "smartphone",
    "SKU-003": "headphones",
    "SKU-004": "laptop bag",
    "SKU-005": "usb hub",
    "SKU-006": "computer mouse",
    "SKU-007": "keyboard",
    "SKU-008": "monitor",
    "SKU-009": "webcam",
    "SKU-010": "phone case",
    "SKU-011": "screen protector",
    "SKU-012": "wireless charger",
    "SKU-013": "power bank",
    "SKU-014": "smartwatch",
    "SKU-015": "earbuds",
    "SKU-016": "hdmi cable",
    "SKU-017": "sd card",
    "SKU-018": "external ssd",
    "SKU-019": "desk lamp",
    "SKU-020": "mouse pad",
}

SKU_OVERRIDE_URLS = {
    "SKU-010": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/CMF_PHONE_ONE_BACK_COVER_INSIDE.jpg/960px-CMF_PHONE_ONE_BACK_COVER_INSIDE.jpg",
    "SKU-019": "https://upload.wikimedia.org/wikipedia/commons/5/53/Anglepoise1227.jpg",
    "SKU-020": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/HP_mouse_and_mousepad_20060803.jpg/330px-HP_mouse_and_mousepad_20060803.jpg",
}


def extract_extension(url: str) -> str:
    path = urlparse(url).path.lower()
    if path.endswith(".png"):
        return ".png"
    if path.endswith(".webp"):
        return ".webp"
    return ".jpg"


def wikipedia_thumbnail_url(page_title: str):
    encoded = quote(page_title)
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    payload = response.json()

    thumb = payload.get("thumbnail", {}).get("source")
    original = payload.get("originalimage", {}).get("source")
    return thumb or original


def image_source_url(sku: str):
    if sku in SKU_OVERRIDE_URLS:
        return SKU_OVERRIDE_URLS[sku]

    titles = SKU_WIKIPEDIA_TITLES.get(sku, ["Consumer_electronics"])
    for title in titles:
        try:
            candidate = wikipedia_thumbnail_url(title)
            if candidate:
                return candidate
        except Exception:
            continue
    return None


def fallback_image_url(sku: str):
    keyword = SKU_FALLBACK_KEYWORDS.get(sku, "consumer electronics")
    encoded = quote_plus(keyword)
    lock_id = int(sku.split("-")[-1])
    return f"https://loremflickr.com/900/600/{encoded}?lock={lock_id}"


def download_image(url: str, output_path: Path) -> bool:
    last_error = None
    for attempt in range(3):
        try:
            response = requests.get(url, headers=HEADERS, timeout=20)
            response.raise_for_status()
            output_path.write_bytes(response.content)
            return output_path.exists() and output_path.stat().st_size > 0
        except Exception as exc:
            last_error = exc
            time.sleep(1.1 + attempt)
    raise last_error


def main():
    db = get_session()
    try:
        products = db.query(Product).order_by(Product.sku.asc()).all()
        if not products:
            print("No products found in database. Upload CSV first using admin flow.")
            return

        ok_count = 0
        fail_count = 0

        for product in products:
            source = image_source_url(product.sku)
            used_fallback = False
            if not source:
                source = fallback_image_url(product.sku)
                used_fallback = True

            ext = extract_extension(source)
            target = IMAGE_DIR / f"{product.sku}{ext}"

            try:
                for existing in IMAGE_DIR.glob(f"{product.sku}.*"):
                    if existing != target:
                        existing.unlink(missing_ok=True)

                download_image(source, target)
                product.image_url = f"/media/products/{product.sku}{ext}"
                ok_count += 1
                mode = "fallback" if used_fallback else "wikipedia"
                print(f"Downloaded {product.sku} -> {target.name} [{mode}] ({source})")
            except Exception as exc:
                try:
                    fallback = fallback_image_url(product.sku)
                    ext = extract_extension(fallback)
                    target = IMAGE_DIR / f"{product.sku}{ext}"
                    download_image(fallback, target)
                    product.image_url = f"/media/products/{product.sku}{ext}"
                    ok_count += 1
                    print(f"Downloaded {product.sku} -> {target.name} [fallback] ({fallback})")
                except Exception as fallback_exc:
                    fail_count += 1
                    print(f"Failed {product.sku}: wiki_err={exc} fallback_err={fallback_exc}")

            time.sleep(0.7)

        db.commit()
        print(f"Done. Success: {ok_count}, Failed: {fail_count}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
