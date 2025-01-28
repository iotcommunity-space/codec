import requests
import os
import json

# Constants
TTN_VENDOR_URL = "https://api.github.com/repos/TheThingsNetwork/lorawan-devices/contents/vendor"
LOCAL_CODEC_PATH = "assets/codecs"
CODECS_JSON_PATH = "assets/codecs.json"
SOURCE_URL = "https://github.com/TheThingsNetwork/lorawan-devices"
SOURCE_NAME = "The Things Network"

# Fetch GitHub token from environment variables
GITHUB_TOKEN = os.getenv("CODEC_TOKEN")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def fetch_github_content(url):
    """Fetch content from the provided GitHub URL."""
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch {url}, Status code: {response.status_code}")
        return []

def generate_unique_slug(slug, existing_slugs):
    """Generate a unique slug by appending a version suffix if needed."""
    if slug not in existing_slugs:
        return slug  # Return original if unique

    counter = 1
    new_slug = f"{slug}-v{counter}"
    while new_slug in existing_slugs:
        counter += 1
        new_slug = f"{slug}-v{counter}"

    return new_slug

def process_sensor(sensor_content, vendor_name, existing_slugs):
    """Process a single sensor and gather its metadata while ensuring unique slugs."""
    base_slug = f"ttn-smart-sensor-{vendor_name.lower().replace('_', '-')}"
    unique_slug = generate_unique_slug(base_slug, existing_slugs)

    sensor_metadata = {
        "name": f"TTN Smart Sensor ({vendor_name.title()})",
        "slug": unique_slug,
        "type": "Sensor",
        "description": f"Codec for {vendor_name.title()}",
        "source": SOURCE_URL,
        "sourceName": SOURCE_NAME,
        "image": None,
        "download": None,
        "readme": "No README available",
        "sourceRepo": f"{SOURCE_URL}/tree/master/vendor/{vendor_name}"
    }

    for item in sensor_content:
        if item['type'] == 'file':
            file_ext = item['name'].split('.')[-1].lower()
            file_url = item['download_url']

            if file_ext == "js":
                sensor_metadata["download"] = file_url
            elif file_ext == "png" and sensor_metadata["image"] is None:
                sensor_metadata["image"] = file_url

    return sensor_metadata, unique_slug

def sync_ttn_vendor(vendor_content, vendor_name, existing_slugs):
    """Sync all sensors within a given vendor, ensuring unique slugs."""
    sensor_metadata, new_slug = process_sensor(vendor_content, vendor_name, existing_slugs)
    existing_slugs.add(new_slug)  # Store the new slug to prevent future duplicates
    return sensor_metadata

def rewrite_codecs_json(new_codecs):
    """Safely update the codecs.json file while keeping existing data intact."""
    try:
        with open(CODECS_JSON_PATH, "r") as f:
            existing_codecs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_codecs = []

    existing_slugs = {codec["slug"] for codec in existing_codecs}

    for new_codec in new_codecs:
        if new_codec["slug"] not in existing_slugs:
            existing_codecs.append(new_codec)
            existing_slugs.add(new_codec["slug"])

    with open(CODECS_JSON_PATH, "w") as f:
        json.dump(existing_codecs, f, indent=2)

    print("Updated codecs.json successfully!")

def sync_ttn_codecs():
    """Main function to sync all TTN codecs."""
    vendors = fetch_github_content(TTN_VENDOR_URL)
    all_new_codecs = []

    try:
        with open(CODECS_JSON_PATH, "r") as f:
            existing_codecs = json.load(f)
            existing_slugs = {codec["slug"] for codec in existing_codecs}
    except (FileNotFoundError, json.JSONDecodeError):
        existing_slugs = set()

    for vendor in vendors:
        if vendor['type'] == 'dir':
            vendor_name = vendor['name']
            vendor_content = fetch_github_content(vendor['url'])
            vendor_metadata = sync_ttn_vendor(vendor_content, vendor_name, existing_slugs)
            all_new_codecs.append(vendor_metadata)

    rewrite_codecs_json(all_new_codecs)

if __name__ == "__main__":
    sync_ttn_codecs()
