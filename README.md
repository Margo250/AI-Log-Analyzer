# Smart Log Analyzer

Проект по разработке ИИ-системы для автоматического анализа и сокращения логов ошибок (stack trace) с помощью локальной LLM (Ollama).

---

## Тема проекта

Разработка консольного приложения на Python, которое принимает на вход текстовый лог ошибки, анализирует его через локальную модель Ollama (llama3.2:3b) и выдаёт структурированный результат: тип ошибки, локацию, суть, возможные причины, рекомендации по исправлению и подсказку по коду.

---

## Скриншот работы
<img width="1987" height="1328" alt="image" src="https://github.com/user-attachments/assets/88e084e2-421b-493b-924a-899bc59b176b" />

---

## Установка и запуск

### 1. Установка Ollama

Скачайте установщик с официального сайта: https://ollama.com/download

**Для Windows:**
- Запустите `OllamaSetup.exe`
- После установки Ollama автоматически запустится в фоне

### 2. Скачивание модели

Откройте командную строку (CMD) и выполните:

```bash
ollama pull llama3.2:3b
```

Модель весит ~2 ГБ, загрузка займёт несколько минут.

### 3. Запуск сервера Ollama

В отдельной консоли выполните:

```bash
ollama serve
```

Оставьте эту консоль открытой. Сервер будет работать на http://localhost:11434

### 4. Клонирование репозитория

```bash
git clone https://github.com/ваш-username/smart-log-analyzer.git
cd smart-log-analyzer
```

### 5. Установка зависимостей Python

```bash
pip install requests
```

### 6. Запуск программы

```bash
python main.py
```

---

## Использование

### Интерактивный режим

```bash
python main.py
```

Введите лог ошибки (можно несколько строк). Для завершения ввода нажмите Enter дважды.

### Чтение из файла

```bash
python main.py --file error.log
# или сокращённо
python main.py -f error.log
```

### Прямая передача лога

```bash
python main.py --log "KeyError: 'user_id' at app.py line 42"
# или сокращённо
python main.py -l "KeyError: 'user_id'"
```

### Справка

```bash
python main.py --help
```

---

## Структура проекта

smart-log-analyzer/

├── main.py              # Основной скрипт

├── requirements.txt     # Зависимости

└── .gitignore

---

## Стек технологий

- Python 3.9+
- Ollama (локальный сервер LLM)
- Модель: llama3.2:3b
- Библиотека: requests

---

## Участники

- Езерская Оксана Геннадьевна
- Кравченко Маргарита Александровна
