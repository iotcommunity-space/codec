import requests
import os
import json

# Constants
TAGOIO_BASE_URL = "https://api.github.com/repos/tago-io/decoders/contents/decoders/connector"
LOCAL_CODEC_PATH = "assets/codecs"
CODECS_JSON_PATH = "assets/codecs.json"
CODEC_REPO_URL = "https://github.com/tago-io/decoders/tree/main/decoders/connector"
DEFAULT_VERSION = "v1.0.0"

# GitHub token for authentication
GITHUB_TOKEN = os.getenv("CODEC_TOKEN")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}


def fetch_github_content(url):
    """Fetch content from GitHub."""
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch content from {url}. Status: {response.status_code}")
        return []


def download_file(file_url, save_path):
    """Download file to local directory."""
    response = requests.get(file_url, headers=HEADERS)
    if response.status_code == 200:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(response.content)
        print(f"Downloaded: {save_path}")
    else:
        print(f"Failed to download {file_url}. Status: {response.status_code}")


def sync_sensor_files(folder_content, local_sensor_path):
    """Download all codec files in a sensor directory."""
    for item in folder_content:
        path = os.path.join(local_sensor_path, item['name'])
        if item['type'] == 'file':
            download_file(item['download_url'], path)
        elif item['type'] == 'dir':
            subfolder_content = fetch_github_content(item['url'])
            sync_sensor_files(subfolder_content, path)


def process_folder(folder, parent_path):
    """Sync a single sensor folder."""
    local_sensor_path = os.path.join(LOCAL_CODEC_PATH, parent_path, folder['name'], DEFAULT_VERSION)
    folder_content = fetch_github_content(folder['url'])
    sync_sensor_files(folder_content, local_sensor_path)
    return folder['name']


def fetch_all_sensors():
    """Fetch all folders from TagoIO codec repository."""
    sensors = fetch_github_content(TAGOIO_BASE_URL)
    all_sensor_folders = {}

    for sensor in sensors:
        if sensor['type'] == 'dir':
            parent = sensor['name']
            parent_content = fetch_github_content(sensor['url'])
            subfolders = []

            for subfolder in parent_content:
                if subfolder['type'] == 'dir':
                    subfolders.append(process_folder(subfolder, parent))

            all_sensor_folders[parent] = subfolders

    return all_sensor_folders


def rewrite_codecs_json(all_sensor_folders):
    """Merge synced codecs with existing custom ones, avoiding duplicates."""
    new_entries = []
    synced_slugs = set()

    # Create entries from synced TagoIO codecs
    for parent_folder, subfolders in all_sensor_folders.items():
        for subfolder in subfolders:
            slug = f"{parent_folder.lower()}-{subfolder.lower()}".replace(" ", "-").replace("--", "-")
            synced_slugs.add(slug)

            sensor_path = os.path.join(LOCAL_CODEC_PATH, parent_folder, subfolder, DEFAULT_VERSION)
            if not os.path.isdir(sensor_path):
                continue

            entry = {
                "name": f"{parent_folder.upper()} - {subfolder.replace('-', ' ').title()}",
                "slug": slug,
                "type": "Sensor",
                "description": f"Codec for {parent_folder.upper()} - {subfolder.title()} ({DEFAULT_VERSION}).",
                "download": f"https://raw.githubusercontent.com/iotcommunity-space/codec/refs/heads/main/assets/codecs/{parent_folder}/{subfolder}/{DEFAULT_VERSION}/payload.js",
                "source": CODEC_REPO_URL,
                "sourceName": "TagoIO Github",
                "image": f"https://raw.githubusercontent.com/iotcommunity-space/codec/refs/heads/main/assets/codecs/{parent_folder}/{subfolder}/{DEFAULT_VERSION}/assets/logo.png",
                "sourceRepo": f"https://github.com/tago-io/decoders/tree/main/decoders/connector/{parent_folder}/{subfolder}"
            }

            new_entries.append(entry)

    # Load existing entries (e.g., manually added codecs like RA02G)
    if os.path.exists(CODECS_JSON_PATH):
        with open(CODECS_JSON_PATH, "r") as f:
            try:
                existing_entries = json.load(f)
            except json.JSONDecodeError:
                print("⚠️ Warning: Existing codecs.json is not valid JSON. Skipping merge.")
                existing_entries = []
    else:
        existing_entries = []

    # Preserve entries not overwritten by the sync
    for entry in existing_entries:
        slug = entry.get("slug")
        if slug and slug not in synced_slugs:
            new_entries.append(entry)

    # Write merged result to codecs.json
    with open(CODECS_JSON_PATH, "w") as f:
        json.dump(new_entries, f, indent=2)
    print("✅ Merged and updated codecs.json successfully.")


def sync_codecs():
    """Main entrypoint."""
    all_sensor_folders = fetch_all_sensors()
    rewrite_codecs_json(all_sensor_folders)


if __name__ == "__main__":
    sync_codecs()
