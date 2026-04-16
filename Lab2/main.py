import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DEEPSEEK_API_KEY")


def main():
    print("=== Smart Log Analyzer ===\n")

    if not API_KEY:
        print("WARN: API-ключ не найден в .env")
    else:
        print("OK: API-ключ найден")

    print("\nВведите лог ошибки. Для завершения ввода нажмите Enter дважды (пустая строка):\n")

    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)

    log_text = "\n".join(lines)

    if not log_text.strip():
        print("\nОшибка: лог не может быть пустым")
        return

    print(f"\n[Анализируем...] (получено {len(log_text)} символов)\n")

    # Заглушка
    print("=" * 50)
    print("РЕЗУЛЬТАТ АНАЛИЗА (ЗАГЛУШКА)")
    print("=" * 50)
    print("Тип ошибки:     KeyError")
    print("Локация:        app.py, строка 42, в функции get_user")
    print("Суть:           В словаре data отсутствует ключ 'user_id'")
    print("Причина:        API вернул ответ без поля user_id")
    print("=" * 50)


if __name__ == "__main__":
    main()