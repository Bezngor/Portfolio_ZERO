# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY app.py .

# Открываем порт 5000
EXPOSE 5000

# Устанавливаем переменную окружения
ENV ENV=production

# Запускаем приложение
CMD ["python", "app.py"]

