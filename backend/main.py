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
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.template_folder = '../front'

db = SQLAlchemy(app)

# Модель пользователя
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(10), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    advertisements = db.Column(db.Text, default='')  # ID объявлений через запятую

# Модель объявления (обновленная)
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.String(10), unique=True, nullable=False)  # Публичный ID
    user_uid = db.Column(db.String(10), nullable=False)  # UID пользователя
    item_type = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.Date, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')

# Генерация UID (6 символов: буквы и цифры)
def gen_UID():
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=6))

# Генерация ID для объявления
def gen_item_ID():
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=8))

# Генерация SMS кода (4 цифры)
def gen_sms_code():
    return str(random.randint(1000, 9999))

# Хэширование пароля
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Главная страница
@app.route('/')
def index():
    user_phone = session.get('phone', None)
    return render_template('main_window/index.html', user_phone=user_phone)

# Страница регистрации - шаг 1: телефон
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        phone = request.form.get('phone')
        
        # Проверка формата телефона (простая проверка)
        if not phone or len(phone) < 10:
            flash('Введите корректный номер телефона', 'error')
            return redirect('/register')
        
        # Генерируем SMS код (в реальном приложении здесь был бы вызов SMS API)
        sms_code = gen_sms_code()
        session['reg_phone'] = phone
        session['sms_code'] = sms_code
        
        # В реальном приложении: отправить SMS
        print(f"SMS код для {phone}: {sms_code}")  # Для тестирования
        
        return redirect('/register/verify')
    
    return render_template('regist/register.html')

# Страница верификации SMS кода
@app.route('/register/verify', methods=['GET', 'POST'])
def register_verify():
    if 'reg_phone' not in session:
        return redirect('/register')
    
    if request.method == 'POST':
        sms_code = request.form.get('sms_code')
        
        if sms_code == session.get('sms_code'):
            session['sms_verified'] = True
            return redirect('/register/details')
        else:
            flash('Неверный код подтверждения', 'error')
    
    return render_template('regist/verify.html', phone=session.get('reg_phone'))

# Страница регистрации - шаг 2: данные пользователя
@app.route('/register/details', methods=['GET', 'POST'])
def register_details():
    if 'reg_phone' not in session or not session.get('sms_verified'):
        return redirect('/register')
    
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Проверки
        if not full_name:
            flash('Введите ФИО', 'error')
            return redirect('/register/details')
        
        if not password or len(password) < 4:
            flash('Пароль должен быть не менее 4 символов', 'error')
            return redirect('/register/details')
        
        if password != confirm_password:
            flash('Пароли не совпадают', 'error')
            return redirect('/register/details')
        
        # Проверяем, не зарегистрирован ли уже телефон
        existing_user = User.query.filter_by(phone=session['reg_phone']).first()
        if existing_user:
            flash('Этот номер телефона уже зарегистрирован', 'error')
            return redirect('/login')
        
        # Создаем нового пользователя
        uid = gen_UID()
        hashed_password = hash_password(password)
        
        new_user = User(
            uid=uid,
            phone=session['reg_phone'],
            full_name=full_name,
            password=hashed_password
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Авторизуем пользователя
        session['user_uid'] = uid
        session['user_full_name'] = full_name
        session['phone'] = session['reg_phone']
        
        # Очищаем временные данные регистрации
        session.pop('reg_phone', None)
        session.pop('sms_code', None)
        session.pop('sms_verified', None)
        
        flash('Регистрация успешна! Ваш UID: ' + uid, 'success')
        return redirect('/')
    
    return render_template('regist/details.html')

# Страница входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        user = User.query.filter_by(phone=phone).first()
        
        if user and user.password == hash_password(password):
            session['user_uid'] = user.uid
            session['user_full_name'] = user.full_name
            session['phone'] = user.phone
            return redirect('/')
        else:
            flash('Неверный номер телефона или пароль', 'error')
    
    return render_template('regist/login.html')

# Выход
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# Создание объявления (обновленная версия с привязкой к пользователю)
@app.route('/create', methods=['GET', 'POST'])
def create():
    if 'user_uid' not in session:
        flash('Для создания объявления необходимо войти в систему', 'error')
        return redirect('/login')
    
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
        
        # Генерируем ID для объявления
        item_id = gen_item_ID()
        
        # Создаем запись в БД
        new_item = Item(
            item_id=item_id,
            user_uid=session['user_uid'],
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
        
        # Обновляем список объявлений пользователя
        user = User.query.filter_by(uid=session['user_uid']).first()
        if user:
            ads = user.advertisements.split(',') if user.advertisements else []
            ads.append(item_id)
            user.advertisements = ','.join(filter(None, ads))
        
        db.session.commit()
        
        flash(f'Объявление создано! ID: {item_id}', 'success')
        return redirect('/search')
    
    return render_template('create_ad/create.html', user_phone=session.get('phone'))

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
                         cities=[c[0] for c in cities],
                         user_uid=session.get('user_uid'))

# Контакты объявления
@app.route('/contact/<string:item_id>')
def contact(item_id):
    item = Item.query.filter_by(item_id=item_id).first_or_404()
    return render_template('search_item/contact.html', item=item)

# Личный кабинет пользователя
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
    
    return render_template('regist/profile.html', 
                         user=user, 
                         items=user_items)

if __name__ == '__main__':
    # Создаем папки
    os.makedirs('../front/main_window', exist_ok=True)
    os.makedirs('../front/create_ad', exist_ok=True)
    os.makedirs('../front/search_item', exist_ok=True)
    os.makedirs('../front/regist', exist_ok=True)
    
    # Создаем таблицы в БД
    with app.app_context():
        db.create_all()
    
    app.run(debug=True, host='0.0.0.0', port=5000)