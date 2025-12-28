import os
from typing import List, Dict, Optional
from anthropic import Anthropic
from dotenv import load_dotenv
load_dotenv()


class TextAgent:
    """
    Класс для работы с генерацией текста через Anthropic API.
    Поддерживает режим диалога с сохранением контекста.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = "https://api.proxyapi.ru/anthropic", model: str = "claude-sonnet-4-5-20250929"):
        """
        Инициализация агента.

        Args:
            api_key: API ключ. Если не указан, берется из переменной PROXY_API_KEY
            base_url: Базовый URL для API (по умолчанию используется proxyapi.ru)
            model: Модель для использования ("gpt-4.1-mini-2025-04-1" или "claude-sonnet-4-5-20250929")
        """
        self.api_key = api_key or os.getenv("PROXY_API_KEY")
        if not self.api_key:
            raise ValueError("API ключ не найден. Укажите его в конструкторе или переменной PROXY_API_KEY")

        # Проверяем корректность модели
        valid_models = ["gpt-4.1-mini-2025-04-1", "claude-sonnet-4-5-20250929"]
        if model not in valid_models:
            raise ValueError(f"Неверная модель. Доступные модели: {valid_models}")

        # Создаем клиент с указанным base_url
        self.client = Anthropic(
            api_key=self.api_key,
            base_url=base_url
        )
        self.messages: List[Dict[str, any]] = []
        self.model = model

    def add_system_message(self, content: str) -> None:
        """
        Добавить системное сообщение для настройки поведения модели.

        Args:
            content: Текст системного сообщения
        """
        # Системные сообщения в Anthropic API обрабатываются отдельно
        self.system_message = content

    def add_user_message(self, content: str) -> None:
        """
        Добавить сообщение пользователя в историю диалога.

        Args:
            content: Текст сообщения пользователя
        """
        self.messages.append({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": content
                }
            ]
        })

    def generate_response(self, user_message: Optional[str] = None,
                         max_tokens: int = 1000,
                         temperature: float = 0.7) -> str:
        """
        Сгенерировать ответ от модели на основе истории диалога.

        Args:
            user_message: Новое сообщение пользователя (опционально)
            max_tokens: Максимальное количество токенов в ответе
            temperature: Температура генерации (0.0 - 1.0)

        Returns:
            str: Ответ модели
        """
        if user_message:
            self.add_user_message(user_message)

        # Подготавливаем параметры для API
        api_params = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": self.messages
        }

        # Добавляем системное сообщение, если оно есть
        if hasattr(self, 'system_message'):
            api_params["system"] = self.system_message

        try:
            response = self.client.messages.create(**api_params)
            assistant_message = response.content[0].text

            # Добавляем ответ ассистента в историю в новом формате
            self.messages.append({
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": assistant_message
                    }
                ]
            })

            return assistant_message

        except Exception as e:
            raise Exception(f"Ошибка при генерации ответа: {str(e)}")

    def clear_history(self) -> None:
        """
        Очистить историю диалога.
        """
        self.messages = []

    def get_history(self) -> List[Dict[str, any]]:
        """
        Получить текущую историю диалога.

        Returns:
            List[Dict[str, any]]: Список сообщений в формате API Anthropic
        """
        return self.messages.copy()

    def print_history(self, model_name: str = "AI") -> None:
        """
        Вывести историю диалога в читаемом формате.

        Args:
            model_name: Отображаемое имя модели для ассистента
        """
        history = self.get_history()

        if not history:
            print("История диалога пуста.")
            return

        print("\nИстория диалога:")
        print("=" * 50)

        for i, message in enumerate(history, 1):
            role = message["role"]
            content = message["content"]

            if role == "user":
                print(f"Пользователь #{i//2 + 1}:")
                if isinstance(content, list) and content:
                    print(f"   {content[0]['text']}")
                else:
                    print(f"   {content}")

            elif role == "assistant":
                print(f"{model_name} #{i//2}:")
                if isinstance(content, list) and content:
                    print(f"   {content[0]['text']}")
                else:
                    print(f"   {content}")

            print("-" * 30)

        print(f"Всего сообщений: {len(history)}")

    def start_chat(self, system_prompt: Optional[str] = None) -> None:
        """
        Начать новый чат с опциональным системным промптом.

        Args:
            system_prompt: Системный промпт для настройки поведения модели
        """
        self.clear_history()
        if system_prompt:
            self.add_system_message(system_prompt)


def select_model():
    """
    Предлагает пользователю выбрать модель для диалога.

    Returns:
        str: Выбранная модель
    """
    print("🤖 Выберите модель для диалога:")
    print("1. Обычная модель (gpt-4.1-mini-2025-04-1) - быстрые ответы")
    print("2. Думающая модель (claude-sonnet-4-5-20250929) - более качественные ответы")
    print()

    while True:
        choice = input("Введите номер модели (1 или 2): ").strip()

        if choice == "1":
            return "gpt-4.1-mini-2025-04-1"
        elif choice == "2":
            return "claude-sonnet-4-5-20250929"
        else:
            print("❌ Пожалуйста, введите 1 или 2.")

def get_model_display_name(model: str) -> str:
    """
    Возвращает отображаемое имя модели для интерфейса.

    Args:
        model: Техническое имя модели

    Returns:
        str: Отображаемое имя модели
    """
    if model == "gpt-4.1-mini-2025-04-1":
        return "GPT-4.1 Mini"
    elif model == "claude-sonnet-4-5-20250929":
        return "Claude Sonnet 4.5"
    else:
        return model

def chat_example():
    """
    Пример использования TextAgent для диалога.
    """
    # Выбираем модель
    selected_model = select_model()
    model_name = get_model_display_name(selected_model)

    # Создаем агента с выбранной моделью
    agent = TextAgent(model=selected_model)

    # Начинаем чат с системным промптом
    agent.start_chat("Ты - полезный AI-ассистент, который отвечает на русском языке.")

    print(f"🤖 Начат диалог с {model_name}. Для выхода введите 'exit', 'quit' или 'выход'.")
    print("=" * 50)

    while True:
        user_input = input("👤 Вы: ").strip()

        if user_input.lower() in ['exit', 'quit', 'выход']:
            print("🤖 Диалог завершен.")

            # Предлагаем показать историю
            show_history = input("Показать историю диалога? (y/n): ").strip().lower()
            if show_history in ['y', 'yes', 'да', 'д']:
                agent.print_history(model_name)

            break

        if user_input.lower() in ['history', 'история', 'h']:
            agent.print_history(model_name)
            continue

        if not user_input:
            continue

        try:
            response = agent.generate_response(user_input)
            print(f"🤖 {model_name}: {response}")
            print("-" * 50)

        except Exception as e:
            print(f"❌ Ошибка: {e}")
            break


if __name__ == "__main__":
    # Запуск примера диалога
    chat_example()
