import queue
from datetime import datetime
import time

import numpy as np
import pvporcupine
import scipy
import sounddevice as sd

from stt_engine import SpeechRecognizer
from command_handler import CommandHandler

from keys import PORCUPINE_ACCESS_TOKEN


class VoiceActivation:
    def __init__(self, sample_rate=16000, channels=1,
                 silence_threshold=0.01, silence_duration=2.0,
                 activation_keyword="emily", debug_mode=True,
                 keyword_path=None, vosk_model_path="./model/vosk"):
        """
        Инициализация модуля активации голосом
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.activation_keyword = activation_keyword.lower()
        self.debug_mode = debug_mode

        # Очередь для аудиоданных
        self.audio_queue = queue.Queue()

        # Флаги состояния
        self.is_listening = False
        self.is_recording = False
        self.audio_data = []

        # Адаптация к шуму
        self.noise_profile = None
        self.noise_adapted = False

        # Статистика
        self.activation_count = 0

        # Porcupine настройки
        self.porcupine_access_key = PORCUPINE_ACCESS_TOKEN
        self.keyword_path = keyword_path

        # Инициализация Porcupine
        self.porcupine = None
        self.setup_porcupine()

        # Инициализация распознавателя речи Vosk
        self.speech_recognizer = None
        self.setup_speech_recognizer(vosk_model_path)

        # Инициализация обработчика команд с TTS
        self.command_handler = CommandHandler(debug_mode=debug_mode, enable_tts=True)

    def setup_porcupine(self):
        """Инициализация Porcupine для детектирования ключевых слов"""
        try:
            if self.keyword_path:
                self.porcupine = pvporcupine.create(
                    access_key=self.porcupine_access_key,
                    keyword_paths=[self.keyword_path]
                )

            self.print_debug("Porcupine инициализирован успешно")
            self.print_debug(f"Требуемая sample rate: {self.porcupine.sample_rate}")
            self.print_debug(f"Размер фрейма: {self.porcupine.frame_length}")

            # Обновляем sample_rate если нужно
            if self.sample_rate != self.porcupine.sample_rate:
                self.print_debug(f"Обновляем sample rate с {self.sample_rate} на {self.porcupine.sample_rate}")
                self.sample_rate = self.porcupine.sample_rate

        except Exception as e:
            self.print_debug(f"Ошибка инициализации Porcupine: {e}")
            self.print_debug("Используется fallback детектор")

    def setup_speech_recognizer(self, model_path):
        """Инициализация распознавателя речи Vosk"""
        try:
            self.speech_recognizer = SpeechRecognizer(
                model_path=model_path,
                sample_rate=self.sample_rate,
                debug_mode=self.debug_mode
            )
            self.print_debug("Распознаватель речи Vosk инициализирован")
        except Exception as e:
            self.print_debug(f"Ошибка инициализации Vosk: {e}")
            self.print_debug("Распознавание речи будет отключено")

    def print_debug(self, message):
        """Вывод отладочной информации"""
        if self.debug_mode:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {message}")

    def setup_audio_device(self):
        """Настройка аудиоустройства"""
        try:
            devices = sd.query_devices()
            default_input = sd.default.device[0]

            self.print_debug(f"Доступные аудиоустройства:")
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    status = "ТЕКУЩЕЕ" if i == default_input else ""
                    self.print_debug(f"  {i}: {device['name']} {status}")

            self.print_debug(f"Используется устройство: {devices[default_input]['name']}")
            return True

        except Exception as e:
            self.print_debug(f"Ошибка настройки аудиоустройства: {e}")
            return False

    def audio_callback(self, indata, frames, time, status):
        """Callback-функция для получения аудиоданных"""
        if status:
            self.print_debug(f"Аудио статус: {status}")

        audio_chunk = indata.copy()
        self.audio_queue.put(audio_chunk)

    def adapt_to_noise(self, duration=3.0):
        """Адаптация к фоновому шуму"""
        self.print_debug("Адаптация к фоновому шуму...")

        noise_samples = []
        start_time = time.time()

        def noise_callback(indata, frames, time, status):
            noise_samples.append(indata.copy())

        with sd.InputStream(callback=noise_callback,
                            channels=self.channels,
                            samplerate=self.sample_rate,
                            blocksize=1024):
            time.sleep(duration)

        if noise_samples:
            noise_data = np.concatenate(noise_samples, axis=0)
            self.noise_profile = np.mean(np.abs(noise_data))
            self.noise_adapted = True

            self.print_debug(f"Адаптация завершена. Уровень шума: {self.noise_profile:.4f}")

    def detect_activation_word(self, audio_data):
        """Детектирование ключевого слова с помощью Porcupine"""
        if self.porcupine is None:
            return self.detect_activation_word_fallback(audio_data)

        try:
            if len(audio_data.shape) > 1:
                audio_data = audio_data.flatten()

            if np.max(np.abs(audio_data)) > 0:
                audio_data = audio_data / np.max(np.abs(audio_data))

            audio_int16 = (audio_data * 32767).astype(np.int16)

            required_length = self.porcupine.frame_length
            if len(audio_int16) < required_length:
                audio_int16 = np.pad(audio_int16, (0, required_length - len(audio_int16)))
            elif len(audio_int16) > required_length:
                audio_int16 = audio_int16[:required_length]

            keyword_index = self.porcupine.process(audio_int16)

            if keyword_index >= 0:
                self.print_debug(f"Ключевое слово обнаружено!")
                return True

        except Exception as e:
            self.print_debug(f"Ошибка Porcupine обработки: {e}")

        return False

    def detect_activation_word_fallback(self, audio_data):
        """Fallback детектор если Porcupine не доступен"""
        volume = np.sqrt(np.mean(audio_data ** 2))
        noise_threshold = self.noise_profile * 4 if self.noise_adapted else 0.05

        if volume > noise_threshold:
            self.print_debug(f"Fallback: Обнаружена речь (уровень: {volume:.4f})")
            return True

        return False

    def cleanup(self):
        """Очистка ресурсов"""
        if self.porcupine is not None:
            self.porcupine.delete()
        self.print_debug("Ресурсы Porcupine освобождены")

    def is_silence(self, audio_chunk):
        """Проверка, является ли аудио-фрагмент тишиной"""
        if len(audio_chunk) == 0:
            return True

        volume = np.sqrt(np.mean(audio_chunk ** 2))  # RMS вместо mean abs
        threshold = self.silence_threshold

        if self.noise_adapted:
            threshold = max(self.noise_profile * 2.0, self.silence_threshold)  # увеличил множитель

        is_silent = volume < threshold
        if self.debug_mode and not is_silent:
            self.print_debug(f"Уровень звука: {volume:.4f}, порог: {threshold:.4f}")

        return is_silent

    def save_debug_recording(self, audio_data, filename_prefix="debug"):
        """Сохранение записи для отладки"""
        if not self.debug_mode:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logs/{filename_prefix}_{timestamp}.wav"

        # Нормализуем данные перед сохранением
        audio_data = audio_data / np.max(np.abs(audio_data)) if np.max(np.abs(audio_data)) > 0 else audio_data

        try:
            scipy.io.wavfile.write(filename, self.sample_rate,
                                   (audio_data * 32767).astype(np.int16))
            self.print_debug(f"Запись сохранена: {filename}")
        except Exception as e:
            self.print_debug(f"Ошибка сохранения записи: {e}")

    def record_until_silence(self):
        """Запись до обнаружения тишины"""
        self.print_debug("Начало записи команды...")

        recorded_audio = []
        silence_start_time = None
        recording_start_time = time.time()

        while self.is_recording:
            try:
                audio_chunk = self.audio_queue.get(timeout=1.0)
                recorded_audio.append(audio_chunk)

                current_chunk = audio_chunk

                if self.is_silence(current_chunk):
                    if silence_start_time is None:
                        silence_start_time = time.time()
                        self.print_debug(f"Начало тишины...")
                    elif time.time() - silence_start_time >= self.silence_duration:
                        self.print_debug("Обнаружена продолжительная тишина, завершение записи")
                        break
                else:
                    if silence_start_time is not None:
                        self.print_debug("Голос обнаружен, сброс таймера тишины")
                    silence_start_time = None

                if time.time() - recording_start_time > 30:
                    self.print_debug("Превышено время записи")
                    break

            except queue.Empty:
                continue

        if recorded_audio:
            return np.concatenate(recorded_audio, axis=0)
        return np.array([])

    def start_listening(self):
        """Запуск прослушивания"""
        if self.is_listening:
            self.print_debug("Уже слушаем...")
            return

        self.is_listening = True
        self.print_debug("Запуск модуля активации...")

        if not self.setup_audio_device():
            self.print_debug("Ошибка настройки аудиоустройства")
            return

        if not self.noise_adapted:
            self.adapt_to_noise()

        try:
            with sd.InputStream(callback=self.audio_callback,
                                channels=self.channels,
                                samplerate=self.sample_rate,
                                blocksize=self.porcupine.frame_length if self.porcupine else 1024):

                self.print_debug("Ожидание ключевого слова 'Эмили'...")

                while self.is_listening:
                    try:
                        audio_chunk = self.audio_queue.get(timeout=0.5)

                        if self.detect_activation_word(audio_chunk):
                            self.activation_count += 1
                            self.print_debug("Ключевое слово обнаружено!")

                            self.is_recording = True
                            command_audio = self.record_until_silence()
                            self.is_recording = False

                            if command_audio.size > 0:
                                self.save_debug_recording(command_audio, "command")
                                self.process_command(command_audio)

                            self.print_debug("Ожидание следующей активации...")

                    except queue.Empty:
                        continue

        except Exception as e:
            self.print_debug(f"Ошибка в аудиопотоке: {e}")
        finally:
            self.is_listening = False

    def process_command(self, audio_data):
        """Обработка записанной команды с распознаванием речи"""
        start_time = time.perf_counter()

        duration = len(audio_data) / self.sample_rate
        self.print_debug(f"Команда получена! Длительность: {duration:.2f} сек")

        try:
            # Распознаем речь
            if self.speech_recognizer:
                stt_start = time.perf_counter()
                recognized_text = self.speech_recognizer.recognize_audio(audio_data)
                stt_time = time.perf_counter() - stt_start

                if recognized_text:
                    self.print_debug(f"Распознанная команда: '{recognized_text}'")
                    self.print_debug(f"Время STT: {stt_time:.3f} сек")

                    nlp_start = time.perf_counter()
                    response = self.command_handler.execute_command(recognized_text)
                    nlp_time = time.perf_counter() - nlp_start

                    tts_start = time.perf_counter()
                    self.print_debug(f"Ответ: {response}")
                    tts_time = time.perf_counter() - tts_start

                    total_time = time.perf_counter() - start_time
                    self.print_debug(
                        f"Общее время отклика: {total_time:.3f} сек (STT: {stt_time:.3f}, NLP: {nlp_time:.3f}, TTS_queuing: {tts_time:.3f})")

                    with open("response_times.log", "a") as f:
                        f.write(
                            f"{time.strftime('%Y-%m-%d %H:%M:%S')}, {total_time:.3f}, {stt_time:.3f}, {nlp_time:.3f}, {tts_time:.3f}, '{recognized_text}'\n")

                else:
                    self.print_debug("Речь не распознана")
            else:
                self.print_debug("Распознаватель речи не доступен")

        finally:
            if self.speech_recognizer:
                self.speech_recognizer.reset_recognizer()

    def stop_listening(self):
        """Остановка прослушивания"""
        self.is_listening = False
        self.is_recording = False

        if hasattr(self, 'command_handler') and self.command_handler.tts_engine:
            self.command_handler.tts_engine.shutdown()

        self.print_debug("Модуль активации остановлен")


    def cleanup(self):
        """Очистка ресурсов"""
        if self.porcupine is not None:
            self.porcupine.delete()
        self.print_debug("Ресурсы Porcupine освобождены")