from flask import Flask, jsonify
import datetime
import os
import socket

app = Flask(__name__)

@app.route('/')
def home():
    """Главная страница приложения"""
    return jsonify({
        'message': 'Добро пожаловать в тестовое Docker приложение!',
        'status': 'running',
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/health')
def health():
    """Проверка здоровья приложения"""
    return jsonify({
        'status': 'healthy',
        'service': 'test-app',
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/info')
def info():
    """Информация о контейнере"""
    return jsonify({
        'hostname': socket.gethostname(),
        'python_version': os.sys.version,
        'environment': os.environ.get('ENV', 'development'),
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/echo/<message>')
def echo(message):
    """Эхо сообщения"""
    return jsonify({
        'original_message': message,
        'echo': message.upper(),
        'length': len(message),
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/multiply/<int:a>/<int:b>')
def multiply(a, b):
    """Умножение двух чисел"""
    return jsonify({
        'a': a,
        'b': b,
        'result': a * b
    })

@app.route('/divide/<int:a>/<int:b>')
def divide(a, b):
    """Деление двух чисел"""
    return jsonify({
        'a': a,
        'b': b,
        'result': a / b
    })

@app.route('/subtract/<int:a>/<int:b>')
def subtract(a, b):
    """Вычитание двух чисел"""
    return jsonify({
        'a': a,
        'b': b,
        'result': a - b
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

