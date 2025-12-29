# PowerShell скрипт для деплоя в Docker Hub
# Использование: .\push_to_dockerhub.ps1

Write-Host "🐳 Деплой Flask Backend в Docker Hub" -ForegroundColor Cyan
Write-Host ""

# Параметры
$USERNAME = "bezngor"
$IMAGE_NAME = "flask-backend"
$LOCAL_IMAGE = "autodeploy-backend:latest"

Write-Host "📦 Шаг 1: Проверка локального образа..." -ForegroundColor Yellow
docker images $LOCAL_IMAGE

Write-Host ""
Write-Host "🏷️  Шаг 2: Создание тега для Docker Hub..." -ForegroundColor Yellow
docker tag $LOCAL_IMAGE "${USERNAME}/${IMAGE_NAME}:latest"

Write-Host ""
Write-Host "📋 Проверка созданного тега:" -ForegroundColor Yellow
docker images "${USERNAME}/${IMAGE_NAME}"

Write-Host ""
Write-Host "🔐 Шаг 3: Логин в Docker Hub..." -ForegroundColor Yellow
Write-Host "Пожалуйста, введите ваши credentials для Docker Hub" -ForegroundColor Green
docker login

Write-Host ""
Write-Host "⬆️  Шаг 4: Push образа в Docker Hub..." -ForegroundColor Yellow
docker push "${USERNAME}/${IMAGE_NAME}:latest"

Write-Host ""
Write-Host "✅ Готово! Образ загружен в Docker Hub" -ForegroundColor Green
Write-Host "🌐 Доступен по адресу: https://hub.docker.com/r/${USERNAME}/${IMAGE_NAME}" -ForegroundColor Cyan
Write-Host ""
Write-Host "Для использования образа:" -ForegroundColor White
Write-Host "  docker pull ${USERNAME}/${IMAGE_NAME}:latest" -ForegroundColor Gray
Write-Host "  docker run -d -p 5000:5000 ${USERNAME}/${IMAGE_NAME}:latest" -ForegroundColor Gray

