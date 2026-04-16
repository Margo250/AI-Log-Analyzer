"""
Smart Log Analyzer - Лаба 3
Реальный вызов Ollama, анализ логов ошибок.
"""

import json
import re
import requests

def check_ollama() -> bool:
    """Проверяет, запущен ли сервер Ollama"""
    try:
        r = requests.get("http://localhost:11434", timeout=2)
        return r.status_code == 200
    except:
        return False

def extract_json_from_text(text: str) -> dict:
    """
    Пытается извлечь JSON из текста разными способами.
    """
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

def analyze_log_with_ollama(log_text: str) -> dict:
    """
    Отправляет лог ошибки в Ollama и возвращает структурированный результат.
    """

    # Улучшенный промпт (жёстко запрещаем лишний текст)
    prompt = f"""Ты — эксперт по анализу ошибок в коде. Проанализируй следующий лог ошибки.

ВАЖНО: Верни ТОЛЬКО JSON. Никаких пояснений, никакого текста до или после JSON.

Ответ должен быть в точности в таком формате:
{{"error_type": "тип ошибки", "location": "файл и строка", "summary": "суть на русском", "possible_cause": "причина"}}

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
                    "temperature": 0.0  # минимальная температура для точности
                }
            },
            timeout=60
        )

        if response.status_code != 200:
            return {
                "error_type": f"Ошибка сервера: {response.status_code}",
                "location": "Не определено",
                "summary": response.text[:200],
                "possible_cause": "Проверьте, запущен ли Ollama"
            }

        result = response.json()
        content = result.get("response", "").strip()

        # Пробуем извлечь JSON разными способами
        parsed = extract_json_from_text(content)

        # Проверяем наличие всех полей
        expected_fields = ["error_type", "location", "summary", "possible_cause"]
        for field in expected_fields:
            if field not in parsed:
                parsed[field] = "Не удалось определить"

        return parsed

    except requests.exceptions.ConnectionError:
        return {
            "error_type": "Ошибка соединения",
            "location": "Не определено",
            "summary": "Не удалось подключиться к Ollama",
            "possible_cause": "Запустите 'ollama serve' в отдельной консоли"
        }
    except Exception as e:
        return {
            "error_type": "Ошибка анализа",
            "location": "Не определено",
            "summary": str(e)[:200],
            "possible_cause": "Модель вернула некорректный ответ"
        }

def print_result(result: dict):
    """Красиво выводит результат анализа в консоль"""
    print("\n" + "=" * 55)
    print("РЕЗУЛЬТАТ АНАЛИЗА (Ollama)")
    print("=" * 55)
    print(f"Тип ошибки:     {result.get('error_type', '?')}")
    print(f"Локация:        {result.get('location', '?')}")
    print(f"Суть:           {result.get('summary', '?')}")
    print(f"Причина:        {result.get('possible_cause', '?')}")
    print("=" * 55)

def main():
    print("\n=== Smart Log Analyzer (Ollama - локальная LLM) ===\n")

    if not check_ollama():
        print("[ОШИБКА] Ollama не запущен!")
        print("Запустите 'ollama serve' в отдельной консоли и попробуйте снова\n")
        return

    print("[OK] Ollama сервер запущен\n")

    print("Введите лог ошибки (stack trace).")
    print("Для завершения ввода нажмите Enter дважды (пустая строка):\n")

    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)

    log_text = "\n".join(lines)

    if not log_text.strip():
        print("\n[ОШИБКА] Лог не может быть пустым")
        return

    print(f"\n[Анализируем...] Отправлено {len(log_text)} символов в Ollama\n")

    result = analyze_log_with_ollama(log_text)
    print_result(result)

if __name__ == "__main__":
    main()