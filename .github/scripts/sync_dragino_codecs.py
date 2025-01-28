import requests
import os
import json

# Constants
DRAGINO_BASE_URL = "https://api.github.com/repos/dragino/dragino-end-node-decoder/contents"
LOCAL_CODEC_PATH = "assets/codecs"
CODECS_JSON_PATH = "assets/codecs.json"
CODEC_REPO_URL = "https://github.com/dragino/dragino-end-node-decoder"
DEFAULT_VERSION = "v1.0.0"

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


def download_file(file_url, save_path):
    """Download the file from the provided URL to the specified path."""
    response = requests.get(file_url, headers=HEADERS)
    if response.status_code == 200:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as file:
            file.write(response.content)
        print(f"Downloaded: {save_path}")
    else:
        print(f"Failed to download {file_url}. Status code: {response.status_code}")


def sync_sensor_files(sensor_path, folder_content):
    """Download all files for a specific sensor."""
    for item in folder_content:
        if item['type'] == 'file':
            # Save only .txt files for decoders
            if item['name'].endswith('.txt'):
                file_path = os.path.join(sensor_path, item['name'])
                download_file(item['download_url'], file_path)


def process_folder(folder, parent_path):
    """Process a folder, fetch its content, and sync all files."""
    sensor_path = os.path.join(LOCAL_CODEC_PATH, parent_path, folder['name'], DEFAULT_VERSION)
    folder_content = fetch_github_content(folder['url'])
    sync_sensor_files(sensor_path, folder_content)
    return folder['name']


def fetch_all_sensors():
    """Fetch all sensors and their subfolders."""
    sensors = fetch_github_content(DRAGINO_BASE_URL)
    all_sensor_folders = {}

    for sensor in sensors:
        if sensor['type'] == 'dir':
            parent_folder_name = sensor['name']
            parent_folder_content = fetch_github_content(sensor['url'])
            sub_sensors = []

            for subfolder in parent_folder_content:
                if subfolder['type'] == 'dir':
                    sub_sensors.append(process_folder(subfolder, parent_folder_name))

            all_sensor_folders[parent_folder_name] = sub_sensors

    return all_sensor_folders


def generate_unique_slug(slug, existing_slugs):
    """Generate a unique slug by appending a version suffix if needed."""
    if slug not in existing_slugs:
        return slug

    counter = 1
    new_slug = f"{slug}-v{counter}"
    while new_slug in existing_slugs:
        counter += 1
        new_slug = f"{slug}-v{counter}"
    return new_slug


def rewrite_codecs_json(all_sensor_folders):
    """Rewrite the codecs.json file with the updated sensor information."""
    sensor_entries = []

    for parent_folder, subfolders in all_sensor_folders.items():
        for subfolder in subfolders:
            sensor_path = os.path.join(LOCAL_CODEC_PATH, parent_folder, subfolder, DEFAULT_VERSION)
            if not os.path.isdir(sensor_path):
                continue

            slug = f"{parent_folder.lower()}-{subfolder.lower()}".replace(" ", "-").replace("--", "-")
            existing_slugs = {entry["slug"] for entry in sensor_entries}

            unique_slug = generate_unique_slug(slug, existing_slugs)

            entry = {
                "name": f"DRAGINO - {subfolder.replace('-', ' ').title()}",
                "slug": unique_slug,
                "type": "Sensor",
                "description": f"Codec for DRAGINO - {subfolder.title()} ({DEFAULT_VERSION}).",
                "download": f"https://raw.githubusercontent.com/iotcommunity-space/codec/refs/heads/main/assets/codecs/{parent_folder}/{subfolder}/{DEFAULT_VERSION}/decoder.txt",
                "source": CODEC_REPO_URL,
                "sourceName": "Dragino",
                "image": "https://raw.githubusercontent.com/iotcommunity-space/codec/refs/heads/main/assets/images/default_logo.png",
                "sourceRepo": f"{CODEC_REPO_URL}/tree/main/{parent_folder}/{subfolder}"
            }
            sensor_entries.append(entry)

    # Merge with existing codecs.json and handle duplicates
    if os.path.exists(CODECS_JSON_PATH):
        with open(CODECS_JSON_PATH, "r") as f:
            existing_entries = json.load(f)

        # Deduplicate based on slug
        existing_slugs = {entry["slug"]: entry for entry in existing_entries}
        for entry in sensor_entries:
            existing_slugs[entry["slug"]] = entry

        sensor_entries = list(existing_slugs.values())

    # Write to codecs.json
    with open(CODECS_JSON_PATH, "w") as f:
        json.dump(sensor_entries, f, indent=2)
    print("Rewritten codecs.json successfully.")


def sync_codecs():
    """Sync all Dragino sensor codecs from the remote repository to the local repository."""
    all_sensor_folders = fetch_all_sensors()
    rewrite_codecs_json(all_sensor_folders)


if __name__ == "__main__":
    sync_codecs()
