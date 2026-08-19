import os
import shutil
import sys
from pathlib import Path

# ==============================================================================
# BASE DIRECTORIES (DEV vs PYINSTALLER FROZEN)
# ==============================================================================

# PyInstaller ile paketlendiğinde True olur
IS_FROZEN = getattr(sys, "frozen", False)

if IS_FROZEN:
    # Paketlenmiş ortamda (.exe çalışırken):
    # APP_DIR: .exe dosyasının fiziksel olarak bulunduğu klasör (yazılabilir veriler, .env, cache, outputs)
    APP_DIR = Path(sys.executable).resolve().parent
    # BUNDLE_DIR: PyInstaller geçici/iç paket dizini (sys._MEIPASS) veya .exe klasörü
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR)).resolve()
else:
    # Geliştirme ortamında (python app.py çalışırken):
    APP_DIR = Path(__file__).resolve().parent
    BUNDLE_DIR = APP_DIR

# Geriye dönük uyumluluk için BASE_DIR (APP_DIR ile aynıdır)
BASE_DIR = APP_DIR

# ==============================================================================
# ENVIRONMENT & CONFIGURATION
# ==============================================================================
ENV_FILE = APP_DIR / ".env"

# ==============================================================================
# ASSETS & STYLES (STATİK KAYNAKLAR)
# ==============================================================================
# Önce bundle (sys._MEIPASS) içindeki assets aranır, yoksa APP_DIR/assets
if (BUNDLE_DIR / "assets").exists():
    ASSETS_DIR = BUNDLE_DIR / "assets"
else:
    ASSETS_DIR = APP_DIR / "assets"

STYLES_DIR = ASSETS_DIR / "styles"
STYLE_QSS = STYLES_DIR / "style.qss"

# Statik Şablon Görselleri
PRESENTER_SCENE_PNG = ASSETS_DIR / "presenter_scene.png"

# ==============================================================================
# RUNTIME WRITABLE DIRECTORIES (DİNAMİK VERİLER & ÇIKTILAR)
# ==============================================================================
# Cache dizini ve dosyası (.exe yanında konumlanır)
CACHE_DIR = APP_DIR / "cache"
DAILY_NEWS_CACHE = CACHE_DIR / "daily_news.json"

# Ses, altyazı ve genel çıktılar
OUTPUTS_DIR = APP_DIR / "outputs"
DAILY_NEWS_AUDIO = OUTPUTS_DIR / "daily_news.mp3"
DAILY_NEWS_SUBTITLE = OUTPUTS_DIR / "daily_news.vtt"

# Video çıktı ve geçici şablon dizinleri
VIDEOS_DIR = APP_DIR / "assets" / "videos"
OUTPUT_VIDEOS_DIR = VIDEOS_DIR / "output"
TEMPLATE_VIDEOS_DIR = VIDEOS_DIR / "template"

LATEST_NEWS_VIDEO = OUTPUT_VIDEOS_DIR / "latest_news.mp4"
SCROLLING_TEXT_STRIP_PNG = TEMPLATE_VIDEOS_DIR / "scrolling_text_strip.png"
SCROLLING_TEXT_VIDEO_MP4 = TEMPLATE_VIDEOS_DIR / "scrolling_text_video.mp4"
PRESENTER_TEMPLATE_MP4 = TEMPLATE_VIDEOS_DIR / "presenter_template.mp4"

# ==============================================================================
# SYSTEM FONTS
# ==============================================================================
WIN_FONTS_DIR = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"

# ==============================================================================
# TOOLS & EXTERNAL BINARIES (FFMPEG / FFPROBE)
# ==============================================================================
TOOLS_DIR = APP_DIR / "tools"


def get_ffmpeg_path() -> Path:
    """
    FFmpeg çalıştırılabilir dosyasının konumunu sırasıyla:
    1. APP_DIR / tools / ffmpeg / ffmpeg.exe (.exe yanındaki tools)
    2. BUNDLE_DIR / tools / ffmpeg / ffmpeg.exe (_MEIPASS içi)
    3. Sistem PATH ortamı (shutil.which)
    4. Varsayılan APP_DIR konumu
    üzerinden dinamik ve güvenli bir şekilde çözer.
    """
    candidates = [
        APP_DIR / "tools" / "ffmpeg" / "ffmpeg.exe",
        BUNDLE_DIR / "tools" / "ffmpeg" / "ffmpeg.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    found_in_path = shutil.which("ffmpeg")
    if found_in_path:
        return Path(found_in_path)

    return candidates[0]


def get_ffprobe_path() -> Path:
    """
    FFprobe çalıştırılabilir dosyasının konumunu sırasıyla:
    1. APP_DIR / tools / ffmpeg / ffprobe.exe
    2. BUNDLE_DIR / tools / ffmpeg / ffprobe.exe
    3. Sistem PATH ortamı (shutil.which)
    4. Varsayılan APP_DIR konumu
    üzerinden dinamik ve güvenli bir şekilde çözer.
    """
    candidates = [
        APP_DIR / "tools" / "ffmpeg" / "ffprobe.exe",
        BUNDLE_DIR / "tools" / "ffmpeg" / "ffprobe.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    found_in_path = shutil.which("ffprobe")
    if found_in_path:
        return Path(found_in_path)

    return candidates[0]


# ==============================================================================
# DIRECTORY ENSURE HELPER
# ==============================================================================
def ensure_runtime_dirs() -> None:
    """Uygulamanın çalışması için gerekli dinamik klasörlerin varlığını garanti eder."""
    for directory in [
        CACHE_DIR,
        OUTPUTS_DIR,
        OUTPUT_VIDEOS_DIR,
        TEMPLATE_VIDEOS_DIR,
    ]:
        directory.mkdir(parents=True, exist_ok=True)
