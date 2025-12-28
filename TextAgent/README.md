# TextAgent - Генерация текста с Claude

Проект для работы с генерацией текста через Anthropic API с использованием модели Claude Sonnet 4.5 и прокси API.

## Установка

1. Активируйте виртуальное окружение:
```bash
venv\Scripts\activate  # Windows
# или
source venv/bin/activate  # Linux/Mac
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Настройте API ключ (см. файл ENV_SETUP.txt):
   - Создайте файл `.env` в корне проекта
   - Добавьте `ANTHROPIC_API_KEY=your-api-key-here`
   - Или установите переменную окружения

4. По умолчанию используется прокси API (proxyapi.ru) с моделью Claude Sonnet 4.5

## Использование

### Простой пример

```python
from text_agent import TextAgent

# Создаем агента с выбором модели
agent = TextAgent(model="claude-sonnet-4-5-20250929")  # или "claude-3-5-haiku-20241022"

# Начинаем чат с системным промптом
agent.start_chat("Ты - полезный AI-ассистент.")

# Генерируем ответы
response1 = agent.generate_response("Привет! Расскажи о Python.")
print(response1)

response2 = agent.generate_response("А какие у него преимущества?")
print(response2)

# Вывести историю диалога
agent.print_history("Claude Sonnet 4.5")
```

### Интерактивный чат

```python
from text_agent import chat_example

# Запускаем интерактивный диалог (с выбором модели)
chat_example()
```

Или запустите файл напрямую:
```bash
python text_agent.py
```

**Выбор модели:**
- Обычная модель (claude-3-5-haiku-20241022) - быстрые ответы
- Думающая модель (claude-sonnet-4-5-20250929) - более качественные ответы

**Команды в чате:**
- `exit`, `quit`, `выход` - завершить диалог
- `history`, `история`, `h` - показать историю диалога во время чата
- После завершения чата будет предложено показать историю

## API Reference

### Класс TextAgent

#### Методы:

- `__init__(api_key=None, base_url="https://api.proxyapi.ru/anthropic", model="claude-sonnet-4-5-20250929")` - Инициализация агента
- `add_system_message(content)` - Добавить системное сообщение
- `add_user_message(content)` - Добавить сообщение пользователя
- `generate_response(user_message=None, max_tokens=1000, temperature=0.7)` - Сгенерировать ответ
- `clear_history()` - Очистить историю диалога
- `get_history()` - Получить историю диалога
- `print_history(model_name="AI")` - Вывести историю диалога в читаемом формате
- `start_chat(system_prompt=None)` - Начать новый чат

## Особенности

- Поддержка режима диалога с сохранением контекста
- Выбор между двумя моделями: Claude 3.5 Haiku (быстрая) и Claude Sonnet 4.5 (качественная)
- Использование прокси API (proxyapi.ru) для обеих моделей
- Настраиваемая температура генерации
- Обработка ошибок API
- Простой интерфейс для интерактивного общения
- Современный формат API сообщений
- Встроенная функция просмотра истории диалога
