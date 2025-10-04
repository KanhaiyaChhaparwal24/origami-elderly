from pathlib import Path
from typing import Union, Optional
import generated.origami.core_pb2 as core_pb
from app.serializer import serialize_data_packet, deserialize_data_packet, serialize_alert, deserialize_alert, serialize_application_summary, deserialize_application_summary

STORAGE_DIR = Path("data_store")
STORAGE_DIR.mkdir(exist_ok=True)

def save_data_packet(packet: core_pb.DataPacket, custom_name: str = None) -> Path:
    """Save a DataPacket to storage"""
    if custom_name:
        filename = f"{custom_name}.packet"
    else:
        filename = f"{packet.app_id}_{packet.source_id}_{packet.data_type}.packet"
    
    path = STORAGE_DIR / filename
    data = serialize_data_packet(packet)
    
    with open(path, "wb") as f:
        f.write(data)
    return path

def load_data_packet(path: Union[str, Path]) -> core_pb.DataPacket:
    """Load a DataPacket from storage"""
    with open(path, "rb") as f:
        data = f.read()
    return deserialize_data_packet(data)

def save_alert(alert: core_pb.Alert, custom_name: str = None) -> Path:
    """Save an Alert to storage"""
    if custom_name:
        filename = f"{custom_name}.alert"
    else:
        filename = f"{alert.app_id}_{alert.alert_id}.alert"
    
    path = STORAGE_DIR / filename
    data = serialize_alert(alert)
    
    with open(path, "wb") as f:
        f.write(data)
    return path

def load_alert(path: Union[str, Path]) -> core_pb.Alert:
    """Load an Alert from storage"""
    with open(path, "rb") as f:
        data = f.read()
    return deserialize_alert(data)

def save_application_summary(summary: core_pb.ApplicationSummary, custom_name: str = None) -> Path:
    """Save an ApplicationSummary to storage"""
    if custom_name:
        filename = f"{custom_name}.summary"
    else:
        filename = f"{summary.app_id}_{summary.entity_ids[0] if summary.entity_ids else 'unknown'}_{summary.period}.summary"
    
    path = STORAGE_DIR / filename
    data = serialize_application_summary(summary)
    
    with open(path, "wb") as f:
        f.write(data)
    return path

def load_application_summary(path: Union[str, Path]) -> core_pb.ApplicationSummary:
    """Load an ApplicationSummary from storage"""
    with open(path, "rb") as f:
        data = f.read()
    return deserialize_application_summary(data)

# Legacy support functions
def save_blob(entity_id: str, data: bytes, suffix: str = "pb") -> Path:
    """Save binary data blob (legacy support)"""
    path = STORAGE_DIR / f"{entity_id}.{suffix}"
    with open(path, "wb") as f:
        f.write(data)
    return path

def load_blob(path: Union[str, Path]) -> bytes:
    """Load binary data blob (legacy support)"""
    with open(path, "rb") as f:
        return f.read()

def list_stored_files(app_id: str = None, file_type: str = None) -> list:
    """List stored files, optionally filtered by app_id and file_type"""
    files = []
    
    for file_path in STORAGE_DIR.iterdir():
        if file_path.is_file():
            if app_id and not file_path.name.startswith(app_id):
                continue
            if file_type and not file_path.name.endswith(f".{file_type}"):
                continue
            files.append(file_path)
    
    return files

def get_storage_stats() -> dict:
    """Get storage statistics"""
    stats = {
        "total_files": 0,
        "by_type": {},
        "by_app": {},
        "total_size_bytes": 0
    }
    
    for file_path in STORAGE_DIR.iterdir():
        if file_path.is_file():
            stats["total_files"] += 1
            stats["total_size_bytes"] += file_path.stat().st_size
            
            # Count by file type
            if "." in file_path.name:
                file_type = file_path.name.split(".")[-1]
                stats["by_type"][file_type] = stats["by_type"].get(file_type, 0) + 1
            
            # Count by app (if filename follows convention)
            if "_" in file_path.name:
                app_id = file_path.name.split("_")[0]
                stats["by_app"][app_id] = stats["by_app"].get(app_id, 0) + 1
    
    return stats
