import requests
import os
import json

# Constants
DRAGINO_BASE_URL = "https://api.github.com/repos/dragino/dragino-end-node-decoder/contents"
LOCAL_CODEC_PATH = "assets/codecs"
CODECS_JSON_PATH = "assets/codecs.json"
DEFAULT_VERSION = "v1.0.0"
SOURCE = "https://github.com/dragino/dragino-end-node-decoder"
SOURCE_NAME = "Dragino"

# Fetch the GitHub token from environment variables
GITHUB_TOKEN = os.getenv("CODEC_TOKEN")

# Set up headers for authentication
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}


def fetch_github_content(url):
    """Fetch content from the provided GitHub URL with authentication."""
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch content from {url}. Status code: {response.status_code}")
    return []


def validate_file_exists(url):
    """Check if a file exists at the provided URL."""
    response = requests.head(url, headers=HEADERS)
    return response.status_code == 200


def download_file(file_url, save_path):
    """Download the file from the provided URL to the specified path with authentication."""
    response = requests.get(file_url, headers=HEADERS)
    if response.status_code == 200:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as file:
            file.write(response.content)
        print(f"Downloaded: {save_path}")
    else:
        print(f"Failed to download {file_url}. Status code: {response.status_code}")


def process_folder(folder, parent_path):
    """Process a folder, fetch its content, and sync all files and subfolders."""
    folder_content = fetch_github_content(folder['url'])
    local_sensor_path = os.path.join(LOCAL_CODEC_PATH, parent_path, folder['name'], DEFAULT_VERSION)
    metadata = []

    for item in folder_content:
        if item['type'] == 'file':
            file_extension = item['name'].split('.')[-1]
            if file_extension in ['txt', 'js', 'py']:
                download_url = item['download_url']
                download_path = os.path.join(local_sensor_path, item['name'])
                download_file(download_url, download_path)
                metadata.append((item['name'], download_url))

    return metadata


def fetch_all_sensors():
    """Fetch all sensors and their subfolders."""
    sensors = fetch_github_content(DRAGINO_BASE_URL)
    all_sensor_metadata = []

    for sensor in sensors:
        if sensor['type'] == 'dir':
            parent_folder_name = sensor['name']
            parent_folder_content = fetch_github_content(sensor['url'])

            for subfolder in parent_folder_content:
                if subfolder['type'] == 'dir':
                    sensor_metadata = process_folder(subfolder, parent_folder_name)
                    for filename, download_url in sensor_metadata:
                        all_sensor_metadata.append({
                            "parent_folder": parent_folder_name,
                            "subfolder": subfolder['name'],
                            "filename": filename,
                            "download_url": download_url
                        })

    return all_sensor_metadata


def rewrite_codecs_json(all_sensor_metadata):
    """Rewrite the codecs.json file with the updated sensor information."""
    # Load existing codecs.json
    if os.path.exists(CODECS_JSON_PATH):
        with open(CODECS_JSON_PATH, "r") as f:
            existing_codecs = json.load(f)
    else:
        existing_codecs = []

    # Build a mapping for duplicates
    existing_slugs = {entry['slug']: entry for entry in existing_codecs}

    new_entries = []

    for metadata in all_sensor_metadata:
        slug = f"{metadata['parent_folder'].lower()}-{metadata['subfolder'].lower()}"
        download_url = metadata["download_url"]

        # Validate if file exists
        if not validate_file_exists(download_url):
            print(f"File missing: {download_url}")
            continue

        # Construct entry
        entry = {
            "name": f"DRAGINO - {metadata['subfolder']}",
            "slug": slug,
            "type": "Sensor",
            "description": f"Codec for DRAGINO - {metadata['subfolder']} ({DEFAULT_VERSION}).",
            "download": download_url,
            "source": SOURCE,
            "sourceName": SOURCE_NAME,
            "image": f"https://raw.githubusercontent.com/iotcommunity-space/codec/refs/heads/main/assets/codecs/{metadata['parent_folder']}/{metadata['subfolder']}/{DEFAULT_VERSION}/assets/logo.png",
            "sourceRepo": f"{SOURCE}/{metadata['parent_folder']}/{metadata['subfolder']}"
        }

        # Handle duplicates: prefer the newer or more complete entry
        if slug in existing_slugs:
            existing_entry = existing_slugs[slug]
            if len(existing_entry.get("description", "")) < len(entry["description"]):
                new_entries.append(entry)
            else:
                new_entries.append(existing_entry)
        else:
            new_entries.append(entry)

    # Write to codecs.json
    with open(CODECS_JSON_PATH, "w") as f:
        json.dump(new_entries, f, indent=2)
    print("Rewritten codecs.json successfully.")


def sync_dragino_codecs():
    """Sync all Dragino codecs from the remote repository to the local repository."""
    all_sensor_metadata = fetch_all_sensors()
    rewrite_codecs_json(all_sensor_metadata)


if __name__ == "__main__":
    sync_dragino_codecs()
