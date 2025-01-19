import requests
import os
import json

# Constants
GITHUB_BASE_URL = "https://api.github.com/repos/iotcommunity-space/codec/contents/assets/codecs"
LOCAL_CODEC_PATH = "assets/codecs"
CODECS_JSON_PATH = "assets/codecs.json"

# Fetch the GitHub token from environment variables
GITHUB_TOKEN = os.getenv("CODEC_TOKEN")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def fetch_github_content(url):
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch content from {url}. Status code: {response.status_code}")
    return []

def download_file(file_url, save_path):
    response = requests.get(file_url, headers=HEADERS)
    if response.status_code == 200:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as file:
            file.write(response.content)
        print(f"Downloaded: {save_path}")
    else:
        print(f"Failed to download {file_url}. Status code: {response.status_code}")

def update_codecs_json():
    if not os.path.exists(CODECS_JSON_PATH):
        with open(CODECS_JSON_PATH, "w") as f:
            json.dump([], f)

    with open(CODECS_JSON_PATH, "r") as f:
        existing_codecs = json.load(f)

    codecs = []
    sensors = fetch_github_content(GITHUB_BASE_URL)
    for sensor in sensors:
        if sensor['type'] == 'dir':
            sensor_name = sensor['name']
            sensor_url = sensor['url']
            sensor_versions = fetch_github_content(sensor_url)

            for version in sensor_versions:
                if version['type'] == 'dir':
                    version_name = version['name']
                    version_url = version['url']
                    files = fetch_github_content(version_url)

                    payload_url = None
                    for file in files:
                        if file['name'] == 'payload.js':
                            payload_url = file['download_url']
                            break

                    entry = {
                        "name": sensor_name.upper(),
                        "slug": sensor_name.lower(),
                        "type": "Sensor",
                        "description": f"Codec for {sensor_name.upper()} (v{version_name}).",
                        "download": payload_url,
                        "source": f"https://github.com/iotcommunity-space/codec",
                        "sourceName": "IoTCommunity GitHub",
                        "image": f"https://raw.githubusercontent.com/iotcommunity-space/codec/main/assets/codecs/{sensor_name}/assets/logo.png",
                        "sourceRepo": f"https://github.com/iotcommunity-space/codec/tree/main/assets/codecs/{sensor_name}"
                    }

                    if entry not in existing_codecs and entry not in codecs:
                        codecs.append(entry)

    with open(CODECS_JSON_PATH, "w") as f:
        json.dump(codecs, f, indent=2)
    print(f"Updated {CODECS_JSON_PATH} with {len(codecs)} entries.")

if __name__ == "__main__":
    update_codecs_json()
