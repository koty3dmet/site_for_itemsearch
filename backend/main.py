from flask import Flask, render_template
import os

app = Flask(__name__)

# Настройка путей к шаблонам
app.template_folder = '../front'

@app.route('/')
def index():
    """Главная страница"""
    return render_template('main_window/index.html')

@app.route('/create')
def create():
    """Страница создания объявления"""
    return render_template('create_ad/create.html')

@app.route('/search')
def search():
    """Страница поиска"""
    return render_template('search_item/search.html')

if __name__ == '__main__':
    # Создаем папки если их нет
    os.makedirs('../front/main_window', exist_ok=True)
    os.makedirs('../front/create_ad', exist_ok=True)
    os.makedirs('../front/search_item', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)