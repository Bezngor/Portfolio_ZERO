#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы TextAgent.
Проверяет инициализацию и базовую функциональность без реального API вызова.
"""

import os
from text_agent import TextAgent
from dotenv import load_dotenv
load_dotenv()

PROXY_API_KEY = os.getenv("PROXY_API_KEY")


def test_initialization():
    """Тест инициализации агента"""
    print("Тест 1: Инициализация без API ключа...")

    try:
        # Временно сохраняем значение PROXY_API_KEY
        original_key = os.environ.get("PROXY_API_KEY")
        # Удаляем переменную окружения для теста
        if "PROXY_API_KEY" in os.environ:
            del os.environ["PROXY_API_KEY"]

        # Это должно вызвать ошибку, так как API ключ не установлен
        agent = TextAgent()
        print("Ошибка: Агент инициализировался без API ключа!")
        return False
    except ValueError as e:
        print(f"Корректно: {e}")
        return True
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return False
    finally:
        # Восстанавливаем переменную окружения
        if original_key:
            os.environ["PROXY_API_KEY"] = original_key

def test_initialization_with_key( proxy_api_key: str = PROXY_API_KEY ):
    """Тест инициализации агента с API ключом"""
    print("\nТест 2: Инициализация с API ключом...")

    try:
        # Создаем агента с тестовым ключом
        agent = TextAgent(api_key=proxy_api_key)
        print("Агент успешно инициализирован с тестовым ключом")
        return True
    except Exception as e:
        print(f"Ошибка при инициализации: {e}")
        return False

def test_chat_functionality( proxy_api_key: str = PROXY_API_KEY ):
    """Тест базовой функциональности чата"""
    print("\nТест 3: Базовая функциональность чата...")

    try:
        agent = TextAgent(api_key=proxy_api_key)

        # Тест добавления системного сообщения
        agent.add_system_message("Ты - тестовый ассистент.")
        print("Системное сообщение добавлено")

        # Тест добавления пользовательского сообщения
        agent.add_user_message("Привет!")
        print("Пользовательское сообщение добавлено")

        # Тест получения истории
        history = agent.get_history()
        if (len(history) == 1 and
            history[0]["role"] == "user" and
            isinstance(history[0]["content"], list) and
            len(history[0]["content"]) == 1 and
            history[0]["content"][0]["type"] == "text" and
            history[0]["content"][0]["text"] == "Привет!"):
            print("История сообщений корректна")
        else:
            print("Ошибка в истории сообщений")
            print(f"Полученная история: {history}")
            return False

        # Тест очистки истории
        agent.clear_history()
        if len(agent.get_history()) == 0:
            print("История очищена")
        else:
            print("Ошибка при очистке истории")
            return False

        return True

    except Exception as e:
        print(f"Ошибка в функциональности чата: {e}")
        return False

def test_print_history(proxy_api_key: str = PROXY_API_KEY):
    """Тест метода print_history"""
    print("\nТест 4: Вывод истории диалога...")

    try:
        agent = TextAgent(api_key=proxy_api_key)

        # Добавим несколько сообщений
        agent.add_user_message("Привет!")
        agent.add_user_message("Как дела?")

        # Проверим, что метод print_history существует и может быть вызван
        if hasattr(agent, 'print_history') and callable(agent.print_history):
            # Попробуем вызвать метод (он выведет информацию в консоль)
            agent.print_history()
            print("Метод print_history успешно выполнен")
            return True
        else:
            print("Метод print_history не найден")
            return False

    except Exception as e:
        print(f"Ошибка в тесте print_history: {e}")
        return False

def main():
    """Запуск всех тестов"""
    print("Запуск тестов TextAgent")
    print("=" * 50)

    tests = [
        test_initialization,
        test_initialization_with_key,
        test_chat_functionality,
        test_print_history
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 50)
    print(f"Результаты: {passed}/{total} тестов пройдено")

    if passed == total:
        print("Все тесты пройдены! Код готов к работе.")
        print("\nДля реального использования:")
        print("   1. Получите API ключ для proxyapi.ru")
        print("   2. Создайте .env файл с PROXY_API_KEY=your-key")
        print("   3. Запустите python text_agent.py")
        print("\nКоманды в чате:")
        print("   - exit/quit/выход - завершить диалог")
        print("   - history/история/h - показать историю")
    else:
        print("Некоторые тесты не пройдены. Проверьте код.")

if __name__ == "__main__":
    main()
