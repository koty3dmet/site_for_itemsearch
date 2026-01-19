from flask import Flask, render_template, send_from_directory
import os

app = Flask(__name__)

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/create')
def create():
    """Страница создания объявления"""
    return render_template('create.html')

@app.route('/search')
def search():
    """Страница поиска"""
    return render_template('search.html')

@app.route('/static/<path:path>')
def send_static(path):
    """Отдача статических файлов"""
    return send_from_directory('static', path)

if __name__ == '__main__':
    # Создаем папки для шаблонов и статики если их нет
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)