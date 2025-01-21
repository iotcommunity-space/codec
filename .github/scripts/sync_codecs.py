import requests
import os
import json

# Constants
TAGOIO_BASE_URL = "https://api.github.com/repos/tago-io/decoders/contents/decoders/connector"
LOCAL_CODEC_PATH = "assets/codecs"
CODECS_JSON_PATH = "assets/codecs.json"
CODEC_REPO_URL = "https://github.com/tago-io/decoders/tree/main/decoders/connector"

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
    """Download the file from the provided URL to the specified path with authentication."""
    response = requests.get(file_url, headers=HEADERS)
    if response.status_code == 200:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as file:
            file.write(response.content)
        print(f"Downloaded: {save_path}")
    else:
        print(f"Failed to download {file_url}. Status code: {response.status_code}")


def sync_sensor_files(folder_content, local_sensor_path):
    """Download all files and subfolders for a specific sensor."""
    for item in folder_content:
        if item['type'] == 'file':
            file_path = os.path.join(local_sensor_path, item['name'])
            download_file(item['download_url'], file_path)
        elif item['type'] == 'dir':
            subfolder_content = fetch_github_content(item['url'])
            subfolder_path = os.path.join(local_sensor_path, item['name'])
            sync_sensor_files(subfolder_content, subfolder_path)


def process_folder(folder, parent_path):
    """Process a folder, fetch its content, and sync all files and subfolders."""
    local_sensor_path = os.path.join(LOCAL_CODEC_PATH, parent_path, folder['name'])
    folder_content = fetch_github_content(folder['url'])
    sync_sensor_files(folder_content, local_sensor_path)
    return folder['name']


def fetch_all_sensors():
    """Fetch all sensors and their subfolders."""
    sensors = fetch_github_content(TAGOIO_BASE_URL)
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


def rewrite_codecs_json(all_sensor_folders):
    """Rewrite the codecs.json file with the updated sensor information."""
    sensor_entries = []

    for parent_folder, subfolders in all_sensor_folders.items():
        for subfolder in subfolders:
            sensor_path = os.path.join(LOCAL_CODEC_PATH, parent_folder, subfolder)
            if not os.path.isdir(sensor_path):
                continue

            # Check for the presence of files
            files = [f for f in os.listdir(sensor_path) if os.path.isfile(os.path.join(sensor_path, f))]
            if files:
                entry = {
                    "name": f"{parent_folder.upper()} - {subfolder}",
                    "slug": f"{parent_folder.lower()}-{subfolder.lower()}",
                    "type": "Sensor",
                    "description": f"Codec for {parent_folder.upper()} - {subfolder}.",
                    "download": f"https://raw.githubusercontent.com/iotcommunity-space/codec/refs/heads/main/assets/codecs/{parent_folder}/{subfolder}/payload.js",
                    "source": CODEC_REPO_URL,
                    "sourceName": "TagoIO Github",
                    "image": f"https://raw.githubusercontent.com/iotcommunity-space/codec/refs/heads/main/assets/codecs/{parent_folder}/{subfolder}/assets/logo.png",
                    "sourceRepo": f"{CODEC_REPO_URL}/tree/main/assets/codecs/{parent_folder}/{subfolder}"
                }
                sensor_entries.append(entry)

    # Write to codecs.json
    with open(CODECS_JSON_PATH, "w") as f:
        json.dump(sensor_entries, f, indent=2)
    print("Rewritten codecs.json successfully.")


def sync_codecs():
    """Sync all sensor codecs from the remote repository to the local repository."""
    all_sensor_folders = fetch_all_sensors()
    rewrite_codecs_json(all_sensor_folders)


if __name__ == "__main__":
    sync_codecs()
