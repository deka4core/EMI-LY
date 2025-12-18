"""
Модуль распознавания речи STT
"""
import json
import os
from vosk import Model, KaldiRecognizer
import numpy as np

class SpeechRecognizer():
    def __init__(self, model_path, sample_rate=16000, debug_mode=True):
        """
        Инициализация распознавателя речи Vosk

        Args:
            model_path (str): Путь к модели Vosk
            sample_rate (int): Частота дискретизации аудио
            debug_mode (bool): Режим отладки
        """
        self.sample_rate = sample_rate
        self.debug_mode = debug_mode
        self.model = None
        self.recognizer = None
        self.model_path = model_path

        self.setup_model(model_path)


    def setup_model(self, model_path):
        """Загрузка модели Vosk"""
        try:
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Модель Vosk не найдена по пути: {model_path}")

            self.model = Model(model_path)
            self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
            self.recognizer.SetWords(True)  # Включаем распознавание отдельных слов

            self.print_debug(f"Модель Vosk загружена: {model_path}")
            self.print_debug(f"Поддерживаемые sample rate: {self.sample_rate}")

        except Exception as e:
            self.print_debug(f"Ошибка загрузки модели Vosk: {e}")
            raise


    def print_debug(self, message):
        """Вывод отладочной информации"""
        if self.debug_mode:
            print(f"[Vosk] {message}")


    def recognize_audio(self, audio_data):
        """
        Распознавание речи из аудиоданных

        Args:
            audio_data (np.array): Аудиоданные в формате float32/int16

        Returns:
            str: Распознанный текст или пустая строка
        """
        if self.recognizer is None:
            self.print_debug("Распознаватель не инициализирован")
            return ""

        try:
            if audio_data.dtype == np.float32 or audio_data.dtype == np.float64:
                audio_int16 = (audio_data * 32767).astype(np.int16)
            else:
                audio_int16 = audio_data.astype(np.int16)

            audio_bytes = audio_int16.tobytes()

            self.recognizer.AcceptWaveform(audio_bytes)
            result = self.recognizer.FinalResult()

            result_dict = json.loads(result)
            recognized_text = result_dict.get("text", "").strip()

            if recognized_text:
                self.print_debug(f"Распознано: '{recognized_text}'")

            return recognized_text

        except Exception as e:
            self.print_debug(f"Ошибка распознавания: {e}")
            return ""


    def reset_recognizer(self):
        """Сброс состояния распознавателя (полезно между командами)"""
        if self.recognizer:
            self.recognizer.Reset()
