# 🚀 Quick Start Guide

## Запуск приложения за 3 шага

### Шаг 1: Запустить Docker Compose

```bash
docker-compose up -d
```

### Шаг 2: Открыть в браузере

```
http://localhost
```

### Шаг 3: Использовать приложение! 🎉

## Что вы увидите?

✨ **Красивый веб-интерфейс** с:
- 📊 Информацией о сервисе
- 🖥️ Данными о контейнере  
- 💬 Echo тестом
- 🔢 Калькулятором (умножение, деление, вычитание)
- ❤️ Health Check статусом

## Основные команды

```bash
# Остановить
docker-compose down

# Посмотреть логи
docker-compose logs -f

# Перезапустить
docker-compose restart
```

## Структура

```
┌─────────────────┐
│   Frontend      │  ← http://localhost
│   (Nginx)       │
└────────┬────────┘
         │ /api/*
         ↓
┌─────────────────┐
│   Backend       │  ← http://localhost:5000
│   (Flask)       │
└─────────────────┘
```

## Тестирование API напрямую

```bash
# Health check
curl http://localhost:5000/health

# Echo
curl http://localhost:5000/echo/Hello

# Калькулятор
curl http://localhost:5000/multiply/5/7
curl http://localhost:5000/divide/10/2
curl http://localhost:5000/subtract/15/5
```

## Подробная документация

- 📖 [README.md](README.md) - Основная документация
- 🐳 [DOCKER-COMPOSE.md](DOCKER-COMPOSE.md) - Docker Compose руководство

---

**Приятного использования!** 🎈

