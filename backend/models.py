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