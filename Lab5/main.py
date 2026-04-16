"""
Smart Log Analyzer - Лаба 5
Аргументы командной строки, чтение из файла, расширенный вывод, рекомендации.
"""

import json
import re
import requests
import sys
import time
import threading
import argparse

# ANSI-коды для цветов
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def check_ollama() -> bool:
    """Проверяет, запущен ли сервер Ollama"""
    try:
        r = requests.get("http://localhost:11434", timeout=2)
        return r.status_code == 200
    except:
        return False

def loading_animation(stop_event):
    """Анимация загрузки"""
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    i = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r{Colors.CYAN}[{frames[i % len(frames)]}]{Colors.END} Анализирую лог через Ollama...")
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1
    sys.stdout.write("\r" + " " * 60 + "\r")
    sys.stdout.flush()


def extract_json_from_text(text: str) -> dict:
    """Пытается извлечь JSON из текста"""
    # Ищем JSON с вложенными скобками
    brace_count = 0
    start = -1
    for i, char in enumerate(text):
        if char == '{':
            if brace_count == 0:
                start = i
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0 and start != -1:
                try:
                    return json.loads(text[start:i + 1])
                except:
                    continue

    # Fallback: вытаскиваем поля через регулярки (обновлённые названия)
    result = {}
    patterns = {
        "error_type": r'"error_type"\s*:\s*"([^"]+)"',
        "root_cause_location": r'"root_cause_location"\s*:\s*"([^"]+)"',
        "final_location": r'"final_location"\s*:\s*"([^"]+)"',
        "short_summary": r'"short_summary"\s*:\s*"([^"]+)"',
        "detailed_explanation": r'"detailed_explanation"\s*:\s*"([^"]+)"',
        "possible_causes": r'"possible_causes"\s*:\s*"([^"]+)"',
        "recommendation": r'"recommendation"\s*:\s*"([^"]+)"',
        "code_hint": r'"code_hint"\s*:\s*"([^"]+)"'
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            result[key] = match.group(1)

    if result:
        return result

    raise ValueError("Не удалось извлечь JSON из ответа")


def analyze_log_with_ollama(log_text: str, stop_animation) -> dict:
    """Отправляет лог ошибки в Ollama и возвращает расширенный анализ."""

    prompt = f"""Ты — эксперт по анализу ошибок в коде. Проанализируй следующий stack trace.

Обрати особое внимание на:
1. Первое исключение (первопричина)
2. Цепочку исключений (during handling... another exception occurred)
3. Финальное исключение

Верни ТОЛЬКО JSON. Никакого текста до или после.

Формат ответа:
{{
    "error_type": "тип ошибки (первопричина → финальное исключение)",
    "root_cause_location": "файл:строка:функция, где возникла ПЕРВАЯ ошибка",
    "final_location": "файл:строка:функция, где упало всё",
    "short_summary": "одно предложение о сути проблемы",
    "detailed_explanation": "развёрнутое объяснение: что пошло не так, почему это привело к цепочке ошибок",
    "possible_causes": "список из 2-3 возможных причин через запятую",
    "recommendation": "конкретные шаги по исправлению (2-3 действия)",
    "code_hint": "пример кода или команды для исправления"
}}

Лог:
{log_text}
"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2:3b",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1}
            },
            timeout=60
        )

        stop_animation.set()

        if response.status_code != 200:
            return {
                "error_type": f"Ошибка сервера: {response.status_code}",
                "root_cause_location": "Не определено",
                "final_location": "Не определено",
                "short_summary": response.text[:100],
                "detailed_explanation": "Сервер Ollama вернул ошибку",
                "possible_causes": "Ollama не запущен или модель не загружена",
                "recommendation": "Запустите 'ollama serve' и проверьте модель",
                "code_hint": "ollama pull llama3.2:3b"
            }

        result = response.json()
        content = result.get("response", "").strip()
        parsed = extract_json_from_text(content)

        # Заполняем недостающие поля
        default_fields = {
            "error_type": "Неизвестная ошибка",
            "root_cause_location": "Не определено",
            "final_location": "Не определено",
            "short_summary": "Не удалось проанализировать",
            "detailed_explanation": "Модель не смогла разобрать лог",
            "possible_causes": "Недостаточно данных",
            "recommendation": "Проверьте лог вручную",
            "code_hint": "-"
        }

        for field, default in default_fields.items():
            if field not in parsed:
                parsed[field] = default

        return parsed

    except requests.exceptions.ConnectionError:
        stop_animation.set()
        return {
            "error_type": "Ошибка соединения",
            "root_cause_location": "Не определено",
            "final_location": "Не определено",
            "short_summary": "Не удалось подключиться к Ollama",
            "detailed_explanation": "Сервер Ollama не запущен или недоступен",
            "possible_causes": "Ollama не установлен, не запущен, или порт 11434 занят",
            "recommendation": "Запустите 'ollama serve' в отдельной консоли",
            "code_hint": "ollama serve"
        }
    except Exception as e:
        stop_animation.set()
        return {
            "error_type": "Ошибка анализа",
            "root_cause_location": "Не определено",
            "final_location": "Не определено",
            "short_summary": str(e)[:100],
            "detailed_explanation": "Произошла ошибка при обработке ответа от модели",
            "possible_causes": "Проблема с парсингом JSON",
            "recommendation": "Попробуйте ещё раз",
            "code_hint": "-"
        }


def print_result(result: dict):
    """Выводит расширенный результат анализа в консоль"""
    print(f"\n{Colors.BOLD}{'=' * 75}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}РЕЗУЛЬТАТ АНАЛИЗА (Ollama){Colors.END}")
    print(f"{Colors.BOLD}{'=' * 75}{Colors.END}\n")

    print(f"{Colors.BOLD}📍 Тип ошибки:{Colors.END}")
    print(f"   {Colors.RED}{result.get('error_type', '?')}{Colors.END}\n")

    print(f"{Colors.BOLD}🎯 Корень проблемы (первая ошибка):{Colors.END}")
    print(f"   {Colors.YELLOW}{result.get('root_cause_location', '?')}{Colors.END}\n")

    print(f"{Colors.BOLD}💥 Финальное падение:{Colors.END}")
    print(f"   {Colors.YELLOW}{result.get('final_location', '?')}{Colors.END}\n")

    print(f"{Colors.BOLD}📝 Кратко:{Colors.END}")
    print(f"   {Colors.GREEN}{result.get('short_summary', '?')}{Colors.END}\n")

    print(f"{Colors.BOLD}🔍 Подробно:{Colors.END}")
    print(f"   {Colors.CYAN}{result.get('detailed_explanation', '?')}{Colors.END}\n")

    print(f"{Colors.BOLD}💡 Возможные причины:{Colors.END}")
    print(f"   {Colors.YELLOW}{result.get('possible_causes', '?')}{Colors.END}\n")

    print(f"{Colors.BOLD}🛠️ Рекомендации:{Colors.END}")
    print(f"   {Colors.GREEN}{result.get('recommendation', '?')}{Colors.END}\n")

    if result.get('code_hint') and result.get('code_hint') != '-':
        print(f"{Colors.BOLD}💻 Подсказка по коду:{Colors.END}")
        print(f"   {Colors.BLUE}{result.get('code_hint', '?')}{Colors.END}\n")

    print(f"{Colors.BOLD}{'=' * 75}{Colors.END}\n")

def read_log_from_file(filepath: str) -> str:
    """Читает лог из файла"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"{Colors.RED}[ОШИБКА] Файл не найден: {filepath}{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}[ОШИБКА] Не удалось прочитать файл: {e}{Colors.END}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description=f"{Colors.CYAN}Smart Log Analyzer - анализ логов ошибок через локальную LLM (Ollama){Colors.END}",
        epilog=f"""{Colors.YELLOW}Примеры:{Colors.END}
  python main.py --file error.log
  python main.py --log "KeyError: 'user_id' at app.py line 42"
  python main.py
  python main.py --help""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("--file", "-f", type=str, help="Путь к файлу с логом ошибки")
    input_group.add_argument("--log", "-l", type=str, help="Лог ошибки в виде строки")

    args = parser.parse_args()

    print(f"\n{Colors.BOLD}{Colors.HEADER}╔═══════════════════════════════════════════════════════════════════════════╗{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}║                 Smart Log Analyzer (Ollama - локальная LLM)               ║{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}╚═══════════════════════════════════════════════════════════════════════════╝{Colors.END}\n")

    # Проверка Ollama
    if not check_ollama():
        print(f"{Colors.RED}[ОШИБКА] Ollama не запущен!{Colors.END}")
        print(f"{Colors.YELLOW}Запустите 'ollama serve' в отдельной консоли и попробуйте снова{Colors.END}\n")
        print(f"{Colors.CYAN}Если Ollama не установлен:{Colors.END}")
        print(f"  1. Скачайте с https://ollama.com/download")
        print(f"  2. Установите")
        print(f"  3. Выполните: ollama pull llama3.2:3b")
        print(f"  4. Запустите: ollama serve\n")
        return

    print(f"{Colors.GREEN}[OK] Ollama сервер запущен{Colors.END}\n")

    # Получение лога
    if args.file:
        print(f"{Colors.CYAN}[INFO] Чтение из файла: {args.file}{Colors.END}\n")
        log_text = read_log_from_file(args.file)
    elif args.log:
        print(f"{Colors.CYAN}[INFO] Анализ переданной строки{Colors.END}\n")
        log_text = args.log
    else:
        print(f"{Colors.BOLD}📄 Введите лог ошибки (stack trace):{Colors.END}")
        print(f"{Colors.CYAN}Для завершения ввода нажмите Enter дважды (пустая строка){Colors.END}\n")
        lines = []
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
        log_text = "\n".join(lines)

    if not log_text.strip():
        print(f"\n{Colors.RED}[ОШИБКА] Лог не может быть пустым{Colors.END}")
        return

    print(f"\n{Colors.CYAN}[INFO] Размер лога: {len(log_text)} символов{Colors.END}")

    # Анимация загрузки
    stop_animation = threading.Event()
    animation_thread = threading.Thread(target=loading_animation, args=(stop_animation,))
    animation_thread.start()

    # Анализ
    result = analyze_log_with_ollama(log_text, stop_animation)
    animation_thread.join()

    # Вывод
    print_result(result)

if __name__ == "__main__":
    main()