class PromptBuilder:

    @staticmethod
    def build_analysis_prompt(cluster, sources: list[str]) -> str:

        articles_text = "\n".join(
            [
                f"- Başlık: {article.title}\n"
                f"  Açıklama: {article.description}"
                for article in cluster.articles
            ]
        )


        return f"""

Sen dünyanın en büyük haber ajansında çalışan kıdemli bir haber editörüsün.

Görevin:
Verilen haber kümesini analiz etmek, gerçek gündem değerini ölçmek ve gereksiz içerikleri elemek.

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



SADECE JSON FORMATINDA CEVAP VER:


{{
    "is_newsworthy": true,
    "summary": "",
    "keywords": [],
    "importance_score": 0,
    "importance_reason": "",
    "category": ""
}}

"""