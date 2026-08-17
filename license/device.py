import hashlib
import uuid

def get_device_id() -> str:
    """Basit cihaz parmak izi (MAC tabanlı)."""
    raw = str(uuid.getnode())
    return hashlib.sha256(raw.encode()).hexdigest()