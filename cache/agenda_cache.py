from pathlib import Path
import json
from datetime import datetime


class AgendaCache:

    def __init__(self):

        self.path = Path(
            "cache/daily_news.json"
        )

        self.path.parent.mkdir(
            exist_ok=True
        )


    def exists_today(self):

        if not self.path.exists():
            return False

        try:
            data = json.loads(
                self.path.read_text(
                    encoding="utf-8"
                )
            )
        except Exception:
            return False

        return (
            data.get("date")
            ==
            datetime.now().strftime("%Y-%m-%d")
        )


    def load(self):

        return json.loads(
            self.path.read_text(
                encoding="utf-8"
            )
        )




    def save(
        self,
        script,
        audio,
        agenda=None,
        kritik=None,
        ai_editor=None
    ):
        data = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "script": script,
            "audio": audio,
            "agenda": agenda or [],
            "kritik": kritik or [],
            "ai_editor": ai_editor or {}
        }
        
        # Dosyaya yazma işleminiz... (Örn: json.dump)
        # with open(self.cache_file, "w", encoding="utf-8") as f:
        #     json.dump(data, f, ensure_ascii=False, indent=4)

        self.path.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=4
            ),
            encoding="utf-8"
        )