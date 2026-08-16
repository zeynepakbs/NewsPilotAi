from services.video.scrolling_text_generator import ScrollingTextGenerator
from services.video.audio_mixer import AudioMixer

SCRIPT = """
Hello everyone and welcome back to the daily briefing.
We start today with a major development in Washington. 
The United States Senate has officially confirmed a new attorney general.
"""

def main():
    print("\n[ADIM 1] İşlem başlıyor...")
    audio_path = "outputs/daily_news.mp3"
    
    print("[ADIM 2] YAZI VİDEOSU OLUŞTURULUYOR...")
    generator = ScrollingTextGenerator()
    scrolling_video = generator.create(SCRIPT, audio_path)
    
    print(f"[ADIM 3] YAZI VİDEOSU BİTTİ ({scrolling_video}). SES BİRLEŞTİRME (AudioMixer) BAŞLIYOR...")
    mixer = AudioMixer()
    final_video = mixer.create_video(scrolling_video, audio_path)
    
    print("[ADIM 4] HER ŞEY BAŞARILI! Sonuç:", final_video)

if __name__ == "__main__":
    main()