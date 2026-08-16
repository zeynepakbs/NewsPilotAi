from pathlib import Path
import json
from datetime import datetime, timedelta


class AgendaCache:

    def __init__(self):
        self.path = Path("cache/daily_news.json")
        self.path.parent.mkdir(exist_ok=True)

    def _agenda_date(self, dt=None):
        if dt is None:
            dt = datetime.now()

        if dt.hour < 7:
            dt = dt - timedelta(days=1)

        return dt.strftime("%Y-%m-%d")

    def exists_today(self):
        if not self.path.exists():
            return False

        try:
            data = json.loads(
                self.path.read_text(encoding="utf-8")
            )
        except Exception:
            return False

        return data.get("date") == self._agenda_date()

    def load(self):
        return json.loads(
            self.path.read_text(encoding="utf-8")
        )

    def save(
        self,
        script,
        audio,
        agenda=None,
        kritik=None,
        ai_editor=None,
        video=None,
        subtitle=None
    ):
        data = {
            "date": self._agenda_date(),
            "script": script,
            "audio": audio,
            "video": video,
            "subtitle": subtitle,
            "agenda": agenda or [],
            "kritik": kritik or [],
            "ai_editor": ai_editor or {}
        }

        self.path.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=4
            ),
            encoding="utf-8"
        )