import os
import queue
import threading
import time
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from config import SAMPLERATE, INPUT_DEVICE

model_path = "vosk-agent/vosk-model-small-ru-0.22"
if not os.path.exists(model_path):
    raise OSError(f"Модель {model_path} не найдена!")

model = Model(model_path)
recognizer = KaldiRecognizer(model, 48000) # 48 КГц

# Очередь для аудио-данных
audio_queue = queue.Queue()
is_recording = False
audio_data = bytearray()
recorded_audio = None

def callback(input_data, frames, time, status):
    if is_recording:
        audio_queue.put(bytes(input_data))

def process_audio():
    while True:
        try:
            if not audio_queue.empty():
                data = audio_queue.get_nowait()
                if is_recording:
                    audio_data.extend(data)
        except queue.Empty:
            time.sleep(0.1)

def main():
    global is_recording, recorded_audio, audio_data
    processing_thread = threading.Thread(target=process_audio, daemon=True)
    processing_thread.start()

    stream = sd.InputStream(
        device=INPUT_DEVICE,
        samplerate=SAMPLERATE,
        blocksize=8000,
        dtype="int16",
        channels=1,
        callback=callback
    )
    stream.start()

    print("Управление:")
    print("1 - записать")
    print("2 - остановить")
    print("3 - распознать")
    print("0 - выход")

    try:
        while True:
            cmd = input("> ").strip()

            if cmd == "1":
                is_recording = True
                audio_data = bytearray()
                recorded_audio = None
                print("Запись...")

            elif cmd == "2" and is_recording:
                is_recording = False
                recorded_audio = bytes(audio_data)

            elif cmd == "3" and recorded_audio:
                recognizer.AcceptWaveform(recorded_audio)
                result = recognizer.Result()
                text = eval(result)["text"]
                print(f"Текст: {text}")

            elif cmd == "0":
                break

    finally:
        stream.stop()
        stream.close()


if __name__ == "__main__":
    main()