# 🔧 Настройка IDE

## ⚠️ Если IDE показывает ошибки импорта

После переноса/реорганизации проекта IDE может показывать:
```
Import "telebot" could not be resolved
Import "dotenv" could not be resolved
```

## ✅ Решение

### Вариант 1: Выбор интерпретатора в VSCode

1. Нажмите `Ctrl+Shift+P`
2. Введите: `Python: Select Interpreter`
3. Выберите: `.\venv\Scripts\python.exe`

### Вариант 2: Через настройки проекта

Создайте файл `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/Scripts/python.exe"
}
```

### Вариант 3: Перезагрузка окна

1. `Ctrl+Shift+P`
2. `Developer: Reload Window`

## 🚀 Запуск бота

### Активация venv:

**PowerShell:**
```powershell
cd "D:\ZERO\Vibecoding\lessons\MyCurrentApi"
.\venv\Scripts\activate
python travel_wallet_bot.py
```

**CMD:**
```cmd
cd "D:\ZERO\Vibecoding\lessons\MyCurrentApi"
venv\Scripts\activate.bat
python travel_wallet_bot.py
```

## 📦 Установленные пакеты:

- ✅ requests
- ✅ python-dotenv
- ✅ pyTelegramBotAPI

## ✨ Структура проекта (правильная):

```
MyCurrentApi/
├── .env                    # Токены (не в git)
├── .gitignore              # Игнорируемые файлы
├── requirements.txt        # Зависимости
├── README.md               # Документация
├── travel_wallet_bot.py    # Основной бот
├── database.py             # БД
├── currency_detector.py    # Определение валют
├── current_api.py          # API курсов
├── venv/                   # Виртуальное окружение
└── travel_wallet.db        # База данных
```

## 🗑️ Что можно удалить вручную:

- `Travel Wallet Telegram Bot/` (старая папка, если осталась)
- `travel_wallet_bot_backup.py` (резервная копия)

Закройте все программы, которые могут держать файлы открытыми, затем удалите.

## ✨ После выбора правильного интерпретатора все ошибки исчезнут!

