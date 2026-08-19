# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

block_cipher = None

project_root = Path('.').resolve()

datas = [
    ('assets/styles/style.qss', 'assets/styles'),
]

binaries = [
    ('tools/ffmpeg/ffmpeg.exe', 'tools/ffmpeg'),
]

hidden_imports = [
    # PySide6 Modülleri
    'PySide6',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtMultimedia',
    'PySide6.QtMultimediaWidgets',
    'PySide6.QtNetwork',

    # Supabase & Veritabanı
    'supabase',
    'postgrest',
    'gotrue',
    'realtime',
    'storage3',
    'functions_framework',
    'httpx',
    'httpcore',
    'h11',
    'anyio',
    'sniffio',

    # AI & API
    'google.genai',
    'google.generativeai',
    'dotenv',
    'feedparser',
    'edge_tts',
    'dateutil',
    'dateutil.parser',
    'dateutil.tz',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'sentence_transformers',
    'torch',

    # Proje İçi Modüller
    'paths',
    'config',
    'license',
    'license.config',
    'license.device',
    'license.license_check',
    'license.license_dialog',
    'license.license_store',
    'cache.agenda_cache',
    'services.news.news_service',
    'services.news.region_detector',
    'services.news.agenda.agenda_selector',
    'services.news.ai.gemini_service',
    'services.news.ai.gemini_client',
    'services.news.ai.news_analyzer',
    'services.news.ai.news_ranker',
    'services.news.ai.prompt_builder',
    'services.news.ai.translator',
    'services.news.ai.models',
    'services.news.collectors.turkey_collector',
    'services.news.collectors.us_collector',
    'services.news.collectors.europe_collector',
    'services.news.collectors.asia_collector',
    'services.news.filter.noise_filter',
    'services.news.ingestion.content_filter',
    'services.news.ingestion.normalizer',
    'services.news.ingestion.rss_parser',
    'services.news.ingestion.rss_provider',
    'services.news.ingestion.sources',
    'services.news.models.article',
    'services.news.pipeline.news_pipeline',
    'services.news.ranking.category_classifier',
    'services.news.ranking.duplicate_detector',
    'services.news.ranking.entity_detector',
    'services.news.ranking.headline_cluster',
    'services.news.ranking.headline_ranker',
    'services.news.ranking.importance_calculator',
    'services.news.script.presenter_persona',
    'services.news.script.script_builder',
    'services.news.script.script_service',
    'services.news.sumarizer.plain_summary',
    'services.news.voice.tts_service',
    'services.video.audio_mixer',
    'services.video.scrolling_text_generator',
    'services.video.template_generator',
    'workers.news_worker',
    'ui.main_window',
    'ui.welcome_page',
    'ui.video_news_page',
    'ui.home_page',
    'ui.news_page',
    'ui.critical_page',
    'ui.widgets.news_card',
    'ui.widgets.chat_input',
    'ui.widgets.flow_layout',
    'widgets.VideoNewsPlayer',
    'widgets.PlayerControls',
    'widgets.AvatarWidget',
]

a = Analysis(
    ['app.py'],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NewsPilot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='NewsPilot',
)
