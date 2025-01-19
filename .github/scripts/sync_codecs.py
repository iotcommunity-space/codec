import requests
import os
import json

# Constants
TAGOIO_BASE_URL = "https://api.github.com/repos/tago-io/decoders/contents/decoders/connector"
LOCAL_CODEC_PATH = "assets/codecs"
CODECS_JSON_PATH = "assets/codecs.json"
CODEC_REPO_URL = "https://github.com/iotcommunity-space/codec"

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

def sync_sensor_files(sensor_name, folder_content, local_sensor_path):
    """Download all files and subfolders for a specific sensor."""
    for item in folder_content:
        if item['type'] == 'file':
            file_path = os.path.join(local_sensor_path, item['name'])
            download_file(item['download_url'], file_path)
        elif item['type'] == 'dir':
            subfolder_content = fetch_github_content(item['url'])
            subfolder_path = os.path.join(local_sensor_path, item['name'])
            sync_sensor_files(sensor_name, subfolder_content, subfolder_path)

def rewrite_codecs_json(local_sensor_folders):
    """Rewrite the codecs.json file with the updated sensor information."""
    sensor_entries = []

    for sensor_name in local_sensor_folders:
        sensor_path = os.path.join(LOCAL_CODEC_PATH, sensor_name)
        if not os.path.isdir(sensor_path):
            continue

        # Check for the presence of subfolders and files
        versions = [v for v in os.listdir(sensor_path) if os.path.isdir(os.path.join(sensor_path, v))]
        if versions:
            latest_version = sorted(versions)[-1]  # Take the latest version
            entry = {
                "name": sensor_name.upper(),
                "slug": sensor_name.lower(),
                "type": "Sensor",
                "description": f"Codec for {sensor_name.upper()} (v{latest_version}).",
                "download": f"https://raw.githubusercontent.com/iotcommunity-space/codec/refs/heads/main/assets/codecs/{local_sensor_folders}/{sensor_name}/{latest_version}/payload.js",
                "source": CODEC_REPO_URL,
                "sourceName": "TagoIO Github",
                "image": f"https://raw.githubusercontent.com/iotcommunity-space/codec/refs/heads/main/assets/codecs/{local_sensor_folders}/{sensor_name}/{latest_version}/assets/logo.png",
                "sourceRepo": f"{CODEC_REPO_URL}/tree/main/assets/codecs/{sensor_name}"
            }
            sensor_entries.append(entry)

    # Write to codecs.json
    with open(CODECS_JSON_PATH, "w") as f:
        json.dump(sensor_entries, f, indent=2)
    print("Rewritten codecs.json successfully.")

def sync_codecs():
    """Sync all sensor codecs from the remote repository to the local repository."""
    sensors = fetch_github_content(TAGOIO_BASE_URL)
    local_sensor_folders = []

    for sensor in sensors:
        if sensor['type'] == 'dir':
            sensor_name = sensor['name']
            print(f"Processing sensor: {sensor_name}")
            sensor_content = fetch_github_content(sensor['url'])
            local_sensor_path = os.path.join(LOCAL_CODEC_PATH, sensor_name)

            # Sync all files and folders for the sensor
            sync_sensor_files(sensor_name, sensor_content, local_sensor_path)
            local_sensor_folders.append(sensor_name)

    # Rewrite the codecs.json file
    rewrite_codecs_json(local_sensor_folders)

if __name__ == "__main__":
    sync_codecs()
