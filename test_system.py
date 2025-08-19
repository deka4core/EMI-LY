import tempfile
import wave
import sounddevice as sd


def save_and_play_audio(data, samplerate=16000):
    """Сохранить и воспроизвести аудио через sounddevice"""
    # Сохраняем во временный файл
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        with wave.open(f.name, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(samplerate)
            wf.writeframes(data)

        # Воспроизводим
        print("🔊 Воспроизвожу запись...")
        try:
            import numpy as np
            with wave.open(f.name, 'rb') as wf:
                frames = wf.readframes(wf.getnframes())
                audio_array = np.frombuffer(frames, dtype=np.int16)
                sd.play(audio_array, samplerate)
                sd.wait()
        except Exception as e:
            print(f"Ошибка воспроизведения: {e}")

        # Удаляем временный файл
        os.unlink(f.name)
        return f.name