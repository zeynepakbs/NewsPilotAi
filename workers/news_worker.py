from pathlib import Path
from PySide6.QtCore import QObject, Signal, Slot
from dateutil import parser as date_parser
from dateutil.tz import gettz, tzutc

from services.news.ai.gemini_service import GeminiService
from services.news.news_service import NewsService
from services.news.ranking.duplicate_detector import DuplicateDetector
from services.news.ranking.category_classifier import CategoryClassifier
from services.news.ranking.headline_ranker import HeadlineRanker
from services.news.ranking.importance_calculator import ImportanceCalculator
from services.news.agenda.agenda_selector import AgendaSelector
from services.news.sumarizer.plain_summary import build_plain_summary
from services.news.script.script_service import ScriptService
from services.news.voice.tts_service import TTSService
from cache.agenda_cache import AgendaCache
from services.news.filter.noise_filter import NewsNoiseFilter

# Video servisleri eklendi
from services.video.template_generator import TemplateGenerator
from services.video.audio_mixer import AudioMixer


class NewsWorker(QObject):

    finished = Signal(dict)
    error = Signal(str)

    def __init__(self):
        super().__init__()
        self.noise_filter = NewsNoiseFilter()

        self.news_service = NewsService()
        self.gemini_service = GeminiService()
        self.script_service = ScriptService()
        self.tts_service = TTSService()
        self.cache = AgendaCache()
        self.duplicate_detector = DuplicateDetector()
        self.category_classifier = CategoryClassifier()
        self.headline_ranker = HeadlineRanker()
        self.importance_calculator = ImportanceCalculator()
        self.agenda_selector = AgendaSelector(max_per_region=2)

        # Video Sınıfları
        self.template_generator = TemplateGenerator()
        self.audio_mixer = AudioMixer()

    def _build_tier_lists(self, scored_clusters):
        kritik = []

        for cluster in scored_clusters:
            tier = ImportanceCalculator.tier_for(cluster.score)

            if tier != "kritik":
                continue

            item = {
                "category": getattr(cluster, "category", "") or "",
                "region": self._resolve_region(cluster),
                "importance": cluster.score,
                "repeat_count": cluster.repeat_count,
                "sources": cluster.sources,
                "body": build_plain_summary(cluster),
            }

            kritik.append(item)

        return kritik

    def _build_script_news(self, clusters):
        news = []

        for cluster in clusters[:10]:
            news.append(
                {
                    "title": getattr(
                        cluster,
                        "translated_title",
                        getattr(cluster, "title", "")
                    ),
                    "summary": build_plain_summary(cluster),
                    "importance": getattr(cluster, "score", 0)
                }
            )

        return news

    def _resolve_region(self, cluster):
        from collections import Counter

        regions = [
            article.region
            for article in cluster.articles
            if getattr(article, "region", "")
        ]

        if not regions:
            return ""

        return Counter(regions).most_common(1)[0][0]

    def _convert_to_turkey_time(self, published_at):
        try:
            published_date = date_parser.parse(published_at)
        except Exception:
            return None

        if published_date.tzinfo is None:
            published_date = published_date.replace(tzinfo=tzutc())

        istanbul = gettz("Europe/Istanbul")
        return published_date.astimezone(istanbul)

    def _is_within_agenda_window(self, published_at):
        if published_at is None:
            return True

        turkey_time = self._convert_to_turkey_time(published_at)
        if turkey_time is None:
            return False

        hour = turkey_time.hour
        return hour >= 19 or hour < 7

    def _filter_agenda_window(self, articles):
        for article in articles[:5]:
            turkey_time = None
            accepted = False

            if article.published_at is None:
                accepted = True
            else:
                turkey_time = self._convert_to_turkey_time(article.published_at)
                accepted = (
                    turkey_time is not None
                    and (turkey_time.hour >= 19 or turkey_time.hour < 7)
                )

            print(article.published_at)
            print(turkey_time)
            print("accepted" if accepted else "rejected")

        return [
            article
            for article in articles
            if self._is_within_agenda_window(article.published_at)
        ]

    @Slot()
    def run(self):
        try:
            print("[NewsWorker] başladı")

            if self.cache.exists_today():
                print("[NewsWorker] Bugünün gündemi cache'den alınıyor")
                data = self.cache.load()
                audio_path = data.get("audio")
                video_path = data.get("video")

                if (
                    audio_path and Path(audio_path).exists()
                    and video_path and Path(video_path).exists()
                ):
                    self.finished.emit(data)
                    return

                print("[NewsWorker] Cache bulundu ancak dosyalar eksik, yeniden oluşturuluyor")

            # 1 - Haberleri çek
            articles = self.news_service.get_combined_news()
            articles = self.noise_filter.filter(articles)

            # 2 - Gündem aralığına filtrele
            articles = self._filter_agenda_window(articles)
            print(f"[NewsWorker] {len(articles)} haber geldi (19:00-07:00 aralığı filtrelendi)")

            self.duplicate_detector.diagnose_threshold(articles)
            self.duplicate_detector.inspect_clusters(
                articles,
                threshold=0.55,
                min_size=3
            )

            # 3 - Duplicate temizleme
            print("[NewsWorker] duplicate başlıyor")
            clusters = self.duplicate_detector.remove_duplicates(articles)

            print(f"[NewsWorker] {len(clusters)} cluster oluştu")

            # 4 - Başlık tekrar sıralaması
            print("[NewsWorker] headline ranking başlıyor")
            clusters = self.headline_ranker.rank(clusters)
            print("[NewsWorker] headline ranking tamamlandı")

            # 5 - Kategori sınıflandırma
            clusters = self.category_classifier.classify(clusters)
            print("[NewsWorker] kategori tamamlandı")

            # 6 - Algoritmik önem puanı
            scored_clusters = self.importance_calculator.calculate(clusters)
            print("[NewsWorker] önem hesaplandı")

            top_clusters = scored_clusters[:20]
            if not top_clusters:
                print("[NewsWorker] Bugün için yeterli haber bulunamadı")
                self.error.emit("Bugün için yeterli haber bulunamadı")
                return

            top_clusters = self.gemini_service.translate_clusters(top_clusters)
            print("[NewsWorker] Top cluster çevirisi tamamlandı")

            ai_editor = self.gemini_service.edit_news(top_clusters)
            print("[NewsWorker] Gemini edit tamamlandı")

            # 7 - Script oluşturuluyor
            print("[NewsWorker] Script oluşturuluyor")
            script_news = self._build_script_news(top_clusters)
            script = self.script_service.generate(script_news)
            print("[NewsWorker] 8 dakikalık script tamamlandı")
            print("\n========== SCRIPT ==========")
            print(script)
            print("========== END SCRIPT ==========")

            if not script or not script.strip():
                print("[NewsWorker] Script boş üretildi, işlem iptal ediliyor")
                self.error.emit("Bugün için yeterli haber bulunamadı")
                return

            # 8 - TTS (Seslendirme)
            print("[NewsWorker] TTS başlıyor")
            audio_path = None
            subtitle_path = None
            try:
                audio_path, subtitle_path = self.tts_service.generate(
                    script,
                    filename="daily_news.mp3"
                )
                print("[NewsWorker] Audio:", audio_path)
                print("[NewsWorker] Subtitle:", subtitle_path)
            except Exception as e:
                print("[NewsWorker] TTS HATA:", e)
                self.error.emit("Ses üretimi sırasında hata oluştu")
                return

            if not audio_path or not Path(audio_path).exists():
                print("[NewsWorker] TTS sonrası audio dosyası bulunamadı")
                self.error.emit("Ses üretimi sırasında hata oluştu")
                return

            # 9 - Video (şablon üzerine ses bindirme / efekt)
            print("[NewsWorker] Video işleniyor... (Bu işlem biraz sürebilir)")
            video_path = None
            try:
                self.template_generator.create()
                video_path = self.audio_mixer.create_video(audio_path)
                print(f"[NewsWorker] Video hazır: {video_path}")
            except Exception as e:
                print(f"[NewsWorker] Video işleme HATA: {e}")
                self.error.emit("Video işleme başarısız oldu")
                return

            # 10 - Gündem seçimi
            agenda = self.agenda_selector.select(scored_clusters)

            # 11 - Kritik haberler
            kritik = self._build_tier_lists(scored_clusters)

            print("[NewsWorker] tamamlandı")

            # UI'a göndermeden önce cache'e kaydet
            self.cache.save(
                script,
                audio_path,
                agenda,
                kritik,
                ai_editor,
                video=video_path,
                subtitle=subtitle_path
            )

            # Artık sesi, videoyu ve altyazıyı UI'a dictionary olarak fırlatıyoruz
            self.finished.emit(
                {
                    "agenda": agenda,
                    "kritik": kritik,
                    "ai_editor": ai_editor,
                    "script": script,
                    "audio": audio_path,
                    "subtitle": subtitle_path,
                    "video": video_path,
                }
            )

        except Exception as e:
            print("[NewsWorker ERROR]", e)
            self.error.emit(str(e))