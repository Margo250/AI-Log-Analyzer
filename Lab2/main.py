"""
Smart Log Analyzer - Лаба 2
Заглушка. Реальный вызов Ollama будет в лабе 3.
"""

import requests


def check_ollama() -> bool:
    """Проверяет, запущен ли сервер Ollama"""
    try:
        r = requests.get("http://localhost:11434", timeout=2)
        return r.status_code == 200
    except:
        return False


def analyze_log_stub(log_text: str) -> dict:
    """Заглушка. Возвращает тестовый результат."""
    return {
        "error_type": "ConnectionError",
        "location": "main.py, строка 24",
        "summary": "Не удалось подключиться к серверу",
        "possible_cause": "Проблема с сетью или DNS"
    }


def main():
    print("\n=== Smart Log Analyzer (Лаба 2 - заглушка) ===\n")

    # Проверка Ollama (просто информация)
    if check_ollama():
        print("[OK] Ollama сервер запущен")
    else:
        print("[INFO] Ollama не обнаружен. Для лабы 3 запустите 'ollama serve'")

    print("\nВведите лог ошибки. Пустая строка - завершить ввод:\n")

    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)

    log_text = "\n".join(lines)

    if not log_text.strip():
        print("Ошибка: лог не может быть пустым")
        return

    print(f"\n[Анализ] Получено {len(log_text)} символов\n")

    result = analyze_log_stub(log_text)

    print("=" * 50)
    print("РЕЗУЛЬТАТ (ЗАГЛУШКА)")
    print("=" * 50)
    print(f"Тип ошибки:  {result['error_type']}")
    print(f"Локация:     {result['location']}")
    print(f"Суть:        {result['summary']}")
    print(f"Причина:     {result['possible_cause']}")
    print("=" * 50)


if __name__ == "__main__":
    main()
