from services.video.audio_mixer import AudioMixer


mixer = AudioMixer()


video = mixer.create_video(
    "outputs/headless_white_collar.mp3"
)


print(video)