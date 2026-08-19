from pathlib import Path
from PySide6.QtCore import QObject, Signal, Slot
from dateutil import parser as date_parser
from dateutil.tz import gettz, tzutc
import hashlib

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

from services.video.scrolling_text_generator import ScrollingTextGenerator
from services.video.audio_mixer import AudioMixer


class NewsWorker(QObject):

    finished = Signal(dict)
    error = Signal(str)
    progress = Signal(int)
    status = Signal(str)

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
        self.agenda_selector = AgendaSelector(
            max_per_region=2
        )

        self.scrolling_text_generator = ScrollingTextGenerator()
        self.audio_mixer = AudioMixer()

    def _build_tier_lists(self, scored_clusters):
        kritik = []

        for cluster in scored_clusters:
            tier = ImportanceCalculator.tier_for(
                cluster.score
            )

            if tier != "kritik":
                continue

            item = {
                "category": getattr(
                    cluster,
                    "category",
                    ""
                ) or "",
                "region": self._resolve_region(
                    cluster
                ),
                "importance": cluster.score,
                "repeat_count": cluster.repeat_count,
                "sources": cluster.sources,
                "body": build_plain_summary(
                    cluster
                ),
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
                        getattr(
                            cluster,
                            "title",
                            ""
                        )
                    ),
                    "summary": build_plain_summary(
                        cluster
                    ),
                    "importance": getattr(
                        cluster,
                        "score",
                        0
                    )
                }
            )

        return news

    def _resolve_region(self, cluster):
        from collections import Counter

        regions = [
            article.region
            for article in cluster.articles
            if getattr(
                article,
                "region",
                ""
            )
        ]

        if not regions:
            return ""

        return Counter(
            regions
        ).most_common(1)[0][0]

    def _convert_to_turkey_time(
        self,
        published_at
    ):
        try:
            published_date = date_parser.parse(
                published_at
            )
        except Exception:
            return None

        if published_date.tzinfo is None:
            published_date = published_date.replace(
                tzinfo=tzutc()
            )

        istanbul = gettz(
            "Europe/Istanbul"
        )

        return published_date.astimezone(
            istanbul
        )

    def _is_within_agenda_window(
        self,
        published_at
    ):
        if published_at is None:
            return True

        turkey_time = (
            self._convert_to_turkey_time(
                published_at
            )
        )

        if turkey_time is None:
            return False

        hour = turkey_time.hour

        return 7<= hour < 19

    def _filter_agenda_window(
        self,
        articles
    ):
        return [
            article
            for article in articles
            if self._is_within_agenda_window(
                article.published_at
            )
        ]

    def _create_news_hash(
        self,
        articles
    ):
        items = []

        for article in articles:
            title = str(
                getattr(
                    article,
                    "title",
                    ""
                ) or ""
            ).strip().lower()

            url = str(
                getattr(
                    article,
                    "url",
                    ""
                ) or ""
            ).strip()

            published_at = str(
                getattr(
                    article,
                    "published_at",
                    ""
                ) or ""
            )

            items.append(
                f"{title}|{url}|{published_at}"
            )

        items.sort()

        raw = "\n".join(items)

        return hashlib.sha256(
            raw.encode("utf-8")
        ).hexdigest()

    def _load_cached_result(
        self,
        data
    ):
        audio_path = data.get("audio")
        video_path = data.get("video")

        if (
            audio_path
            and Path(audio_path).exists()
            and video_path
            and Path(video_path).exists()
        ):
            return True

        return False

    @Slot()
    def run(self):
        try:
            print("[NewsWorker] başladı")

            self.status.emit("Sistem kontrol ediliyor...")
            self.progress.emit(5)

            if self.cache.exists_today():
                print("[NewsWorker] Bugünün gündemi cache'den alınıyor")

                self.status.emit(
                    "Bugünün gündemi önbellekten yükleniyor..."
                )
                self.progress.emit(90)

                data = self.cache.load()

                audio_path = data.get("audio")
                video_path = data.get("video")

                if (
                    audio_path
                    and Path(audio_path).exists()
                    and video_path
                    and Path(video_path).exists()
                ):
                    self.progress.emit(100)
                    self.status.emit("Hazır!")

                    self.finished.emit(data)
                    return

                print(
                    "[NewsWorker] Cache bulundu ancak video veya ses dosyası eksik."
                )
                print(
                    "[NewsWorker] Eksik dosyalar yeniden oluşturulacak."
                )

            self.status.emit("Güncel haberler taranıyor...")
            self.progress.emit(10)

            articles = self.news_service.get_combined_news()
            articles = self.noise_filter.filter(articles)

            print(
                f"[NewsWorker] Haber sayısı: {len(articles)}"
            )

            self.status.emit(
                "Gündem saat aralığı filtreleniyor..."
            )
            self.progress.emit(20)

            articles = self._filter_agenda_window(articles)

            if not articles:
                self.error.emit(
                    "Gündem saat aralığında haber bulunamadı"
                )
                return

            self.duplicate_detector.diagnose_threshold(
                articles
            )

            self.duplicate_detector.inspect_clusters(
                articles,
                threshold=0.55,
                min_size=3
            )

            self.status.emit(
                "Benzer haberler temizleniyor..."
            )
            self.progress.emit(30)

            clusters = self.duplicate_detector.remove_duplicates(
                articles
            )

            self.status.emit(
                "Haber başlıkları sıralanıyor..."
            )
            self.progress.emit(40)

            clusters = self.headline_ranker.rank(
                clusters
            )

            self.status.emit(
                "Haber kategorileri sınıflandırılıyor..."
            )
            self.progress.emit(45)

            clusters = self.category_classifier.classify(
                clusters
            )

            self.status.emit(
                "Haber önem puanları hesaplanıyor..."
            )
            self.progress.emit(50)

            scored_clusters = self.importance_calculator.calculate(
                clusters
            )

            top_clusters = scored_clusters[:20]

            if not top_clusters:
                self.error.emit(
                    "Bugün için yeterli haber bulunamadı"
                )
                return

            self.status.emit(
                "Haberler yapay zeka ile çevriliyor (Gemini)..."
            )
            self.progress.emit(60)

            top_clusters = (
                self.gemini_service.translate_clusters(
                    top_clusters
                )
            )

            self.status.emit(
                "Yapay zeka bülteni düzenliyor..."
            )
            self.progress.emit(68)

            ai_editor = self.gemini_service.edit_news(
                top_clusters
            )

            self.status.emit(
                "Haber bülteni metni oluşturuluyor..."
            )
            self.progress.emit(75)

            script_news = self._build_script_news(
                top_clusters
            )

            script = self.script_service.generate(
                script_news
            )

            if not script or not script.strip():
                self.error.emit(
                    "Script boş üretildi, işlem iptal ediliyor"
                )
                return

            self.status.emit(
                "Seslendirme (TTS) ve altyazı üretiliyor..."
            )
            self.progress.emit(85)

            audio_path = None
            subtitle_path = None

            try:
                audio_path, subtitle_path = (
                    self.tts_service.generate(
                        script,
                        filename="daily_news.mp3"
                    )
                )
            except Exception as e:
                print(
                    "[NewsWorker] TTS HATA:",
                    e
                )

                self.error.emit(
                    "Ses üretimi sırasında hata oluştu"
                )
                return

            if (
                not audio_path
                or not Path(audio_path).exists()
            ):
                self.error.emit(
                    "Ses dosyası bulunamadı"
                )
                return

            self.status.emit(
                "Video oluşturuluyor ve ses birleştiriliyor..."
            )
            self.progress.emit(95)

            video_path = None

            try:
                scrolling_video = (
                    self.scrolling_text_generator.create(
                        script,
                        audio_path
                    )
                )

                video_path = self.audio_mixer.create_video(
                    scrolling_video,
                    audio_path
                )

            except Exception as e:
                print(
                    f"[NewsWorker] Video işleme HATA: {e}"
                )

                self.error.emit(
                    "Video işleme başarısız oldu"
                )
                return

            agenda = self.agenda_selector.select(
                scored_clusters
            )

            kritik = self._build_tier_lists(
                scored_clusters
            )

            self.cache.save(
                script,
                audio_path,
                agenda,
                kritik,
                ai_editor,
                video=video_path,
                subtitle=subtitle_path
            )

            print(
                "[NewsWorker] Yeni gündem videosu cache'e kaydedildi"
            )

            self.progress.emit(100)
            self.status.emit("Tamamlandı!")

            self.finished.emit(
                {
                    "agenda": agenda,
                    "kritik": kritik,
                    "ai_editor": ai_editor,
                    "script": script,
                    "audio": audio_path,
                    "subtitle": subtitle_path,
                    "video": video_path
                }
            )

        except Exception as e:
            print(
                "[NewsWorker ERROR]",
                e
            )

            self.error.emit(
                str(e)
            )