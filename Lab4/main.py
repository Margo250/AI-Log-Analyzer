"""
Smart Log Analyzer - Лаба 4
Цветной вывод, анимация загрузки, улучшенный интерфейс.
"""

import json
import re
import requests
import sys
import time
import threading

# ANSI-коды для цветов (работает в Windows/Mac/Linux)
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def check_ollama() -> bool:
    """Проверяет, запущен ли сервер Ollama"""
    try:
        r = requests.get("http://localhost:11434", timeout=2)
        return r.status_code == 200
    except:
        return False

def loading_animation(stop_event):
    """Анимация загрузки в отдельном потоке"""
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    i = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r{Colors.CYAN}[{frames[i % len(frames)]}]{Colors.END} Анализирую лог через Ollama...")
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1
    sys.stdout.write("\r" + " " * 50 + "\r")
    sys.stdout.flush()

def extract_json_from_text(text: str) -> dict:
    """Пытается извлечь JSON из текста разными способами."""

    # Способ 1: ищем { ... } в тексте
    json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            pass

    # Способ 2: ищем JSON с вложенными скобками
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
                    return json.loads(text[start:i+1])
                except:
                    continue

    # Способ 3: вытаскиваем поля через регулярки (fallback)
    result = {}

    error_type_match = re.search(r'"error_type"\s*:\s*"([^"]+)"', text)
    if error_type_match:
        result["error_type"] = error_type_match.group(1)

    location_match = re.search(r'"location"\s*:\s*"([^"]+)"', text)
    if location_match:
        result["location"] = location_match.group(1)

    summary_match = re.search(r'"summary"\s*:\s*"([^"]+)"', text)
    if summary_match:
        result["summary"] = summary_match.group(1)

    cause_match = re.search(r'"possible_cause"\s*:\s*"([^"]+)"', text)
    if cause_match:
        result["possible_cause"] = cause_match.group(1)

    if result:
        return result

    raise ValueError("Не удалось извлечь JSON из ответа")


def analyze_log_with_ollama(log_text: str, stop_animation) -> dict:
    """Отправляет лог ошибки в Ollama и возвращает структурированный результат."""

    prompt = f"""Ты — эксперт по анализу ошибок в коде с 10-летним опытом. Проанализируй следующий stack trace.

Твоя задача — объяснить проблему так, чтобы её понял даже джуниор.

Ответ должен быть ТОЛЬКО JSON в точном формате:
{{
    "error_type": "конкретное название исключения",
    "location": "файл:строка:функция (самое важное место)",
    "summary": "коротко, но информативно: что пошло не так (15-20 слов)",
    "possible_cause": "наиболее вероятная причина: кодовая проблема, инфраструктура, нагрузка, данные",
    "recommendation": "что делать: конкретный совет по исправлению (10-15 слов)"
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
                "options": {
                    "temperature": 0.1
                }
            },
            timeout=60
        )

        stop_animation.set()

        if response.status_code != 200:
            return {
                "error_type": f"Ошибка сервера: {response.status_code}",
                "location": "Не определено",
                "summary": response.text[:200],
                "possible_cause": "Проверьте, запущен ли Ollama",
                "recommendation": "Запустите 'ollama serve'"
            }

        result = response.json()
        content = result.get("response", "").strip()
        parsed = extract_json_from_text(content)

        # Добавляем recommendation, если его нет
        expected_fields = ["error_type", "location", "summary", "possible_cause", "recommendation"]
        for field in expected_fields:
            if field not in parsed:
                if field == "recommendation":
                    parsed[field] = "Увеличьте размер пула соединений или добавьте ретраи"
                else:
                    parsed[field] = "Не удалось определить"

        return parsed

    except requests.exceptions.ConnectionError:
        stop_animation.set()
        return {
            "error_type": "Ошибка соединения",
            "location": "Не определено",
            "summary": "Не удалось подключиться к Ollama",
            "possible_cause": "Сервер не запущен",
            "recommendation": "Запустите 'ollama serve' в отдельной консоли"
        }
    except Exception as e:
        stop_animation.set()
        return {
            "error_type": "Ошибка анализа",
            "location": "Не определено",
            "summary": str(e)[:200],
            "possible_cause": "Модель вернула некорректный ответ",
            "recommendation": "Попробуйте ещё раз или перезапустите Ollama"
        }


def print_result(result: dict):
    """Красиво выводит результат анализа в консоль с цветами"""
    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}РЕЗУЛЬТАТ АНАЛИЗА (Ollama){Colors.END}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.END}")

    print(f"{Colors.BOLD}Тип ошибки:{Colors.END}     {Colors.RED}{result.get('error_type', '?')}{Colors.END}")
    print(f"{Colors.BOLD}Локация:{Colors.END}        {Colors.YELLOW}{result.get('location', '?')}{Colors.END}")
    print(f"{Colors.BOLD}Суть:{Colors.END}           {Colors.GREEN}{result.get('summary', '?')}{Colors.END}")
    print(f"{Colors.BOLD}Причина:{Colors.END}        {Colors.CYAN}{result.get('possible_cause', '?')}{Colors.END}")
    print(f"{Colors.BOLD}Рекомендация:{Colors.END}   {Colors.BLUE}{result.get('recommendation', '?')}{Colors.END}")

    print(f"{Colors.BOLD}{'=' * 60}{Colors.END}\n")

def main():
    print(f"\n{Colors.BOLD}{Colors.HEADER}=== Smart Log Analyzer (Ollama - локальная LLM) ==={Colors.END}\n")

    if not check_ollama():
        print(f"{Colors.RED}[ОШИБКА] Ollama не запущен!{Colors.END}")
        print(f"{Colors.YELLOW}Запустите 'ollama serve' в отдельной консоли и попробуйте снова{Colors.END}\n")
        return

    print(f"{Colors.GREEN}[OK] Ollama сервер запущен{Colors.END}\n")

    print(f"{Colors.BOLD}Введите лог ошибки (stack trace):{Colors.END}")
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

    # Анимация загрузки
    stop_animation = threading.Event()
    animation_thread = threading.Thread(target=loading_animation, args=(stop_animation,))
    animation_thread.start()

    # Анализ лога
    result = analyze_log_with_ollama(log_text, stop_animation)

    # Ждём завершения анимации
    animation_thread.join()

    # Вывод результата
    print_result(result)

if __name__ == "__main__":
    main()