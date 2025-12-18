import threading
from voice_activation import VoiceActivation

if __name__ == "__main__":
    voice_activation = VoiceActivation(
        sample_rate=48000,
        silence_threshold=0.02,
        silence_duration=3,
        activation_keyword="эмили",
        debug_mode=True,
        keyword_path="./model/porcupine/Emily_en_windows_v3_0_0.ppn",
        vosk_model_path="./model/vosk-model-small-ru-0.22"
    )

    try:
        listener_thread = threading.Thread(target=voice_activation.start_listening)
        listener_thread.daemon = True
        listener_thread.start()

        print("Голосовой ассистент запущен!")
        print("Скажите 'Эмили' для активации")
        print("Нажмите Enter для остановки...")

        input()

    except KeyboardInterrupt:
        print("\nОстановка ассистента...")
    finally:
        voice_activation.stop_listening()
        print("Ассистент остановлен.")