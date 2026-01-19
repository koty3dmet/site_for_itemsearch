from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import random
import string
import hashlib

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lost_and_found.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'simple-secret-key-123'
app.template_folder = '../front'

db = SQLAlchemy(app)

# Модель пользователя (упрощенная)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(10), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)  # Отображаемое имя для входа
    full_name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    advertisements = db.Column(db.Text, default='')

# Модель объявления
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.String(10), unique=True, nullable=False)
    user_uid = db.Column(db.String(10), nullable=False)
    item_type = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.Date, nullable=False)
    contact_info = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')

# Генерация UID
def gen_UID():
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=6))

# Генерация ID для объявления
def gen_item_ID():
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=8))

# Хэширование пароля
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Главная страница
@app.route('/')
def index():
    return render_template('main_window/index.html', logged_in='user_uid' in session)

# Регистрация (простая форма)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        full_name = request.form.get('full_name', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Валидация
        if not username or len(username) < 3:
            flash('Имя пользователя должно быть не менее 3 символов', 'error')
            return redirect('/register')
        
        if not full_name:
            flash('Введите ФИО', 'error')
            return redirect('/register')
        
        if not password or len(password) < 4:
            flash('Пароль должен быть не менее 4 символов', 'error')
            return redirect('/register')
        
        if password != confirm_password:
            flash('Пароли не совпадают', 'error')
            return redirect('/register')
        
        # Проверяем, не занято ли имя пользователя
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Это имя пользователя уже занято', 'error')
            return redirect('/register')
        
        # Создаем нового пользователя
        uid = gen_UID()
        hashed_password = hash_password(password)
        
        new_user = User(
            uid=uid,
            username=username,
            full_name=full_name,
            password=hashed_password
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            
            # Автоматически авторизуем
            session['user_uid'] = uid
            session['username'] = username
            session['full_name'] = full_name
            session['logged_in'] = True
            
            flash(f'✅ Регистрация успешна! Ваш UID: {uid}', 'success')
            return redirect('/')
            
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка регистрации: {e}")
            flash('Ошибка регистрации', 'error')
            return redirect('/register')
    
    return render_template('register.html')

# Вход в аккаунт
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == hash_password(password):
            session['user_uid'] = user.uid
            session['username'] = user.username
            session['full_name'] = user.full_name
            session['logged_in'] = True
            return redirect('/')
        else:
            flash('Неверное имя пользователя или пароль', 'error')
    
    return render_template('login.html')

# Выход
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# Создание объявления
@app.route('/create', methods=['GET', 'POST'])
def create():
    if 'user_uid' not in session:
        flash('Для создания объявления необходимо войти в систему', 'error')
        return redirect('/login')
    
    if request.method == 'POST':
        item_type = request.form.get('item_type')
        category = request.form.get('category')
        city = request.form.get('city')
        title = request.form.get('title')
        description = request.form.get('description')
        date_str = request.form.get('date')
        contact_info = request.form.get('contact_info', '')
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            date = datetime.now().date()
        
        item_id = gen_item_ID()
        
        new_item = Item(
            item_id=item_id,
            user_uid=session['user_uid'],
            item_type=item_type,
            category=category,
            city=city,
            title=title,
            description=description,
            date=date,
            contact_info=contact_info,
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_item)
        
        # Обновляем список объявлений пользователя
        user = User.query.filter_by(uid=session['user_uid']).first()
        if user:
            ads = user.advertisements.split(',') if user.advertisements else []
            ads.append(item_id)
            user.advertisements = ','.join(filter(None, ads))
        
        db.session.commit()
        
        flash(f'✅ Объявление создано! ID: {item_id}', 'success')
        return redirect('/search')
    
    return render_template('create_ad/create.html')

# Поиск объявлений
@app.route('/search', methods=['GET', 'POST'])
def search():
    items = []
    
    if request.method == 'POST':
        search_query = request.form.get('search_query', '')
        category = request.form.get('category', '')
        city = request.form.get('city', '')
        
        query = Item.query.filter_by(status='active')
        
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
        items = Item.query.filter_by(status='active').order_by(Item.created_at.desc()).limit(50).all()
    
    categories = db.session.query(Item.category).distinct().all()
    cities = db.session.query(Item.city).distinct().all()
    
    return render_template('search_item/search.html', 
                         items=items,
                         categories=[c[0] for c in categories],
                         cities=[c[0] for c in cities])

# Контакты объявления
@app.route('/contact/<string:item_id>')
def contact(item_id):
    item = Item.query.filter_by(item_id=item_id).first_or_404()
    return render_template('search_item/contact.html', item=item)

# Личный кабинет
@app.route('/profile')
def profile():
    if 'user_uid' not in session:
        return redirect('/login')
    
    user = User.query.filter_by(uid=session['user_uid']).first()
    user_items = []
    
    if user and user.advertisements:
        item_ids = user.advertisements.split(',')
        for item_id in item_ids:
            if item_id:
                item = Item.query.filter_by(item_id=item_id).first()
                if item:
                    user_items.append(item)
    
    return render_template('profile.html', 
                         user=user, 
                         items=user_items)

if __name__ == '__main__':
    # Создаем папки
    os.makedirs('../front/main_window', exist_ok=True)
    os.makedirs('../front/create_ad', exist_ok=True)
    os.makedirs('../front/search_item', exist_ok=True)
    
    # Создаем таблицы в БД
    with app.app_context():
        db.create_all()
        print("✅ База данных создана")
    
    print("=" * 60)
    print("🚀 Сервер запущен! http://localhost:5000")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)