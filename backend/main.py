from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lost_and_found.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.template_folder = '../front'

db = SQLAlchemy(app)

# Модель базы данных
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_type = db.Column(db.String(20), nullable=False)  # lost/found
    category = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.Date, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')  # active/closed

@app.route('/')
def index():
    """Главная страница"""
    return render_template('main_window/index.html')

@app.route('/create', methods=['GET', 'POST'])
def create():
    """Страница создания объявления"""
    if request.method == 'POST':
        # Получаем данные из формы
        item_type = request.form.get('item_type')
        category = request.form.get('category')
        city = request.form.get('city')
        title = request.form.get('title')
        description = request.form.get('description')
        date_str = request.form.get('date')
        phone = request.form.get('phone')
        email = request.form.get('email')
        
        # Конвертируем дату
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            date = datetime.now().date()
        
        # Создаем запись в БД
        new_item = Item(
            item_type=item_type,
            category=category,
            city=city,
            title=title,
            description=description,
            date=date,
            phone=phone,
            email=email
        )
        
        db.session.add(new_item)
        db.session.commit()
        
        return redirect(url_for('search'))
    
    return render_template('create_ad/create.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    """Страница поиска"""
    items = []
    
    if request.method == 'POST':
        # Получаем параметры поиска
        search_query = request.form.get('search_query', '')
        category = request.form.get('category', '')
        city = request.form.get('city', '')
        
        # Базовый запрос
        query = Item.query.filter_by(status='active')
        
        # Применяем фильтры
        if search_query:
            query = query.filter(
                db.or_(
                    Item.title.ilike(f'%{search_query}%'),
                    Item.description.ilike(f'%{search_query}%')
                )
            )
        
        if category and category != 'all':
            query = query.filter_by(category=category)
        
        if city and city != 'all':
            query = query.filter_by(city=city)
        
        items = query.order_by(Item.created_at.desc()).all()
    else:
        # Показываем все активные объявления
        items = Item.query.filter_by(status='active').order_by(Item.created_at.desc()).limit(50).all()
    
    # Получаем уникальные категории и города для фильтров
    categories = db.session.query(Item.category).distinct().all()
    cities = db.session.query(Item.city).distinct().all()
    
    return render_template('search_item/search.html', 
                         items=items,
                         categories=[c[0] for c in categories],
                         cities=[c[0] for c in cities])

@app.route('/contact/<int:item_id>')
def contact(item_id):
    """Страница контактов для объявления"""
    item = Item.query.get_or_404(item_id)
    return render_template('search_item/contact.html', item=item)

if __name__ == '__main__':
    # Создаем папки
    os.makedirs('../front/main_window', exist_ok=True)
    os.makedirs('../front/create_ad', exist_ok=True)
    os.makedirs('../front/search_item', exist_ok=True)
    
    # Создаем таблицы в БД
    with app.app_context():
        db.create_all()
    
    app.run(debug=True, host='0.0.0.0', port=5000)