import re

class EntityDetector:

    IGNORE_ENTITIES = {
        "türkiye", "turkiye", "turkey",
        "irak", "iran", "almanya", "germany",
        "spain", "ispanya", "abd", "amerika",
        "america", "usa", "israil", "israel",
        "avrupa", "europe", "dünya", "world",
        # STOP_ENTITIES ile birleştirdik:
        "bakan", "başkan", "government", "news"
    }

    def __init__(self):
        # Regex kuralını 1 kere derliyoruz (Milyonlarca kez derlenmekten kurtulduk)
        self.clean_pattern = re.compile(r"[^A-Za-zÇĞİÖŞÜçğıöşü]")
        
        # Daha önce işlenen başlıkların Entity'lerini hafızada tutacak sözlük
        self.cache = {}

    def extract(self, title: str):
        if not title:
            return set()
            
        # Eğer bu başlık daha önce işlendiyse, işlemi tekrar yapma, hafızadan dön!
        if title in self.cache:
            return self.cache[title]

        words = title.split()
        entities = set()

        for word in words:
            # Önceden derlenmiş regex'i kullanıyoruz (Çok daha hızlı)
            clean = self.clean_pattern.sub("", word)
            clean = clean.lower()

            if len(clean) < 3:
                continue

            # Blacklist kontrolü
            if clean in self.IGNORE_ENTITIES:
                continue

            # Büyük harfle başlayan gerçek isim adayları
            original = word.replace("'", "")

            if original and original[0].isupper():
                entities.add(clean)

        # Sonucu hafızaya kaydet
        self.cache[title] = entities
        
        return entities

    def similarity(self, title1: str, title2: str):
        # Artık bu fonksiyon binlerce kez çağrılsa bile, extract() hafızadan okuduğu için anında yanıt verecek
        e1 = self.extract(title1)
        e2 = self.extract(title2)

        if not e1 or not e2:
            return 0

        intersection = len(e1.intersection(e2))
        union = len(e1.union(e2))

        if union == 0:
            return 0

        return intersection / union