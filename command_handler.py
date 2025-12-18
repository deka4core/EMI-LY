"""
Модуль обработки команд
Ядро логики
"""
import os
import sys
import subprocess
import webbrowser
import platform
import psutil
import datetime
import time
import requests
from typing import Dict, List, Callable
import json
from tts_engine import TTSEngine


class CommandHandler:
    def __init__(self, debug_mode=True, enable_tts=True):
        """
        Инициализация обработчика команд

        Args:
            debug_mode (bool): Режим отладки
            enable_tts (bool): Включение голосовых ответов
        """
        self.debug_mode = debug_mode
        self.enable_tts = enable_tts
        self.commands = self._initialize_commands()
        self.system_info = self._get_system_info()

        # Инициализация TTS
        self.tts_engine = None
        if enable_tts:
            self.setup_tts()

    def setup_tts(self):
        """Инициализация TTS движка"""
        try:
            self.tts_engine = TTSEngine(
                rate=160,
                volume=0.8,
                debug_mode=self.debug_mode
            )
            self.print_debug("TTS движок инициализирован")

        except Exception as e:
            self.print_debug(f"Ошибка инициализации TTS: {e}")
            self.tts_engine = None

    def _initialize_commands(self) -> Dict[str, Callable]:
        """Инициализация словаря команд с большим количеством вариантов"""
        commands = {
            # Приветствия и базовые команды
            "привет": lambda: "Привет! Чем могу помочь?",
            "здравствуй": lambda: "Здравствуйте! Рад вас слышать.",
            "добрый день": lambda: "Добрый день! Чем могу быть полезен?",

            # Команды "как дела"
            "как дела": lambda: "Всё отлично! Готова выполнять ваши команды.",
            "как твои дела": lambda: "У меня всё прекрасно, спасибо что спросили!",
            "как ты": lambda: "Всё хорошо, работаю в штатном режиме!",
            "как настроение": lambda: "У меня всегда отличное настроение!",
            "как жизнь": lambda: "Жизнь прекрасна, особенно когда могу помочь!",

            # Благодарности
            "спасибо": lambda: "Пожалуйста! Обращайтесь ещё.",
            "благодарю": lambda: "Всегда рада помочь!",

            # Системные команды
            "перезагрузи компьютер": self.restart_computer,
            "выключи компьютер": self.shutdown_computer,
            "открой диспетчер задач": self.open_task_manager,
            "покажи системную информацию": self.show_system_info,
            "очисти экран": self.clear_screen,

            # Приложения
            "открой блокнот": self.open_notepad,
            "открой калькулятор": self.open_calculator,
            "открой проводник": self.open_explorer,
            "открой браузер": self.open_browser,

            # Время и дата
            "который час": self.show_time,
            "сколько время": self.show_time,
            "какое время": self.show_time,
            "текущее время": self.show_time,
            "какая дата": self.show_date,
            "какое сегодня число": self.show_date,
            "текущая дата": self.show_date,

            # Веб-команды
            "открой youtube": self.open_youtube,
            "открой ютуб": self.open_youtube,
            "открой google": self.open_google,
            "открой гугл": self.open_google,

            # Информационные
            "что ты умеешь": self.show_capabilities,
            "расскажи о себе": lambda: "Я голосовой ассистент, созданный для помощи в повседневных задачах.",
            "кто ты": lambda: "Я ваш голосовой помощник, готовый помочь с различными задачами.",
        }
        return commands

    def execute_command(self, command_text: str) -> str:
        """
        Выполнение команды на основе распознанного текста
        """
        command_lower = command_text.lower().strip()
        self.print_debug(f"Поиск команды для: '{command_lower}'")

        # Поиск точного совпадения
        if command_lower in self.commands:
            try:
                result = self.commands[command_lower]()
                self.print_debug(f"Команда выполнена: {command_lower}")
                self.speak_response(result)
                return result
            except Exception as e:
                error_msg = f"Ошибка выполнения команды: {e}"
                self.print_debug(error_msg)
                self.speak_response("Произошла ошибка")
                return error_msg

        # Поиск частичного совпадения
        for cmd, func in self.commands.items():
            if cmd in command_lower:
                try:
                    result = func()
                    self.print_debug(f"Команда выполнена (частичное совпадение): {cmd}")
                    self.speak_response(result)
                    return result
                except Exception as e:
                    error_msg = f"Ошибка выполнения команды: {e}"
                    self.print_debug(error_msg)
                    self.speak_response("Произошла ошибка")
                    return error_msg

        # Если команда не найдена
        self.print_debug(f"Команда не найдена: {command_lower}")
        not_found_response = "Извините, я не понял команду. Попробуйте сказать иначе."
        self.speak_response(not_found_response)
        return not_found_response

    def speak_response(self, text: str):
        """Произнесение ответа"""
        if self.enable_tts and self.tts_engine and text:
            self.tts_engine.speak(text)

    def show_capabilities(self) -> str:
        """Показ возможностей ассистента"""
        capabilities = [
            "Управление системой: перезагрузка, выключение",
            "Открытие приложений: браузер, блокнот, калькулятор",
            "Информация: время, дата, системная информация",
            "Веб-команды: открытие сайтов",
            "И многое другое!"
        ]
        response = "Я умею:\n" + "\n".join(f"- {cap}" for cap in capabilities)
        return response

    def _get_system_info(self) -> Dict:
        """Получение информации о системе"""
        return {
            "os": platform.system(),
            "version": platform.version(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
            "memory": f"{psutil.virtual_memory().total // (1024 ** 3)} GB"
        }

    def print_debug(self, message: str):
        """Вывод отладочной информации"""
        if self.debug_mode:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"[CommandHandler {timestamp}] {message}")

    # === СИСТЕМНЫЕ КОМАНДЫ ===

    def restart_computer(self) -> str:
        """Перезагрузка компьютера"""
        self.print_debug("Выполняется перезагрузка компьютера...")

        if platform.system() == "Windows":
            os.system("shutdown /r /t 5")
            return "Компьютер будет перезагружен через 5 секунд"
        elif platform.system() == "Linux":
            os.system("sudo shutdown -r now")
            return "Компьютер перезагружается"
        else:
            return "Перезагрузка не поддерживается на этой системе"

    def shutdown_computer(self) -> str:
        """Выключение компьютера"""
        self.print_debug("Выполняется выключение компьютера...")

        if platform.system() == "Windows":
            os.system("shutdown /s /t 5")
            return "Компьютер будет выключен через 5 секунд"
        elif platform.system() == "Linux":
            os.system("sudo shutdown -h now")
            return "Компьютер выключается"
        else:
            return "Выключение не поддерживается на этой системе"

    def open_task_manager(self) -> str:
        """Открытие диспетчера задач"""
        self.print_debug("Открываю диспетчер задач...")

        if platform.system() == "Windows":
            os.system("taskmgr")
            return "Диспетчер задач открыт"
        elif platform.system() == "Linux":
            os.system("gnome-system-monitor")
            return "Системный монитор открыт"
        else:
            return "Диспетчер задач не поддерживается на этой системе"

    def show_system_info(self) -> str:
        """Показ системной информации"""
        info = self.system_info
        response = (
            f"Информация о системе:\n"
            f"ОС: {info['os']}\n"
            f"Версия: {info['version']}\n"
            f"Архитектура: {info['architecture']}\n"
            f"Память: {info['memory']}\n"
            f"Процессор: {info['processor'][:50]}..."  # Обрезаем длинные названия
        )
        self.print_debug("Показываю системную информацию")
        return response

    def clear_screen(self) -> str:
        """Очистка экрана терминала"""
        os.system('cls' if platform.system() == 'Windows' else 'clear')
        self.print_debug("Экран очищен")
        return "Экран очищен"

    # === КОМАНДЫ ПРИЛОЖЕНИЙ ===

    def open_notepad(self) -> str:
        """Открытие блокнота"""
        self.print_debug("Открываю блокнот...")

        if platform.system() == "Windows":
            os.system("notepad")
            return "Блокнот открыт"
        elif platform.system() == "Linux":
            os.system("gedit")
            return "Текстовый редактор открыт"
        else:
            return "Блокнот не поддерживается на этой системе"

    def open_calculator(self) -> str:
        """Открытие калькулятора"""
        self.print_debug("Открываю калькулятор...")

        if platform.system() == "Windows":
            os.system("calc")
            return "Калькулятор открыт"
        elif platform.system() == "Linux":
            os.system("gnome-calculator")
            return "Калькулятор открыт"
        else:
            return "Калькулятор не поддерживается на этой системе"

    def open_explorer(self) -> str:
        """Открытие проводника"""
        self.print_debug("Открываю проводник...")

        if platform.system() == "Windows":
            os.system("explorer")
            return "Проводник открыт"
        elif platform.system() == "Linux":
            os.system("nautilus")
            return "Файловый менеджер открыт"
        else:
            return "Проводник не поддерживается на этой системе"

    def open_browser(self) -> str:
        """Открытие браузера по умолчанию"""
        self.print_debug("Открываю браузер...")

        try:
            webbrowser.open_new("about:blank")
            return "Браузер открыт"
        except Exception as e:
            return f"Не удалось открыть браузер: {e}"

    def close_all_apps(self) -> str:
        """Закрытие всех приложений"""
        self.print_debug("Закрываю приложения...")

        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            closed_count = 0
            system_processes = ['system', 'svchost.exe', 'explorer.exe', 'taskmgr.exe']

            for proc in processes:
                try:
                    if proc.info['name'].lower() not in system_processes:
                        proc.terminate()
                        closed_count += 1
                except:
                    continue

            return f"Закрыто приложений: {closed_count}"
        except Exception as e:
            return f"Ошибка при закрытии приложений: {e}"

    # === ВЕБ-КОМАНДЫ ===

    def open_youtube(self) -> str:
        """Открытие YouTube"""
        self.print_debug("Открываю YouTube...")
        webbrowser.open_new("https://www.youtube.com")
        return "YouTube открыт"

    def open_google(self) -> str:
        """Открытие Google"""
        self.print_debug("Открываю Google...")
        webbrowser.open_new("https://www.google.com")
        return "Google открыт"

    # === ИНФОРМАЦИОННЫЕ КОМАНДЫ ===

    def show_time(self) -> str:
        """Показ текущего времени"""
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.print_debug(f"Текущее время: {current_time}")
        return f"Сейчас {current_time}"

    def show_date(self) -> str:
        """Показ текущей даты"""
        current_date = datetime.datetime.now().strftime("%d.%m.%Y")
        self.print_debug(f"Текущая дата: {current_date}")
        return f"Сегодня {current_date}"

    def show_weather(self) -> str:
        """Показ погоды (заглушка)"""
        self.print_debug("Запрос погоды...")
        # Здесь можно интегрировать с API погоды
        return "Для показа погоды необходимо настроить API. Сейчас солнечно! 🌞"

    # === ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ ===

    def add_custom_command(self, command: str, function: Callable):
        """
        Добавление пользовательской команды

        Args:
            command (str): Текст команды
            function (Callable): Функция-обработчик
        """
        self.commands[command.lower()] = function
        self.print_debug(f"Добавлена пользовательская команда: {command}")

    def remove_command(self, command: str):
        """
        Удаление команды

        Args:
            command (str): Текст команды для удаления
        """
        if command.lower() in self.commands:
            del self.commands[command.lower()]
            self.print_debug(f"Команда удалена: {command}")
        else:
            self.print_debug(f"Команда для удаления не найдена: {command}")