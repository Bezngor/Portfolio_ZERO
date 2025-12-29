// API base URL - в Docker Compose будет проксироваться через nginx
const API_URL = '/api';

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    loadHome();
    loadInfo();
    checkHealth();
    
    // Автообновление статуса каждые 30 секунд
    setInterval(checkHealth, 30000);
    
    // Enter для отправки в Echo
    document.getElementById('echoInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendEcho();
    });
});

// Обновление времени последнего обновления
function updateLastUpdateTime() {
    const now = new Date();
    document.getElementById('lastUpdate').textContent = now.toLocaleTimeString('ru-RU');
}

// Загрузка главной информации
async function loadHome() {
    try {
        const response = await fetch(`${API_URL}/`);
        const data = await response.json();
        
        const homeDiv = document.getElementById('homeData');
        homeDiv.innerHTML = `
            <p><strong>Сообщение:</strong> ${data.message}</p>
            <p><strong>Статус:</strong> ${data.status}</p>
            <p><strong>Время:</strong> ${new Date(data.timestamp).toLocaleString('ru-RU')}</p>
        `;
        updateLastUpdateTime();
    } catch (error) {
        showError('homeData', error);
    }
}

// Загрузка информации о контейнере
async function loadInfo() {
    try {
        const response = await fetch(`${API_URL}/info`);
        const data = await response.json();
        
        const infoDiv = document.getElementById('infoData');
        infoDiv.innerHTML = `
            <p><strong>Hostname:</strong> ${data.hostname}</p>
            <p><strong>Окружение:</strong> ${data.environment}</p>
            <p><strong>Python версия:</strong> ${data.python_version.split('\\n')[0]}</p>
            <p><strong>Время:</strong> ${new Date(data.timestamp).toLocaleString('ru-RU')}</p>
        `;
        updateLastUpdateTime();
    } catch (error) {
        showError('infoData', error);
    }
}

// Проверка здоровья
async function checkHealth() {
    const statusBadge = document.getElementById('status');
    statusBadge.textContent = 'проверка...';
    statusBadge.className = 'status-badge checking';
    
    try {
        const response = await fetch(`${API_URL}/health`);
        const data = await response.json();
        
        if (data.status === 'healthy') {
            statusBadge.textContent = '✓ Работает';
            statusBadge.className = 'status-badge healthy';
        }
        
        const healthDiv = document.getElementById('healthData');
        healthDiv.innerHTML = `
            <p><strong>Статус:</strong> ${data.status}</p>
            <p><strong>Сервис:</strong> ${data.service}</p>
            <p><strong>Проверено:</strong> ${new Date(data.timestamp).toLocaleString('ru-RU')}</p>
        `;
        updateLastUpdateTime();
    } catch (error) {
        statusBadge.textContent = '✗ Ошибка';
        statusBadge.className = 'status-badge error';
        showError('healthData', error);
    }
}

// Отправка Echo сообщения
async function sendEcho() {
    const input = document.getElementById('echoInput');
    const message = input.value.trim();
    
    if (!message) {
        showResult('echoResult', 'Введите сообщение!', true);
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/echo/${encodeURIComponent(message)}`);
        const data = await response.json();
        
        const resultDiv = document.getElementById('echoResult');
        resultDiv.innerHTML = `
            <p><strong>Исходное:</strong> ${data.original_message}</p>
            <p><strong>Echo:</strong> ${data.echo}</p>
            <p><strong>Длина:</strong> ${data.length} символов</p>
        `;
        resultDiv.className = 'result-box show';
        input.value = '';
    } catch (error) {
        showResult('echoResult', `Ошибка: ${error.message}`, true);
    }
}

// Вычисления
async function calculate(operation) {
    const a = document.getElementById('numA').value;
    const b = document.getElementById('numB').value;
    
    if (!a || !b) {
        showResult('calcResult', 'Введите оба числа!', true);
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/${operation}/${a}/${b}`);
        
        if (!response.ok) {
            throw new Error('Ошибка вычисления');
        }
        
        const data = await response.json();
        
        const operations = {
            multiply: '×',
            divide: '÷',
            subtract: '−'
        };
        
        const resultDiv = document.getElementById('calcResult');
        resultDiv.innerHTML = `
            <p><strong>Операция:</strong> ${data.a} ${operations[operation]} ${data.b}</p>
            <p><strong>Результат:</strong> ${data.result}</p>
        `;
        resultDiv.className = 'result-box show';
    } catch (error) {
        showResult('calcResult', `Ошибка: ${error.message}`, true);
    }
}

// Показать результат
function showResult(elementId, message, isError = false) {
    const div = document.getElementById(elementId);
    div.innerHTML = `<p><strong>${isError ? 'Ошибка:' : 'Результат:'}</strong> ${message}</p>`;
    div.className = isError ? 'result-box show error' : 'result-box show';
}

// Показать ошибку
function showError(elementId, error) {
    const div = document.getElementById(elementId);
    div.innerHTML = `<p class="loading" style="color: #ef4444;">❌ Ошибка подключения: ${error.message}</p>`;
}

