class PromptBuilder:

    # Bir kümede çok kaynaklı haberlerde onlarca makale birikebiliyor;
    # hepsinin (uzun) açıklamasını tek prompt'a basmak MAX_TOKENS hatasına
    # yol açıyordu. Temsilci olarak en fazla N makale, her biri kırpılmış
    # açıklamayla gönderiliyor - analiz kalitesini etkilemeden token
    # kullanımını sınırlı tutar.
    MAX_ARTICLES_IN_PROMPT = 6
    MAX_DESCRIPTION_CHARS = 350


    @staticmethod
    def _truncate(text, limit):

        if not text:
            return text

        if len(text) <= limit:
            return text

        return text[:limit].rsplit(" ", 1)[0] + "..."


    @classmethod
    def build_analysis_prompt(cls, cluster, sources: list[str]) -> str:

        representative_articles = cluster.articles[:cls.MAX_ARTICLES_IN_PROMPT]

        articles_text = "\n".join(
            [
                f"- Başlık: {article.title}\n"
                f"  Açıklama: {cls._truncate(article.description, cls.MAX_DESCRIPTION_CHARS)}"
                for article in representative_articles
            ]
        )


        return f"""

Sen dünyanın en büyük haber ajansında çalışan kıdemli bir haber editörüsün.

Görevin:
Verilen haber kümesini analiz etmek, gerçek gündem değerini ölçmek ve gereksiz içerikleri elemek.

ÖNEMLİ DİL KURALI:
Analiz talimatları Türkçe olsa bile, JSON çıktısındaki TÜM metin alanları
("summary", "importance_reason", "keywords" içindeki her öğe) İNGİLİZCE
olmalı. Haber içerikleri Türkçe olsa dahi özeti İngilizce yaz. Sadece
"category" alanı aşağıdaki listedeki Türkçe kategori adlarından biri olmalı.

HABER BAŞLIĞI:
{cluster.title}


MEVCUT KATEGORİ:
{cluster.category}


SİSTEM PUANI:
{cluster.score}


KAÇ FARKLI KAYNAKTA GEÇİYOR:
{cluster.source_count}


KAYNAKLAR:
{", ".join(sources)}


HABER İÇERİKLERİ:

{articles_text}



ANALİZ KURALLARI:


1) Önce haber kalitesini değerlendir.

Aşağıdaki içerikleri düşük önem olarak değerlendir:

- Magazin dedikoduları
- Ünlülerin özel hayatı
- Film/dizi haberleri
- Yemek tarifleri
- SEO amaçlı "bugün ne oldu" sayfaları
- Tıklama amaçlı başlıklar
- Tek kaynaktan gelen önemsiz haberler


2) Gerçek gündem haberlerini önceliklendir:

Öncelik sırası:

1. Savaş, kriz, afet, deprem
2. Devlet kararları ve siyasi gelişmeler
3. Ekonomik gelişmeler
4. Finans piyasaları
5. Sağlık krizleri
6. Teknoloji gelişmeleri
7. Spor
8. Magazin


3) Kategori kontrolü yap.

Sadece şu kategorilerden birini kullan:

Siyaset
Ekonomi
Borsa
Teknoloji
Sağlık
Afet
Spor
Magazin
Dünya
Diğer


4) Haber gerçekten önemli değilse:

importance_score değerini düşür.


5) Önem puanı ver:

0-20:
Önemsiz / gündem değil

21-50:
Orta önem

51-80:
Önemli

81-100:
Kritik gündem



SADECE JSON FORMATINDA CEVAP VER (summary, importance_reason ve keywords
alanlarındaki TÜM metinler İngilizce olmalı, category Türkçe kalmalı):


{{
    "is_newsworthy": true,
    "summary": "",
    "keywords": [],
    "importance_score": 0,
    "importance_reason": "",
    "category": ""
}}

"""