import argparse
import io
import json
import os


def load_json_file(file_name: str) -> dict:
    with io.open(file_name, encoding="utf-8") as f:
        return json.load(f)


def extract_version(version: dict) -> tuple:
    epoch = version.get("version_epoch", 0)
    version_parts = version["version"].split(".")
    major = version_parts[0]
    minor = version_parts[1] if len(version_parts) > 1 else 0
    patch = version_parts[2] if len(version_parts) > 2 else 0
    return (epoch, int(major), int(minor), int(patch))


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="KiCad repository packages.json builder")

    parser.add_argument("metadata", help="Metadata repo location")

    args = parser.parse_args()

    _, package_dirs, _ = next(os.walk(os.path.join(args.metadata, "packages")))

    packages: list = load_json_file("packages.json")["packages"]
    new_packages = {}

    for package in package_dirs:
        pkg_metadata = load_json_file(
            os.path.join(args.metadata, "packages", package, "metadata.json"))
        new_packages[pkg_metadata["identifier"]] = pkg_metadata

    # remove packages no longer in metadata repo
    packages = [p for p in packages if p["identifier"] in new_packages]

    # pull in updates
    for idx, pkg in enumerate(packages):
        id = pkg["identifier"]
        packages[idx] = new_packages[id]
        del new_packages[id]

    # append new packages to the end
    for pkg in new_packages.values():
        packages.append(pkg)

    for pkg in packages:
        pkg["versions"] = sorted(pkg["versions"], key=extract_version, reverse=True)

    with io.open("artifacts/packages.json", "w", encoding="utf-8") as f:
        json.dump({"packages": packages}, f, indent=4, sort_keys=True)
        print(file=f)  # add a newline at the end of file
