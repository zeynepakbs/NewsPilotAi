from datetime import datetime, timezone, timedelta
from supabase import create_client
from .config import SUPABASE_URL, SUPABASE_ANON_KEY
from .device import get_device_id

def check_license(license_key: str) -> tuple[bool, str]:
    """
    Lisansı Supabase'e karşı doğrular.
    Dönüş: (basarili_mi, mesaj)
    """
    try:
        sb = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        device_id = get_device_id()
        now = datetime.now(timezone.utc)

        res = sb.table("licenses").select("*").eq("license_key", license_key).execute()
        if not res.data:
            return False, "Geçersiz lisans anahtarı."

        row = res.data[0]

        if not row.get("is_active", True):
            return False, "Bu lisans devre dışı bırakılmış."

        # İlk aktivasyon: cihazı kaydet ve süreyi başlat
        if row.get("device_id") is None:
            duration = row.get("duration_days", 60)
            expires = now + timedelta(days=duration)
            sb.table("licenses").update({
                "device_id": device_id,
                "expires_at": expires.isoformat(),
                "last_seen_at": now.isoformat()
            }).eq("license_key", license_key).execute()
            return True, "Lisans aktive edildi."

        # Başka cihaz kontrolü
        if row["device_id"] != device_id:
            return False, "Bu lisans başka bir cihaza kayıtlı."

        # Süre kontrolü
        if row.get("expires_at"):
            expires_at = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))
            if expires_at < now:
                return False, "Lisans süresi dolmuş."

        sb.table("licenses").update({
            "last_seen_at": now.isoformat()
        }).eq("license_key", license_key).execute()

        return True, "OK"

    except Exception as e:
        return False, f"Sunucuya bağlanılamadı: {e}"