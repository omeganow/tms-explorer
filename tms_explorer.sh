#!/bin/bash

if [ -d "./.env" ]; then
    echo "Running from virtualenv -> if you encounter problems delete .env-Folder and retry"
    source ./.env/bin/activate
    which python
    python3 -u src/tms_app.py
else
    echo "Initializing! Setting up python virtual env for tmsExplorer!"
    python3 -m venv .env
    source ./.env/bin/activate
    python3 -m pip install -r requirements.txt
    python3 -u src/tms_app.py
fi
deactivate

