#!/bin/bash

METADATA_REPO_URL="https://github.com/osholt/kicad-plugin-repo-metadata.git"

mkdir -p artifacts

echo "Cloning metadata repo $METADATA_REPO_URL"
git clone --depth 1 "$METADATA_REPO_URL" metadata
cd metadata
git rev-parse --short HEAD > ../artifacts/metadata_commit.txt
cd ..

# create resources.zip
cd metadata/packages

ICON_FILES=$(find . -mindepth 2 -maxdepth 2 -type f -name icon.png | sort)

if [ ! -z "$ICON_FILES" ]; then
    # set icon file timestamps to their commit timestamps to make
    # zip output deterministic and avoid unnecessary updates to repo
    for ICON in $ICON_FILES; do
        TIME=$(git log --pretty=format:%cd -n 1 --date=iso -- "$ICON")
        TIME=$(gdate --date="$TIME" +%Y%m%d%H%M.%S)
        touch -t "$TIME" "$ICON"
    done
    echo "$ICON_FILES" | zip -9 "../../artifacts/resources.zip" -@
else
    touch empty
    zip -9 "../../artifacts/resources.zip" empty
    rm empty
fi

cd ../..

# create packages.json
python3 ci/build-packages.py ./metadata/

cp artifacts/packages.json .
cp artifacts/resources.zip .

rm -rvf artifacts > /dev/null
rm -rvf metadata > /dev/null

