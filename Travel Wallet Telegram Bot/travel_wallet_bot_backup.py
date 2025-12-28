#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Travel Wallet Bot
A mini-wallet for travelers with real-time currency conversion
"""

import telebot
from telebot import types
import os
from dotenv import load_dotenv
from database import Database
from current_api import convert_currency, get_all_supported_currencies
from currency_detector import detect_currency_with_api, find_currency_by_country
import re
from datetime import datetime
import logging
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress TeleBot verbose logging for cleaner output
telebot_logger = logging.getLogger('TeleBot')
telebot_logger.setLevel(logging.WARNING)

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CURRENCY_ACCESS_KEY = os.getenv("CURRENCY_ACCESS_KEY")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN not found in environment variables")
if not CURRENCY_ACCESS_KEY:
    raise ValueError("CURRENCY_ACCESS_KEY not found in environment variables")

# Initialize bot and database
bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=True)
db = Database()

# Flag for graceful shutdown
is_running = True

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global is_running
    is_running = False
    logger.info("Получен сигнал завершения")
    print("\n⏳ Останавливаю бота...")
    bot.stop_polling()
    print("👋 Бот успешно остановлен!")
    sys.exit(0)

# Country to currency mapping (most common countries)
COUNTRY_CURRENCY_MAP = {
    "Россия": "RUB", "Russia": "RUB",
    "США": "USD", "USA": "USD", "Америка": "USD", "America": "USD",
    "Великобритания": "GBP", "UK": "GBP", "Англия": "GBP", "England": "GBP",
    "Европа": "EUR", "Europe": "EUR", "ЕС": "EUR", "EU": "EUR",
    "Германия": "EUR", "Germany": "EUR",
    "Франция": "EUR", "France": "EUR",
    "Италия": "EUR", "Italy": "EUR",
    "Испания": "EUR", "Spain": "EUR",
    "Китай": "CNY", "China": "CNY",
    "Япония": "JPY", "Japan": "JPY",
    "Южная Корея": "KRW", "South Korea": "KRW", "Корея": "KRW", "Korea": "KRW",
    "Таиланд": "THB", "Thailand": "THB",
    "Вьетнам": "VND", "Vietnam": "VND",
    "Турция": "TRY", "Turkey": "TRY",
    "ОАЭ": "AED", "UAE": "AED", "Дубай": "AED", "Dubai": "AED",
    "Индия": "INR", "India": "INR",
    "Бразилия": "BRL", "Brazil": "BRL",
    "Канада": "CAD", "Canada": "CAD",
    "Австралия": "AUD", "Australia": "AUD",
    "Швейцария": "CHF", "Switzerland": "CHF",
    "Мексика": "MXN", "Mexico": "MXN",
    "Сингапур": "SGD", "Singapore": "SGD",
    "Индонезия": "IDR", "Indonesia": "IDR",
    "Польша": "PLN", "Poland": "PLN",
    "Чехия": "CZK", "Czech Republic": "CZK", "Прага": "CZK", "Prague": "CZK",
    "Швеция": "SEK", "Sweden": "SEK",
    "Норвегия": "NOK", "Norway": "NOK",
    "Дания": "DKK", "Denmark": "DKK",
}

# States for conversation flow
STATE_WAITING_FROM_COUNTRY = "waiting_from_country"
STATE_WAITING_TO_COUNTRY = "waiting_to_country"
STATE_WAITING_INITIAL_AMOUNT = "waiting_initial_amount"
STATE_WAITING_RATE_CONFIRMATION = "waiting_rate_confirmation"
STATE_WAITING_CUSTOM_RATE = "waiting_custom_rate"
STATE_WAITING_NEW_RATE = "waiting_new_rate"
STATE_WAITING_CATEGORY = "waiting_category"


# Utility functions
def get_currency_from_country(country_name: str) -> str:
    """Get currency code from country name with caching"""
    # First check cache in database
    cached = db.get_cached_currency(country_name.strip())
    if cached:
        return cached
    
    # Try to detect currency
    currency = detect_currency_with_api(country_name)
    
    # Cache if found
    if currency:
        db.cache_currency(country_name.strip(), currency)
    
    return currency


def format_amount(amount: float) -> str:
    """Format amount with thousand separators"""
    return f"{amount:,.2f}".replace(",", " ")


def get_main_menu_keyboard():
    """Create main menu inline keyboard"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("🆕 Создать путешествие", callback_data="menu_new_trip"),
        types.InlineKeyboardButton("🗺 Активные поездки", callback_data="menu_active_trips")
    )
    keyboard.add(
        types.InlineKeyboardButton("📦 Архив поездок", callback_data="menu_closed_trips"),
        types.InlineKeyboardButton("💰 Баланс", callback_data="menu_balance")
    )
    keyboard.add(
        types.InlineKeyboardButton("📊 История расходов", callback_data="menu_history"),
        types.InlineKeyboardButton("💱 Изменить курс", callback_data="menu_change_rate")
    )
    return keyboard


def get_back_to_menu_keyboard():
    """Create back to menu button"""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🔙 Главное меню", callback_data="menu_main"))
    return keyboard


def get_trip_management_keyboard(trip_id: int, is_active: bool = True):
    """Create keyboard for trip management"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    if is_active:
        keyboard.add(
            types.InlineKeyboardButton("📦 Закрыть поездку", callback_data=f"close_trip_{trip_id}")
        )
    else:
        keyboard.add(
            types.InlineKeyboardButton("🔄 Возобновить поездку", callback_data=f"reopen_trip_{trip_id}")
        )
    keyboard.add(
        types.InlineKeyboardButton("🔙 Назад", callback_data="menu_active_trips" if is_active else "menu_closed_trips")
    )
    return keyboard


# Command handlers
@bot.message_handler(commands=['start'])
def start_command(message):
    """Handle /start command"""
    user = message.from_user
    db.add_user(user.id, user.username, user.first_name, user.last_name)
    
    welcome_text = (
        f"👋 Привет, {user.first_name}!\n\n"
        "Я — твой личный кошелёк для путешествий! 💼✈️\n\n"
        "Я помогу тебе:\n"
        "• Отслеживать расходы в разных валютах\n"
        "• Конвертировать суммы по актуальным курсам\n"
        "• Управлять бюджетом нескольких поездок\n\n"
        "Выбери действие из меню ниже:"
    )
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_menu_keyboard())


@bot.message_handler(commands=['menu'])
def menu_command(message):
    """Handle /menu command"""
    bot.send_message(
        message.chat.id,
        "📱 Главное меню:",
        reply_markup=get_main_menu_keyboard()
    )


@bot.message_handler(commands=['newtrip'])
def newtrip_command(message):
    """Handle /newtrip command"""
    start_new_trip(message.chat.id, message.from_user.id)


@bot.message_handler(commands=['switch'])
def switch_command(message):
    """Handle /switch command"""
    show_my_trips(message.chat.id, message.from_user.id)


@bot.message_handler(commands=['balance'])
def balance_command(message):
    """Handle /balance command"""
    show_balance(message.chat.id, message.from_user.id)


@bot.message_handler(commands=['history'])
def history_command(message):
    """Handle /history command"""
    show_history(message.chat.id, message.from_user.id)


@bot.message_handler(commands=['setrate'])
def setrate_command(message):
    """Handle /setrate command"""
    start_rate_change(message.chat.id, message.from_user.id)


# Callback query handler
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    """Handle all callback queries"""
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    try:
        # Main menu callbacks
        if call.data == "menu_main":
            bot.edit_message_text(
                "📱 Главное меню:",
                chat_id,
                call.message.message_id,
                reply_markup=get_main_menu_keyboard()
            )
        
        elif call.data == "menu_new_trip":
            bot.edit_message_text(
                "🆕 Создание нового путешествия...",
                chat_id,
                call.message.message_id
            )
            start_new_trip(chat_id, user_id)
        
        elif call.data == "menu_my_trips":
            bot.delete_message(chat_id, call.message.message_id)
            show_my_trips(chat_id, user_id)
        
        elif call.data == "menu_balance":
            bot.delete_message(chat_id, call.message.message_id)
            show_balance(chat_id, user_id)
        
        elif call.data == "menu_history":
            bot.delete_message(chat_id, call.message.message_id)
            show_history(chat_id, user_id)
        
        elif call.data == "menu_change_rate":
            bot.delete_message(chat_id, call.message.message_id)
            start_rate_change(chat_id, user_id)
        
        # Rate confirmation callbacks
        elif call.data.startswith("rate_accept_"):
            trip_id = int(call.data.split("_")[2])
            handle_rate_acceptance(chat_id, user_id, call.message.message_id, trip_id)
        
        elif call.data.startswith("rate_custom_"):
            trip_id = int(call.data.split("_")[2])
            handle_rate_custom(chat_id, user_id, call.message.message_id, trip_id)
        
        # Expense confirmation callbacks
        elif call.data.startswith("expense_yes_"):
            expense_data = call.data.split("_")
            amount = float(expense_data[2])
            handle_expense_confirmation(chat_id, user_id, call.message.message_id, amount, True)
        
        elif call.data.startswith("expense_no_"):
            handle_expense_confirmation(chat_id, user_id, call.message.message_id, 0, False)
        
        # Trip selection callbacks
        elif call.data.startswith("select_trip_"):
            trip_id = int(call.data.split("_")[2])
            handle_trip_selection(chat_id, user_id, call.message.message_id, trip_id)
        
        # Try to answer the callback query, but ignore if it's too old
        try:
            bot.answer_callback_query(call.id)
        except telebot.apihelper.ApiTelegramException as e:
            # Ignore "query is too old" errors
            if "query is too old" in str(e).lower() or "query ID is invalid" in str(e).lower():
                logger.debug(f"Ignored old callback query: {call.id}")
            else:
                raise
    
    except telebot.apihelper.ApiTelegramException as e:
        # Handle Telegram API specific errors
        if "query is too old" in str(e).lower() or "query ID is invalid" in str(e).lower():
            logger.debug(f"Callback query expired: {call.id}")
        else:
            logger.error(f"Telegram API error in callback handler: {e}")
            try:
                bot.send_message(
                    chat_id,
                    f"❌ Произошла ошибка при обработке запроса.\n"
                    f"Попробуйте выбрать действие из меню:",
                    reply_markup=get_main_menu_keyboard()
                )
            except:
                pass
    
    except Exception as e:
        logger.error(f"Error in callback handler: {e}", exc_info=True)
        try:
            bot.send_message(
                chat_id,
                f"❌ Произошла ошибка при обработке запроса.\n"
                f"Попробуйте выбрать действие из меню:",
                reply_markup=get_main_menu_keyboard()
            )
        except:
            pass


# Trip creation flow
def start_new_trip(chat_id, user_id):
    """Start new trip creation flow"""
    db.set_user_state(user_id, STATE_WAITING_FROM_COUNTRY, {})
    bot.send_message(
        chat_id,
        "🏠 Введите страну отправления (например: Россия, США, Китай):"
    )


def handle_from_country(message, user_id):
    """Handle from country input"""
    country = message.text.strip()
    currency = get_currency_from_country(country)
    
    if not currency:
        bot.send_message(
            message.chat.id,
            f"❌ К сожалению, я не знаю валюту для страны '{country}'.\n\n"
            f"Попробуйте ввести по-другому или выберите из списка:\n"
            f"{', '.join(list(COUNTRY_CURRENCY_MAP.keys())[:10])}...",
            reply_markup=get_back_to_menu_keyboard()
        )
        return
    
    state_data = {"from_country": country, "from_currency": currency}
    db.set_user_state(user_id, STATE_WAITING_TO_COUNTRY, state_data)
    
    bot.send_message(
        message.chat.id,
        f"✅ Страна отправления: {country} ({currency})\n\n"
        f"🎯 Теперь введите страну назначения:"
    )


def handle_to_country(message, user_id):
    """Handle to country input"""
    state = db.get_user_state(user_id)
    country = message.text.strip()
    currency = get_currency_from_country(country)
    
    if not currency:
        bot.send_message(
            message.chat.id,
            f"❌ К сожалению, я не знаю валюту для страны '{country}'.\n\n"
            f"Попробуйте ввести по-другому.",
            reply_markup=get_back_to_menu_keyboard()
        )
        return
    
    state_data = state['data']
    state_data['to_country'] = country
    state_data['to_currency'] = currency
    
    # Get exchange rate from API
    try:
        result = convert_currency(
            1,
            state_data['from_currency'],
            state_data['to_currency']
        )
        
        if result.get('success'):
            rate = result.get('info', {}).get('quote', 0)
            if rate > 0:
                state_data['api_rate'] = rate
                db.set_user_state(user_id, STATE_WAITING_INITIAL_AMOUNT, state_data)
                
                bot.send_message(
                    message.chat.id,
                    f"✅ Маршрут: {state_data['from_country']} → {country}\n"
                    f"💱 {state_data['from_currency']} → {state_data['to_currency']}\n\n"
                    f"💰 Введите начальную сумму в {state_data['from_currency']}, "
                    f"которую вы планируете взять с собой:"
                )
            else:
                raise ValueError("Invalid rate received")
        else:
            raise ValueError(result.get('error', {}).get('info', 'API Error'))
    
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ Ошибка при получении курса валют: {str(e)}\n\n"
            f"Попробуйте позже или обратитесь к администратору.",
            reply_markup=get_back_to_menu_keyboard()
        )
        db.clear_user_state(user_id)


def handle_initial_amount(message, user_id):
    """Handle initial amount input"""
    state = db.get_user_state(user_id)
    
    try:
        amount = float(message.text.strip().replace(",", ".").replace(" ", ""))
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        state_data = state['data']
        state_data['initial_amount'] = amount
        
        # Convert to foreign currency
        result = convert_currency(
            amount,
            state_data['from_currency'],
            state_data['to_currency']
        )
        
        if result.get('success'):
            converted = result.get('result', 0)
            rate = result.get('info', {}).get('quote', 0)
            
            state_data['converted_amount'] = converted
            state_data['current_rate'] = rate
            
            db.set_user_state(user_id, STATE_WAITING_RATE_CONFIRMATION, state_data)
            
            # Show rate confirmation
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(
                types.InlineKeyboardButton("✅ Да, подходит", callback_data="rate_accept_0"),
                types.InlineKeyboardButton("❌ Нет, ввести свой", callback_data="rate_custom_0")
            )
            
            bot.send_message(
                message.chat.id,
                f"💱 Текущий курс обмена:\n"
                f"1 {state_data['from_currency']} = {rate:.4f} {state_data['to_currency']}\n\n"
                f"💰 Ваша сумма:\n"
                f"{format_amount(amount)} {state_data['from_currency']} = "
                f"{format_amount(converted)} {state_data['to_currency']}\n\n"
                f"Подходит ли вам этот курс?",
                reply_markup=keyboard
            )
        else:
            raise ValueError("Conversion failed")
    
    except ValueError:
        bot.send_message(
            message.chat.id,
            "❌ Пожалуйста, введите корректное положительное число (например: 10000 или 10000.50)"
        )


def handle_rate_acceptance(chat_id, user_id, message_id, trip_id):
    """Handle rate acceptance"""
    state = db.get_user_state(user_id)
    
    if not state or state['state'] != STATE_WAITING_RATE_CONFIRMATION:
        bot.edit_message_text(
            "❌ Ошибка: неверное состояние",
            chat_id,
            message_id
        )
        return
    
    state_data = state['data']
    
    # Create trip
    trip_name = f"{state_data['from_country']} → {state_data['to_country']}"
    trip_id = db.create_trip(
        user_id=user_id,
        trip_name=trip_name,
        from_country=state_data['from_country'],
        to_country=state_data['to_country'],
        from_currency=state_data['from_currency'],
        to_currency=state_data['to_currency'],
        exchange_rate=state_data['current_rate'],
        initial_amount_home=state_data['initial_amount'],
        initial_amount_foreign=state_data['converted_amount'],
        is_custom_rate=False
    )
    
    db.set_active_trip(user_id, trip_id)
    db.clear_user_state(user_id)
    
    bot.edit_message_text(
        f"✅ Путешествие создано!\n\n"
        f"📍 Маршрут: {trip_name}\n"
        f"💱 Курс: 1 {state_data['from_currency']} = {state_data['current_rate']:.4f} {state_data['to_currency']}\n"
        f"💰 Стартовый баланс:\n"
        f"   • {format_amount(state_data['initial_amount'])} {state_data['from_currency']}\n"
        f"   • {format_amount(state_data['converted_amount'])} {state_data['to_currency']}\n\n"
        f"Теперь просто отправляйте мне суммы расходов цифрами, "
        f"и я буду их учитывать! 📝",
        chat_id,
        message_id,
        reply_markup=get_back_to_menu_keyboard()
    )


def handle_rate_custom(chat_id, user_id, message_id, trip_id):
    """Handle custom rate request"""
    state = db.get_user_state(user_id)
    
    if not state:
        bot.edit_message_text(
            "❌ Ошибка: неверное состояние",
            chat_id,
            message_id
        )
        return
    
    state_data = state['data']
    db.set_user_state(user_id, STATE_WAITING_CUSTOM_RATE, state_data)
    
    bot.edit_message_text(
        f"✏️ Введите свой курс обмена:\n\n"
        f"Сколько {state_data['to_currency']} вы получаете за 1 {state_data['from_currency']}?\n\n"
        f"Например: 12.5",
        chat_id,
        message_id
    )


def handle_custom_rate_input(message, user_id):
    """Handle custom rate input"""
    state = db.get_user_state(user_id)
    
    try:
        custom_rate = float(message.text.strip().replace(",", "."))
        if custom_rate <= 0:
            raise ValueError("Rate must be positive")
        
        state_data = state['data']
        state_data['current_rate'] = custom_rate
        state_data['converted_amount'] = state_data['initial_amount'] * custom_rate
        
        # Create trip with custom rate
        trip_name = f"{state_data['from_country']} → {state_data['to_country']}"
        trip_id = db.create_trip(
            user_id=user_id,
            trip_name=trip_name,
            from_country=state_data['from_country'],
            to_country=state_data['to_country'],
            from_currency=state_data['from_currency'],
            to_currency=state_data['to_currency'],
            exchange_rate=custom_rate,
            initial_amount_home=state_data['initial_amount'],
            initial_amount_foreign=state_data['converted_amount'],
            is_custom_rate=True
        )
        
        db.set_active_trip(user_id, trip_id)
        db.clear_user_state(user_id)
        
        bot.send_message(
            message.chat.id,
            f"✅ Путешествие создано с вашим курсом!\n\n"
            f"📍 Маршрут: {trip_name}\n"
            f"💱 Курс: 1 {state_data['from_currency']} = {custom_rate:.4f} {state_data['to_currency']}\n"
            f"💰 Стартовый баланс:\n"
            f"   • {format_amount(state_data['initial_amount'])} {state_data['from_currency']}\n"
            f"   • {format_amount(state_data['converted_amount'])} {state_data['to_currency']}\n\n"
            f"Теперь просто отправляйте мне суммы расходов! 📝",
            reply_markup=get_back_to_menu_keyboard()
        )
    
    except ValueError:
        bot.send_message(
            message.chat.id,
            "❌ Пожалуйста, введите корректное положительное число (например: 12.5)"
        )


# Trip management functions
def show_my_trips(chat_id, user_id):
    """Show user's trips"""
    trips = db.get_user_trips(user_id)
    
    if not trips:
        bot.send_message(
            chat_id,
            "📭 У вас пока нет путешествий.\n\n"
            "Создайте первое путешествие, чтобы начать!",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    active_trip = db.get_active_trip(user_id)
    active_trip_id = active_trip['trip_id'] if active_trip else None
    
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    for trip in trips:
        is_active = trip['trip_id'] == active_trip_id
        status = "✅ " if is_active else ""
        button_text = f"{status}{trip['trip_name']} ({trip['to_currency']})"
        keyboard.add(
            types.InlineKeyboardButton(
                button_text,
                callback_data=f"select_trip_{trip['trip_id']}"
            )
        )
    
    keyboard.add(types.InlineKeyboardButton("🔙 Главное меню", callback_data="menu_main"))
    
    bot.send_message(
        chat_id,
        "🗺 Ваши путешествия:\n\n"
        "✅ — активное путешествие\n"
        "Нажмите на путешествие, чтобы сделать его активным:",
        reply_markup=keyboard
    )


def handle_trip_selection(chat_id, user_id, message_id, trip_id):
    """Handle trip selection"""
    trip = db.get_trip(trip_id)
    
    if not trip or trip['user_id'] != user_id:
        bot.edit_message_text(
            "❌ Путешествие не найдено",
            chat_id,
            message_id
        )
        return
    
    db.set_active_trip(user_id, trip_id)
    
    bot.edit_message_text(
        f"✅ Активное путешествие изменено!\n\n"
        f"📍 {trip['trip_name']}\n"
        f"💱 {trip['from_currency']} → {trip['to_currency']}\n"
        f"💰 Баланс:\n"
        f"   • {format_amount(trip['current_balance_foreign'])} {trip['to_currency']}\n"
        f"   • {format_amount(trip['current_balance_home'])} {trip['from_currency']}",
        chat_id,
        message_id,
        reply_markup=get_back_to_menu_keyboard()
    )


def show_balance(chat_id, user_id):
    """Show current balance"""
    trip = db.get_active_trip(user_id)
    
    if not trip:
        bot.send_message(
            chat_id,
            "❌ У вас нет активного путешествия.\n\n"
            "Создайте новое путешествие, чтобы начать!",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    expenses = db.get_trip_total_expenses(trip['trip_id'])
    
    bot.send_message(
        chat_id,
        f"💰 Баланс путешествия\n"
        f"📍 {trip['trip_name']}\n\n"
        f"🏦 Текущий баланс:\n"
        f"   • {format_amount(trip['current_balance_foreign'])} {trip['to_currency']}\n"
        f"   • {format_amount(trip['current_balance_home'])} {trip['from_currency']}\n\n"
        f"💸 Потрачено:\n"
        f"   • {format_amount(expenses['total_foreign'])} {trip['to_currency']}\n"
        f"   • {format_amount(expenses['total_home'])} {trip['from_currency']}\n\n"
        f"💵 Начальная сумма:\n"
        f"   • {format_amount(trip['initial_amount_foreign'])} {trip['to_currency']}\n"
        f"   • {format_amount(trip['initial_amount_home'])} {trip['from_currency']}",
        reply_markup=get_back_to_menu_keyboard()
    )


def show_history(chat_id, user_id):
    """Show expense history"""
    trip = db.get_active_trip(user_id)
    
    if not trip:
        bot.send_message(
            chat_id,
            "❌ У вас нет активного путешествия.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    expenses = db.get_trip_expenses(trip['trip_id'], limit=20)
    
    if not expenses:
        bot.send_message(
            chat_id,
            f"📊 История расходов\n"
            f"📍 {trip['trip_name']}\n\n"
            f"Расходов пока нет.",
            reply_markup=get_back_to_menu_keyboard()
        )
        return
    
    history_text = f"📊 История расходов\n📍 {trip['trip_name']}\n\n"
    
    for exp in expenses[:10]:
        date = datetime.fromisoformat(exp['created_at']).strftime("%d.%m %H:%M")
        history_text += (
            f"🔸 {date}\n"
            f"   {format_amount(exp['amount_foreign'])} {trip['to_currency']} = "
            f"{format_amount(exp['amount_home'])} {trip['from_currency']}\n"
        )
    
    total = db.get_trip_total_expenses(trip['trip_id'])
    history_text += (
        f"\n💸 Всего потрачено:\n"
        f"   {format_amount(total['total_foreign'])} {trip['to_currency']} = "
        f"{format_amount(total['total_home'])} {trip['from_currency']}"
    )
    
    bot.send_message(
        chat_id,
        history_text,
        reply_markup=get_back_to_menu_keyboard()
    )


def start_rate_change(chat_id, user_id):
    """Start rate change flow"""
    trip = db.get_active_trip(user_id)
    
    if not trip:
        bot.send_message(
            chat_id,
            "❌ У вас нет активного путешествия.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    db.set_user_state(user_id, STATE_WAITING_NEW_RATE, {"trip_id": trip['trip_id']})
    
    bot.send_message(
        chat_id,
        f"💱 Изменение курса\n"
        f"📍 {trip['trip_name']}\n\n"
        f"Текущий курс: 1 {trip['from_currency']} = {trip['exchange_rate']:.4f} {trip['to_currency']}\n\n"
        f"Введите новый курс обмена:"
    )


def handle_new_rate(message, user_id):
    """Handle new rate input"""
    state = db.get_user_state(user_id)
    
    try:
        new_rate = float(message.text.strip().replace(",", "."))
        if new_rate <= 0:
            raise ValueError("Rate must be positive")
        
        trip_id = state['data']['trip_id']
        trip = db.get_trip(trip_id)
        
        db.update_trip_rate(trip_id, new_rate, is_custom=True)
        db.clear_user_state(user_id)
        
        bot.send_message(
            message.chat.id,
            f"✅ Курс обновлён!\n\n"
            f"📍 {trip['trip_name']}\n"
            f"💱 Новый курс: 1 {trip['from_currency']} = {new_rate:.4f} {trip['to_currency']}\n\n"
            f"Все новые расходы будут рассчитываться по новому курсу.",
            reply_markup=get_back_to_menu_keyboard()
        )
    
    except ValueError:
        bot.send_message(
            message.chat.id,
            "❌ Пожалуйста, введите корректное положительное число"
        )


# Expense handling
def handle_expense_amount(message, user_id):
    """Handle numeric expense input"""
    trip = db.get_active_trip(user_id)
    
    if not trip:
        bot.send_message(
            message.chat.id,
            "❌ У вас нет активного путешествия.\n\n"
            "Создайте новое путешествие, чтобы начать!",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    try:
        amount_foreign = float(message.text.strip().replace(",", ".").replace(" ", ""))
        if amount_foreign <= 0:
            raise ValueError("Amount must be positive")
        
        # Convert to home currency using trip rate
        amount_home = amount_foreign / trip['exchange_rate']
        
        # Create confirmation keyboard
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("✅ Да", callback_data=f"expense_yes_{amount_foreign}"),
            types.InlineKeyboardButton("❌ Нет", callback_data=f"expense_no_{amount_foreign}")
        )
        
        # Store pending expense in user state
        db.set_user_state(user_id, "pending_expense", {
            "amount_foreign": amount_foreign,
            "amount_home": amount_home,
            "trip_id": trip['trip_id']
        })
        
        bot.send_message(
            message.chat.id,
            f"💸 {format_amount(amount_foreign)} {trip['to_currency']} = "
            f"{format_amount(amount_home)} {trip['from_currency']}\n\n"
            f"Учесть как расход?",
            reply_markup=keyboard
        )
    
    except ValueError:
        bot.send_message(
            message.chat.id,
            "❌ Пожалуйста, введите корректное положительное число"
        )


def handle_expense_confirmation(chat_id, user_id, message_id, amount, confirmed):
    """Handle expense confirmation"""
    state = db.get_user_state(user_id)
    
    if not state or state['state'] != "pending_expense":
        bot.edit_message_text(
            "❌ Ошибка: неверное состояние",
            chat_id,
            message_id
        )
        return
    
    if not confirmed:
        bot.edit_message_text(
            "❌ Расход не учтён",
            chat_id,
            message_id,
            reply_markup=get_back_to_menu_keyboard()
        )
        db.clear_user_state(user_id)
        return
    
    expense_data = state['data']
    trip = db.get_trip(expense_data['trip_id'])
    
    # Add expense
    db.add_expense(
        trip_id=expense_data['trip_id'],
        amount_foreign=expense_data['amount_foreign'],
        amount_home=expense_data['amount_home']
    )
    
    # Update balance
    new_balance_foreign = trip['current_balance_foreign'] - expense_data['amount_foreign']
    new_balance_home = trip['current_balance_home'] - expense_data['amount_home']
    
    db.update_trip_balance(
        trip_id=expense_data['trip_id'],
        balance_home=new_balance_home,
        balance_foreign=new_balance_foreign
    )
    
    db.clear_user_state(user_id)
    
    bot.edit_message_text(
        f"✅ Расход учтён!\n\n"
        f"💸 Потрачено:\n"
        f"   {format_amount(expense_data['amount_foreign'])} {trip['to_currency']} = "
        f"{format_amount(expense_data['amount_home'])} {trip['from_currency']}\n\n"
        f"💰 Остаток:\n"
        f"   {format_amount(new_balance_foreign)} {trip['to_currency']} = "
        f"{format_amount(new_balance_home)} {trip['from_currency']}",
        chat_id,
        message_id,
        reply_markup=get_back_to_menu_keyboard()
    )


# Main message handler
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Handle all text messages"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Check user state
    state = db.get_user_state(user_id)
    
    if state:
        # Handle states
        if state['state'] == STATE_WAITING_FROM_COUNTRY:
            handle_from_country(message, user_id)
        elif state['state'] == STATE_WAITING_TO_COUNTRY:
            handle_to_country(message, user_id)
        elif state['state'] == STATE_WAITING_INITIAL_AMOUNT:
            handle_initial_amount(message, user_id)
        elif state['state'] == STATE_WAITING_CUSTOM_RATE:
            handle_custom_rate_input(message, user_id)
        elif state['state'] == STATE_WAITING_NEW_RATE:
            handle_new_rate(message, user_id)
        return
    
    # Check if message is a number (potential expense)
    if re.match(r'^\d+([.,]\d+)?$', text.replace(" ", "")):
        handle_expense_amount(message, user_id)
    else:
        bot.send_message(
            message.chat.id,
            "❓ Отправьте число для добавления расхода или используйте меню:",
            reply_markup=get_main_menu_keyboard()
        )


# Error handler
@bot.message_handler(content_types=['photo', 'document', 'audio', 'video', 'voice', 'sticker'])
def handle_other_content(message):
    """Handle non-text messages"""
    bot.send_message(
        message.chat.id,
        "❌ Я работаю только с текстовыми сообщениями и числами.",
        reply_markup=get_main_menu_keyboard()
    )


# Start bot
if __name__ == "__main__":
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    print("=" * 50)
    print("🤖 Travel Wallet Bot")
    print("=" * 50)
    
    # Test bot token before starting
    try:
        print("🔍 Проверка токена бота...")
        bot_info = bot.get_me()
        print(f"✅ Подключение успешно! Бот: @{bot_info.username}")
    except Exception as e:
        logger.error(f"Ошибка при проверке токена: {e}")
        print(f"❌ Не удалось подключиться к Telegram API")
        print(f"\n💡 Возможные причины:")
        print(f"   1. Нет подключения к интернету")
        print(f"   2. Telegram API недоступен в вашем регионе (нужен VPN)")
        print(f"   3. Неверный TELEGRAM_TOKEN в .env файле")
        print(f"   4. Firewall/антивирус блокирует подключение")
        print(f"\n💡 Попробуйте:")
        print(f"   - Проверить интернет-соединение")
        print(f"   - Включить VPN (если Telegram заблокирован)")
        print(f"   - Проверить токен в .env файле")
        sys.exit(1)
    
    # Try to remove webhook, but don't fail if it times out
    try:
        print("🔄 Очистка webhook...")
        bot.remove_webhook()
        print("✅ Webhook очищен")
    except Exception as e:
        logger.warning(f"Не удалось очистить webhook: {e}")
        print("⚠️  Webhook не очищен (продолжаем)")
    
    print("✅ Бот запущен и готов к работе!")
    print("📱 Нажмите Ctrl+C для остановки")
    print("=" * 50)
    logger.info("Bot started successfully")
    
    try:
        # Start polling with proper settings
        # allowed_updates - only process messages and callback queries
        # skip_pending=True - skip old updates when bot restarts
        bot.infinity_polling(
            timeout=30, 
            long_polling_timeout=30,
            allowed_updates=['message', 'callback_query'],
            skip_pending=True
        )
    except KeyboardInterrupt:
        pass  # Handled by signal_handler
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        print(f"\n❌ Критическая ошибка: {str(e)[:200]}")
        try:
            bot.stop_polling()
        except:
            pass
        print("👋 Бот остановлен")
        sys.exit(1)
