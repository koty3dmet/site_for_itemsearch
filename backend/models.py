from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    """Модель пользователя"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(10), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связь с объявлениями
    items = db.relationship('Item', backref='author', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username} ({self.full_name})>'

class Item(db.Model):
    """Модель объявления (потерянной/найденной вещи)"""
    __tablename__ = 'items'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.String(10), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Основная информация
    item_type = db.Column(db.String(10), nullable=False)  # 'lost' или 'found'
    category = db.Column(db.String(50), nullable=False)   # категория
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Место и время
    city = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200))  # конкретное место
    date = db.Column(db.Date, nullable=False)
    
    # Контактная информация
    contact_name = db.Column(db.String(100))
    contact_phone = db.Column(db.String(20))
    contact_email = db.Column(db.String(100))
    
    # Технические поля
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')  # active, closed, returned
    
    def __repr__(self):
        return f'<Item {self.item_id}: {self.title}>'

class PlatformStats(db.Model):
    """Модель для хранения статистики платформы"""
    __tablename__ = 'platform_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Основная статистика
    total_users = db.Column(db.Integer, default=0)  # количество пользователей
    active_items = db.Column(db.Integer, default=0)  # активные объявления
    found_items = db.Column(db.Integer, default=0)   # найденные/возвращенные вещи
    total_items = db.Column(db.Integer, default=0)   # всего объявлений за все время
    
    # Дополнительная статистика (по желанию)
    lost_items = db.Column(db.Integer, default=0)    # потерянных вещей
    found_items_reported = db.Column(db.Integer, default=0)  # найденных вещей
    
    # Временные метки
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PlatformStats: {self.total_users} users, {self.active_items} active items>'
    
    def update_stats(self, db_session, Item, User):
        """Обновление статистики на основе текущих данных в БД"""
        self.total_users = User.query.count()
        self.active_items = Item.query.filter_by(status='active').count()
        self.found_items = Item.query.filter_by(status='returned').count()
        self.total_items = Item.query.count()
        self.lost_items = Item.query.filter_by(item_type='lost').count()
        self.found_items_reported = Item.query.filter_by(item_type='found').count()
        self.last_updated = datetime.utcnow()
        
        db_session.add(self)
        db_session.commit()
    
    def increment_found_items(self, db_session):
        """Увеличивает счетчик найденных вещей (при нажатии кнопки)"""
        self.found_items += 1
        self.last_updated = datetime.utcnow()
        db_session.add(self)
        db_session.commit()
    
    @classmethod
    def get_current_stats(cls):
        """Получение текущей статистики или создание новой записи"""
        stats = cls.query.first()
        if not stats:
            stats = PlatformStats()
            db.session.add(stats)
            db.session.commit()
        return stats