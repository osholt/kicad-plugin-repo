import base64
import hashlib
import io
import json
import os
import requests
import logging
from datetime import datetime
from requests.exceptions import HTTPError


# uncomment for http logging
# import http.client as http_client
# http_client.HTTPConnection.debuglevel = 1
# logging.basicConfig()
# logging.getLogger().setLevel(logging.DEBUG)
# requests_log = logging.getLogger("requests.packages.urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True


READ_SIZE = 65536
PUSH_BRANCH="main"
CI_PROJECT_ID = os.environ["CI_PROJECT_ID"]
CI_PROJECT_URL = os.environ["CI_PROJECT_URL"]
RESOURCES_URL = f"{CI_PROJECT_URL}/-/jobs/artifacts/{PUSH_BRANCH}/raw/artifacts/resources.zip?job=update"
PACKAGES_URL=f"{CI_PROJECT_URL}/-/raw/{PUSH_BRANCH}/packages.json"
GITLAB_API_URL = os.environ["CI_API_V4_URL"]
COMMITS_API_URL = f"{GITLAB_API_URL}/projects/{CI_PROJECT_ID}/repository/commits"
PRIVATE_API_TOKEN = os.environ["PRIVATE_API_TOKEN"]


def getsha256(filename: str) -> str:
    hash = hashlib.sha256()
    with io.open(filename, "rb") as f:
        data = f.read(READ_SIZE)
        while data:
            hash.update(data)
            data = f.read(READ_SIZE)
    return hash.hexdigest()


def load_json_file(file_name: str) -> dict:
    with io.open(file_name, encoding="utf-8") as f:
        return json.load(f)


def get_file_base64(file_name: str) -> str:
    with io.open(file_name, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def update(json: dict, file: str) -> bool:
    mtime = os.path.getmtime(file)
    dt = datetime.fromtimestamp(mtime)
    sha = getsha256(file)
    if sha == json["sha256"]:
        return False
    json["sha256"] = sha
    json["update_timestamp"] = int(mtime)
    json["update_time_utc"] = dt.strftime("%Y-%m-%d %H:%M:%S")
    return True


repository = load_json_file("repository.json")

if not os.path.exists("artifacts/packages.json"):
    print("Could not find packages.json in artifacts directory")
    exit(1)

update_packages = update(repository["packages"], "artifacts/packages.json")
update_resources = update(repository["resources"], "artifacts/resources.zip")

if update_packages or update_resources:
    print("Committing changes to repository")

    with io.open("artifacts/metadata_commit.txt", "r") as f:
        metadata_commit = f.readline()

    repository["packages"]["url"] = PACKAGES_URL
    if update_resources:
        repository["resources"]["url"] = RESOURCES_URL

    request_data = {
        "branch": PUSH_BRANCH,
        "author_email": "gitlab-ci-bot@kicad.org",
        "author_name": "KiCad gitlab CI bot",
        "commit_message": f"CI update from metadata repository\n\nMetadata repo commit {metadata_commit}",
        "actions": [
            {
                "action": "update",
                "file_path": "repository.json",
                "content": json.dumps(repository, indent=4, sort_keys=True) + "\n",
            }
        ]
    }

    if update_packages:
        request_data["actions"].append({
            "action": "update",
            "file_path": "packages.json",
            "content": get_file_base64("artifacts/packages.json"),
            "encoding": "base64",
        })

    request_headers = {
        "Content-Type": "application/json",
        "PRIVATE-TOKEN": PRIVATE_API_TOKEN,
    }

    try:
        response = requests.post(
            COMMITS_API_URL, json=request_data, headers=request_headers)

        response_json = response.json()
        print("Response:")
        print(json.dumps(response_json, indent=4))

        response.raise_for_status()

        print("Change committed successfully:", response_json["web_url"])
    except HTTPError as e:
        print("Exception calling gitlab commits api", e)
        exit(1)
    except json.JSONDecodeError as e:
        print("Invalid response", e)
        exit(1)
else:
    print("No change detected")
