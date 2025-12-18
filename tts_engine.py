import pyttsx3
import threading
import queue
import time
from typing import Optional


class TTSEngine:
    def __init__(self, rate=150, volume=0.9, voice_id=None, debug_mode=True):
        """
        Инициализация локального TTS движка
        """
        self.debug_mode = debug_mode
        self.engine = None
        self.is_speaking = False
        self.speech_queue = queue.Queue()
        self.last_speech_time = 0
        self.speech_lock = threading.Lock()
        self._shutdown_flag = False

        self.setup_engine(rate, volume, voice_id)

        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()

    def setup_engine(self, rate: int, volume: float, voice_id: Optional[int]):
        """Настройка TTS движка"""
        try:
            self.engine = pyttsx3.init()

            # Настройка параметров
            self.engine.setProperty('rate', rate)
            self.engine.setProperty('volume', volume)

            # Настройка голоса
            voices = self.engine.getProperty('voices')
            if voices:
                if voice_id is not None and voice_id < len(voices):
                    self.engine.setProperty('voice', voices[voice_id].id)
                else:
                    for voice in voices:
                        if 'russian' in voice.name.lower() or 'russian' in voice.id.lower():
                            self.engine.setProperty('voice', voice.id)
                            self.print_debug(f"Выбран русский голос: {voice.name}")
                            break
                    else:
                        self.engine.setProperty('voice', voices[0].id)
                        self.print_debug(f"Выбран голос по умолчанию: {voices[0].name}")

            self.engine.connect('started-utterance', self._on_start_speech)
            self.engine.connect('finished-utterance', self._on_end_speech)

            self.print_debug("TTS движок инициализирован успешно")

        except Exception as e:
            self.print_debug(f"Ошибка инициализации TTS: {e}")
            raise

    def _on_start_speech(self, name='tts_message'):
        """Обработчик начала речи"""
        self.print_debug("Начало воспроизведения речи")
        with self.speech_lock:
            self.is_speaking = True

    def _on_end_speech(self, name='tts_message'):
        """Обработчик окончания речи"""
        self.print_debug("Окончание воспроизведения речи")
        with self.speech_lock:
            self.is_speaking = False

    def print_debug(self, message: str):
        """Вывод отладочной информации"""
        if self.debug_mode:
            print(f"[TTS] {message}")

    def speak(self, text: str):
        """
        Произнесение текста
        """
        if not text or self.engine is None or self._shutdown_flag:
            return

        cleaned_text = self._clean_text(text)

        self.speech_queue.put(cleaned_text)
        self.print_debug(f"Добавлено в очередь: '{cleaned_text[:30]}...'")

    def _process_queue(self):
        """Фоновая обработка очереди сообщений"""
        while not self._shutdown_flag:
            try:
                text = self.speech_queue.get(timeout=0.5)
                if text and not self._shutdown_flag:
                    self.print_debug(f"Начинаю говорить: '{text[:50]}...'")
                    self.last_speech_time = time.time()

                    try:
                        self.engine.startLoop(False)

                        self.engine.say(text)

                        start_time = time.time()
                        while self.engine.isBusy():
                            self.engine.iterate()

                            # Таймаут на случай зависания
                            if time.time() - start_time > 10.0:  # 10 секунд таймаут
                                self.print_debug("Таймаут речи")
                                break

                        self.engine.endLoop()

                        self.print_debug("Речь завершена успешно")

                    except Exception as e:
                        self.print_debug(f"Ошибка при воспроизведении: {e}")
                        try:
                            self.engine.endLoop()
                        except:
                            pass

                    finally:
                        with self.speech_lock:
                            self.is_speaking = False

            except queue.Empty:
                continue
            except Exception as e:
                self.print_debug(f"Ошибка в обработке очереди: {e}")
                with self.speech_lock:
                    self.is_speaking = False

    def _clean_text(self, text: str) -> str:
        """Очистка текста для лучшего произношения"""
        replacements = {
            '...': '.',
            '..': '.',
            'GB': 'гигабайт',
            'MB': 'мегабайт',
        }

        cleaned = text
        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)

        cleaned = ' '.join(cleaned.split())
        return cleaned

    def _finished(self, timeout: float = 10.0) -> bool:
        """
        Ожидание завершения текущего воспроизведения
        """
        start_time = time.time()
        while self.is_speaking:
            if time.time() - start_time > timeout:
                self.print_debug("Таймаут ожидания завершения речи")
                return False
            time.sleep(0.1)
        return True

    def get_status(self):
        """Получение статуса TTS"""
        return {
            'is_speaking': self.is_speaking,
            'queue_size': self.speech_queue.qsize(),
            'last_speech_time': self.last_speech_time
        }

    def stop(self):
        """Остановка воспроизведения"""
        if self.engine:
            try:
                self.engine.stop()
                time.sleep(0.5)
            except Exception as e:
                self.print_debug(f"Ошибка при остановке: {e}")

        with self.speech_lock:
            self.is_speaking = False

    def shutdown(self):
        """Полное выключение TTS движка"""
        self.print_debug("Завершение работы TTS...")
        self._shutdown_flag = True
        self.stop()

        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
            except queue.Empty:
                break

        if self.engine:
            try:
                del self.engine
                self.engine = None
            except:
                pass

        self.print_debug("TTS завершил работу")