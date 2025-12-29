# 🐳 Деплой в Docker Hub

## Быстрый деплой образа Flask бэкенда

### Шаг 1: Логин в Docker Hub

Выполните команду в терминале:

```bash
docker login
```

Введите:
- **Username:** `bezngor`
- **Password:** ваш пароль от Docker Hub

### Шаг 2: Создание тега (уже выполнено ✓)

```bash
docker tag autodeploy-backend:latest bezngor/flask-backend:latest
```

### Шаг 3: Push образа в Docker Hub

```bash
docker push bezngor/flask-backend:latest
```

### Шаг 4: Проверка

После успешного push, ваш образ будет доступен по адресу:
```
https://hub.docker.com/r/bezngor/flask-backend
```

## 📦 Использование образа с Docker Hub

Теперь любой может использовать ваш образ:

```bash
# Скачать образ
docker pull bezngor/flask-backend:latest

# Запустить контейнер
docker run -d -p 5000:5000 --name flask-app bezngor/flask-backend:latest
```

## 🏷️ Создание версий (tags)

Рекомендуется использовать версионирование:

```bash
# Создать тег с версией
docker tag autodeploy-backend:latest bezngor/flask-backend:v1.0.0
docker tag autodeploy-backend:latest bezngor/flask-backend:stable

# Запушить все теги
docker push bezngor/flask-backend:latest
docker push bezngor/flask-backend:v1.0.0
docker push bezngor/flask-backend:stable
```

## 🔄 Обновление Docker Compose для использования Docker Hub образа

Измените `docker-compose.yml`:

```yaml
services:
  backend:
    image: bezngor/flask-backend:latest  # Вместо build
    container_name: flask-backend
    ports:
      - "5000:5000"
    # ... остальные настройки
```

Это позволит запускать приложение без локальной сборки.

## 🚀 Автоматизация (опционально)

Создайте скрипт `deploy.sh`:

```bash
#!/bin/bash
# Сборка образа
docker-compose build backend

# Создание тегов
docker tag autodeploy-backend:latest bezngor/flask-backend:latest
docker tag autodeploy-backend:latest bezngor/flask-backend:$(date +%Y%m%d)

# Push в Docker Hub
docker push bezngor/flask-backend:latest
docker push bezngor/flask-backend:$(date +%Y%m%d)

echo "✅ Образ успешно загружен в Docker Hub!"
```

Использование:
```bash
chmod +x deploy.sh
./deploy.sh
```

## 🔐 Использование токена вместо пароля

Для большей безопасности используйте Personal Access Token:

1. Зайдите на https://hub.docker.com/settings/security
2. Создайте новый Access Token
3. Используйте его вместо пароля:

```bash
docker login -u bezngor
# Вместо пароля вставьте токен
```

## 📋 Полезные команды

```bash
# Просмотр локальных образов
docker images bezngor/*

# Удаление образа из Docker Hub (через веб-интерфейс)
# https://hub.docker.com/r/bezngor/flask-backend/tags

# Информация об образе
docker inspect bezngor/flask-backend:latest

# Просмотр истории слоев
docker history bezngor/flask-backend:latest
```

## 🌐 Публичный доступ

После push ваш образ будет доступен публично:
- Ссылка: `https://hub.docker.com/r/bezngor/flask-backend`
- Pull команда: `docker pull bezngor/flask-backend`

Если хотите сделать образ приватным:
1. Зайдите на Docker Hub
2. Откройте репозиторий
3. Settings → Make Private

