from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, User, Item
from datetime import datetime
import os
import random
import string
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../instance/lost_and_found.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-123-change-this'
app.config['SESSION_TYPE'] = 'filesystem'

# Указываем путь к шаблонам
app.template_folder = '../front'

# Инициализируем БД
db.init_app(app)

# Генерация UID пользователя
def generate_uid():
    characters = string.ascii_uppercase + string.digits
    return 'USR-' + ''.join(random.choices(characters, k=6))

# Генерация ID для объявления
def generate_item_id():
    characters = string.ascii_uppercase + string.digits
    return 'ITEM-' + ''.join(random.choices(characters, k=8))

# Хэширование пароля
def hash_password(password):
    return generate_password_hash(password)

# Проверка пароля
def verify_password(stored_hash, password):
    return check_password_hash(stored_hash, password)

# ===== МАРШРУТЫ =====

# Главная страница
@app.route('/')
def index():
    return render_template('index.html')

# Регистрация
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
        
        # Проверка уникальности username
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Это имя пользователя уже занято', 'error')
            return redirect('/register')
        
        # Создание пользователя
        uid = generate_uid()
        hashed_password = hash_password(password)
        
        new_user = User(
            uid=uid,
            username=username,
            full_name=full_name,
            password_hash=hashed_password
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            
            # Авторизация
            session['user_id'] = new_user.id
            session['user_uid'] = new_user.uid
            session['username'] = new_user.username
            session['full_name'] = new_user.full_name
            session['logged_in'] = True
            
            flash(f'✅ Регистрация успешна! Ваш UID: {uid}', 'success')
            return redirect('/')
            
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка регистрации: {e}")
            flash('Ошибка регистрации. Попробуйте снова.', 'error')
            return redirect('/register')
    
    return render_template('register/register.html')

# Вход
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        user = User.query.filter_by(username=username).first()
        
        if user and verify_password(user.password_hash, password):
            session['user_id'] = user.id
            session['user_uid'] = user.uid
            session['username'] = user.username
            session['full_name'] = user.full_name
            session['logged_in'] = True
            
            flash(f'✅ Добро пожаловать, {user.full_name}!', 'success')
            return redirect('/')
        else:
            flash('Неверное имя пользователя или пароль', 'error')
    
    return render_template('register/login.html')

# Выход
@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect('/')

# Профиль
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Для доступа к профилю необходимо войти в систему', 'error')
        return redirect('/login')
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect('/')
    
    # Получаем объявления пользователя
    user_items = Item.query.filter_by(user_id=user.id).order_by(Item.created_at.desc()).all()
    
    return render_template('register/profile.html', user=user, items=user_items)

# Создание объявления
@app.route('/create', methods=['GET', 'POST'])
def create():
    if 'user_id' not in session:
        flash('Для создания объявления необходимо войти в систему', 'error')
        return redirect('/login')
    
    if request.method == 'POST':
        item_type = request.form.get('item_type')
        category = request.form.get('category')
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        city = request.form.get('city', '').strip()
        location = request.form.get('location', '').strip()
        date_str = request.form.get('date')
        
        # Контактная информация
        contact_name = request.form.get('contact_name', '').strip()
        contact_phone = request.form.get('contact_phone', '').strip()
        contact_email = request.form.get('contact_email', '').strip()
        
        # Валидация
        if not title:
            flash('Введите заголовок объявления', 'error')
            return redirect('/create')
        
        if not category:
            flash('Выберите категорию', 'error')
            return redirect('/create')
        
        if not city:
            flash('Введите город', 'error')
            return redirect('/create')
        
        # Преобразование даты
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            date = datetime.now().date()
        
        # Создание объявления
        item_id = generate_item_id()
        
        new_item = Item(
            item_id=item_id,
            user_id=session['user_id'],
            item_type=item_type,
            category=category,
            title=title,
            description=description,
            city=city,
            location=location,
            date=date,
            contact_name=contact_name or session['full_name'],
            contact_phone=contact_phone,
            contact_email=contact_email
        )
        
        try:
            db.session.add(new_item)
            db.session.commit()
            
            flash(f'✅ Объявление создано! ID: {item_id}', 'success')
            return redirect('/search')
            
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка создания объявления: {e}")
            flash('Ошибка создания объявления', 'error')
            return redirect('/create')
    
    return render_template('create_ad/create.html')

# Поиск объявлений
@app.route('/search', methods=['GET', 'POST'])
def search():
    items = []
    search_query = ''
    category_filter = ''
    city_filter = ''
    
    if request.method == 'POST':
        search_query = request.form.get('search_query', '').strip()
        category_filter = request.form.get('category', '')
        city_filter = request.form.get('city', '')
        item_type_filter = request.form.get('item_type', '')
        
        # Построение запроса
        query = Item.query.filter_by(status='active')
        
        if search_query:
            query = query.filter(
                db.or_(
                    Item.title.ilike(f'%{search_query}%'),
                    Item.description.ilike(f'%{search_query}%'),
                    Item.category.ilike(f'%{search_query}%')
                )
            )
        
        if category_filter and category_filter != 'all':
            query = query.filter_by(category=category_filter)
        
        if city_filter and city_filter != 'all':
            query = query.filter_by(city=city_filter)
        
        if item_type_filter and item_type_filter != 'all':
            query = query.filter_by(item_type=item_type_filter)
        
        items = query.order_by(Item.created_at.desc()).all()
    else:
        # По умолчанию показываем последние 20 активных объявлений
        items = Item.query.filter_by(status='active').order_by(Item.created_at.desc()).limit(20).all()
    
    # Получаем уникальные категории и города для фильтров
    categories = db.session.query(Item.category).distinct().order_by(Item.category).all()
    cities = db.session.query(Item.city).distinct().order_by(Item.city).all()
    
    return render_template('search_item/search.html',
                         items=items,
                         search_query=search_query,
                         categories=[c[0] for c in categories],
                         cities=[c[0] for c in cities])

# Просмотр объявления
@app.route('/item/<string:item_id>')
def view_item(item_id):
    item = Item.query.filter_by(item_id=item_id).first_or_404()
    return render_template('search_item/contact.html', item=item)

# Удаление объявления
@app.route('/delete_item/<string:item_id>')
def delete_item(item_id):
    if 'user_id' not in session:
        flash('Необходимо войти в систему', 'error')
        return redirect('/login')
    
    item = Item.query.filter_by(item_id=item_id).first_or_404()
    
    # Проверка прав
    if item.user_id != session['user_id']:
        flash('У вас нет прав на удаление этого объявления', 'error')
        return redirect('/profile')
    
    try:
        db.session.delete(item)
        db.session.commit()
        flash('✅ Объявление удалено', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Ошибка при удалении объявления', 'error')
    
    return redirect('/profile')

# ===== ИНИЦИАЛИЗАЦИЯ =====

def init_db():
    """Создание таблиц в БД"""
    with app.app_context():
        # Создаем все папки для шаблонов
        templates_dirs = [
            '../front',
            '../front/register',
            '../front/create_ad',
            '../front/search_item'
        ]
        
        for dir_path in templates_dirs:
            os.makedirs(dir_path, exist_ok=True)
        
        # Создаем таблицы
        db.create_all()
        print("✅ База данных инициализирована")
        
        # Создаем тестового пользователя (опционально)
        if User.query.count() == 0:
            test_user = User(
                uid='USR-ADMIN',
                username='admin',
                full_name='Администратор Системы',
                password_hash=hash_password('admin123')
            )
            db.session.add(test_user)
            db.session.commit()
            print("✅ Создан тестовый пользователь: admin / admin123")

if __name__ == '__main__':
    init_db()
    print("\n" + "="*60)
    print("🚀 Сервер запущен: http://localhost:5000")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)