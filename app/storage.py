from pathlib import Path

STORAGE_DIR = Path("data_store")
STORAGE_DIR.mkdir(exist_ok=True)

def save_blob(patient_id, data: bytes, suffix="pb"):
    path = STORAGE_DIR / f"{patient_id}.{suffix}"
    with open(path, "wb") as f:
        f.write(data)
    return path

def load_blob(path):
    with open(path, "rb") as f:
        return f.read()
