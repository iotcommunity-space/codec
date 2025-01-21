import requests
import os
import json

# Constants
MILESIGHT_BASE_URL = "https://api.github.com/repos/Milesight-IoT/SensorDecoders/contents"
LOCAL_CODEC_PATH = "assets/codecs"
CODECS_JSON_PATH = "assets/codecs.json"
SOURCE_URL = "https://github.com/Milesight-IoT/SensorDecoders"
SOURCE_NAME = "Milesight-IoT"

# GitHub token for API authentication (reusing the same token as TagoIO)
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


def download_file(file_url, save_path):
    """Download a file and save it locally."""
    response = requests.get(file_url, headers=HEADERS)
    if response.status_code == 200:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(response.content)
        print(f"Downloaded: {save_path}")
    else:
        print(f"Failed to download {file_url}, Status code: {response.status_code}")


def process_sensor(sensor_content, series_name, sensor_name):
    """Process a single sensor and gather its metadata."""
    local_sensor_path = os.path.join(LOCAL_CODEC_PATH, series_name, sensor_name)
    sensor_metadata = {
        "name": f"{series_name.replace('_', ' ').title()} - {sensor_name.replace('_', ' ').title()}",
        "slug": f"{series_name.lower()}-{sensor_name.lower()}".replace("_", "-"),
        "type": "Sensor",
        "description": f"Codec for {series_name.replace('_', ' ').title()} - {sensor_name.replace('_', ' ').title()}.",
        "source": SOURCE_URL,
        "sourceName": SOURCE_NAME,
        "image": None,
        "download": None,
        "readme": "No README available",
        "sourceRepo": f"{SOURCE_URL}/tree/main/{series_name}/{sensor_name}"
    }

    for item in sensor_content:
        if item['type'] == 'file':
            file_path = os.path.join(local_sensor_path, item['name'])
            download_file(item['download_url'], file_path)

            if item['name'].endswith(".js"):
                sensor_metadata["download"] = item['download_url']
            elif item['name'].endswith(".png") and sensor_metadata["image"] is None:
                sensor_metadata["image"] = item['download_url']
            elif item['name'].endswith(".md"):
                sensor_metadata["readme"] = item['download_url']

    return sensor_metadata


def sync_milesight_series(series_content, series_name):
    """Sync all sensors within a given series."""
    all_sensors_metadata = []
    for sensor in series_content:
        if sensor['type'] == 'dir':
            sensor_content = fetch_github_content(sensor['url'])
            sensor_metadata = process_sensor(sensor_content, series_name, sensor['name'])
            all_sensors_metadata.append(sensor_metadata)
    return all_sensors_metadata


def remove_duplicates_and_merge(existing_codecs, new_codecs):
    """Merge new codecs into the existing JSON, resolving duplicates."""
    merged_codecs = {c['slug']: c for c in existing_codecs}

    for codec in new_codecs:
        slug = codec['slug']
        if slug in merged_codecs:
            # Merge intelligently: pick the most complete entry
            merged_codecs[slug] = max(merged_codecs[slug], codec, key=lambda x: len(json.dumps(x)))
        else:
            merged_codecs[slug] = codec

    return list(merged_codecs.values())


def rewrite_codecs_json(new_codecs):
    """Rewrite the codecs.json file with merged codecs."""
    # Load existing codecs.json
    try:
        with open(CODECS_JSON_PATH, "r") as f:
            existing_codecs = json.load(f)
    except FileNotFoundError:
        existing_codecs = []

    # Merge with new codecs
    merged_codecs = remove_duplicates_and_merge(existing_codecs, new_codecs)

    # Write back to codecs.json
    with open(CODECS_JSON_PATH, "w") as f:
        json.dump(merged_codecs, f, indent=2)
    print("Updated codecs.json successfully!")


def sync_milesight_codecs():
    """Main function to sync all Milesight codecs."""
    series_content = fetch_github_content(MILESIGHT_BASE_URL)
    all_new_codecs = []

    for series in series_content:
        if series['type'] == 'dir':
            series_name = series['name']
            series_content = fetch_github_content(series['url'])
            series_metadata = sync_milesight_series(series_content, series_name)
            all_new_codecs.extend(series_metadata)

    # Update the codecs.json file
    rewrite_codecs_json(all_new_codecs)


if __name__ == "__main__":
    sync_milesight_codecs()
