import base64
import hashlib
import io
import json
import os
import requests
import logging
from datetime import datetime
from requests.exceptions import HTTPError


READ_SIZE = 65536


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

def write_json_file(jd: dict, file_name: str) -> bool:
    with open(file_name, 'w') as fp:
        json.dump(jd, fp)

def get_file_base64(file_name: str) -> str:
    with io.open(file_name, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def update(jd: dict, file: str) -> bool:
    mtime = os.path.getmtime(file)
    dt = datetime.fromtimestamp(mtime)
    sha = getsha256(file)
    if sha == jd["sha256"]:
        return False
    jd["sha256"] = sha
    jd["update_timestamp"] = int(mtime)
    jd["update_time_utc"] = dt.strftime("%Y-%m-%d %H:%M:%S")
    return True


repository = load_json_file("repository.json")

if not os.path.exists("packages.json"):
    print("Could not find packages.json in current directory")
    exit(1)

update_packages = update(repository["packages"], "packages.json")
update_resources = update(repository["resources"], "resources.zip")

if update_packages or update_resources:
    write_json_file(repository, "repository.json")
else:
    print("No change detected")
