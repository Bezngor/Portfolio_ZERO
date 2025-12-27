#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проверки подключения к Telegram API
"""

import os
import sys
from dotenv import load_dotenv
import requests

print("=" * 60)
print("🔍 Проверка подключения к Telegram API")
print("=" * 60)

# Load environment
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TELEGRAM_TOKEN:
    print("❌ TELEGRAM_TOKEN не найден в .env файле")
    sys.exit(1)

print(f"✅ Токен найден: {TELEGRAM_TOKEN[:20]}...")

# Test connection
print("\n1️⃣ Проверка доступности api.telegram.org...")
try:
    response = requests.get("https://api.telegram.org", timeout=10)
    print(f"✅ api.telegram.org доступен (статус: {response.status_code})")
except requests.exceptions.Timeout:
    print("❌ Таймаут подключения к api.telegram.org")
    print("💡 Telegram API может быть заблокирован в вашем регионе")
    print("   Попробуйте включить VPN")
    sys.exit(1)
except requests.exceptions.ConnectionError as e:
    print(f"❌ Ошибка подключения: {e}")
    print("💡 Проверьте интернет-соединение")
    sys.exit(1)

# Test bot token
print("\n2️⃣ Проверка токена бота...")
try:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe"
    response = requests.get(url, timeout=10)
    data = response.json()
    
    if data.get('ok'):
        bot_info = data.get('result', {})
        print(f"✅ Токен валиден!")
        print(f"   ID бота: {bot_info.get('id')}")
        print(f"   Имя: {bot_info.get('first_name')}")
        print(f"   Username: @{bot_info.get('username')}")
        print(f"   Может читать группы: {bot_info.get('can_read_all_group_messages', False)}")
    else:
        print(f"❌ Ошибка: {data.get('description')}")
        print("💡 Проверьте правильность токена в .env файле")
        sys.exit(1)
except requests.exceptions.Timeout:
    print("❌ Таймаут при проверке токена")
    print("💡 Включите VPN и попробуйте снова")
    sys.exit(1)
except Exception as e:
    print(f"❌ Ошибка: {e}")
    sys.exit(1)

# Check webhook
print("\n3️⃣ Проверка webhook...")
try:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getWebhookInfo"
    response = requests.get(url, timeout=10)
    data = response.json()
    
    if data.get('ok'):
        webhook_info = data.get('result', {})
        webhook_url = webhook_info.get('url', '')
        
        if webhook_url:
            print(f"⚠️  Активен webhook: {webhook_url}")
            print(f"   Последняя ошибка: {webhook_info.get('last_error_message', 'Нет')}")
            print(f"💡 Для работы через polling нужно удалить webhook")
            print(f"   Это сделает бот автоматически при запуске")
        else:
            print("✅ Webhook не установлен (это хорошо для polling)")
    else:
        print(f"⚠️  Не удалось проверить webhook: {data.get('description')}")
except Exception as e:
    print(f"⚠️  Ошибка при проверке webhook: {e}")

print("\n" + "=" * 60)
print("✅ Все проверки пройдены!")
print("🚀 Можете запускать бота: python travel_wallet_bot.py")
print("=" * 60)

