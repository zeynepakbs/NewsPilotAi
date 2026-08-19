from supabase import create_client
from .config import SUPABASE_URL, SUPABASE_ANON_KEY
from .device import get_device_id

def check_license(license_key: str) -> tuple[bool, str]:
    """
    Lisansı Supabase'e karşı doğrular (RPC üzerinden, RLS-safe).
    Dönüş: (basarili_mi, mesaj)
    """
    try:
        sb = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        device_id = get_device_id()

        res = sb.rpc(
            "validate_and_activate_license",
            {"p_license_key": license_key, "p_device_id": device_id}
        ).execute()

        data = res.data or {}
        return bool(data.get("ok")), data.get("message", "Bilinmeyen hata.")

    except Exception as e:
        return False, f"Sunucuya bağlanılamadı: {e}"