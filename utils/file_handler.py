import os
from pathlib import Path

UPLOAD_DIR = Path("data")
UPLOAD_DIR.mkdir(exist_ok=True)

def save_uploaded_files(files_dict):
    saved_paths = {}
    for key, uploaded_file in files_dict.items():
        file_path = UPLOAD_DIR / uploaded_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.read())
        saved_paths[key] = str(file_path)
    return saved_paths
