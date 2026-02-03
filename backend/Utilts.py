from datetime import datetime, timedelta
from models import db, PlatformStats, Item, User

def update_platform_stats():
    """Обновляет статистику платформы"""
    stats = PlatformStats.get_current_stats()
    stats.update_stats(db.session, Item, User)
    return stats

def get_platform_stats():
    """Получает текущую статистику платформы"""
    return PlatformStats.get_current_stats()

def get_basic_stats():
    """Получает базовую статистику для отображения на сайте"""
    stats = PlatformStats.get_current_stats()
    
    # Форматируем дату для красивого отображения
    if stats.last_updated:
        time_diff = datetime.utcnow() - stats.last_updated
        if time_diff < timedelta(minutes=1):
            time_ago = "только что"
        elif time_diff < timedelta(hours=1):
            minutes = int(time_diff.total_seconds() / 60)
            time_ago = f"{minutes} минут назад"
        elif time_diff < timedelta(days=1):
            hours = int(time_diff.total_seconds() / 3600)
            time_ago = f"{hours} часов назад"
        else:
            time_ago = stats.last_updated.strftime('%d.%m.%Y %H:%M')
    else:
        time_ago = "никогда"
    
    return {
        'total_users': stats.total_users,
        'active_items': stats.active_items,
        'found_items': stats.found_items,
        'total_items': stats.total_items,
        'lost_items': stats.lost_items,
        'found_items_reported': stats.found_items_reported,
        'last_updated': stats.last_updated,
        'time_ago': time_ago
    }

def increment_found_counter():
    """Увеличивает счетчик найденных вещей"""
    stats = PlatformStats.get_current_stats()
    stats.increment_found_items(db.session)
    return stats.found_items

def get_daily_stats():
    """Получает статистику за последние 7 дней"""
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    # Новые пользователи за 7 дней
    new_users = User.query.filter(User.created_at >= seven_days_ago).count()
    
    # Новые объявления за 7 дней
    new_items = Item.query.filter(Item.created_at >= seven_days_ago).count()
    
    # Найденные вещи за 7 дней
    found_items = Item.query.filter(
        Item.status == 'returned',
        Item.created_at >= seven_days_ago
    ).count()
    
    return {
        'new_users_7days': new_users,
        'new_items_7days': new_items,
        'found_items_7days': found_items
    }

def get_category_stats():
    """Статистика по категориям"""
    from sqlalchemy import func
    
    categories = db.session.query(
        Item.category, 
        func.count(Item.id).label('count')
    ).filter_by(status='active')\
     .group_by(Item.category)\
     .order_by(func.count(Item.id).desc())\
     .all()
    
    return categories

def get_city_stats():
    """Статистика по городам"""
    from sqlalchemy import func
    
    cities = db.session.query(
        Item.city, 
        func.count(Item.id).label('count')
    ).filter_by(status='active')\
     .group_by(Item.city)\
     .order_by(func.count(Item.id).desc())\
     .all()
    
    return cities