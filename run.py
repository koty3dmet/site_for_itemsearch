#!/usr/bin/env python3
"""
Файл для запуска приложения
"""

import sys
import os

# Добавляем backend в путь
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from main import app, init_db

if __name__ == '__main__':
    # Инициализируем БД
    init_db()
    
    print("\n" + "="*60)
    print("🚀 Сервер запущен: http://localhost:5000")
    print("="*60 + "\n")
    
    # Запускаем приложение
    app.run(debug=True, host='0.0.0.0', port=5000)