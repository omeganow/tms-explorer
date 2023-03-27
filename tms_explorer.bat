if exist .env/ (
    echo "Running from virtualenv -> if you encounter problems delete .env-Folder and retry"
    call ".\.env\Scripts\activate.bat"
    python -u src/tms_app.py
) else (
    echo "Initializing! Setting up python virtual env for tmsExplorer!"
    python -m venv .env
    call ".\.env\Scripts\activate.bat"
    python -m pip install -r requirements.txt
    python -u src/tms_app.py
)
deactivate