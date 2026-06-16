"""
Инициализация БД: создание таблиц, ролей, жанров и тестовых пользователей.
Запускать: python db_seed.py
"""
import sqlite3
import os
from werkzeug.security import generate_password_hash

DB = os.path.join(os.path.dirname(__file__), 'library.db')
SCHEMA = os.path.join(os.path.dirname(__file__), 'schema.sql')


def init():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')

    with open(SCHEMA, encoding='utf-8') as f:
        conn.executescript(f.read())

    # Роли
    roles = [
        ('администратор', 'Суперпользователь, полный доступ'),
        ('модератор', 'Может редактировать книги и модерировать рецензии'),
        ('пользователь', 'Может оставлять рецензии'),
    ]
    for name, desc in roles:
        conn.execute(
            'INSERT OR IGNORE INTO roles (name, description) VALUES (?,?)',
            (name, desc)
        )

    # Жанры
    genres = [
        'Фантастика', 'Фэнтези', 'Детектив', 'Роман', 'Приключения',
        'Ужасы', 'Исторический', 'Научная литература', 'Биография', 'Поэзия'
    ]
    for g in genres:
        conn.execute('INSERT OR IGNORE INTO genres (name) VALUES (?)', (g,))

    # Тестовые пользователи
    users = [
        ('admin', 'admin123', 'Деев', 'Егор', 'Викторович', 'администратор'),
        ('moder', 'moder123', 'Иванов', 'Иван', 'Иванович', 'модератор'),
        ('user1', 'user123', 'Петров', 'Пётр', None, 'пользователь'),
    ]
    for login, pwd, last, first, middle, role_name in users:
        role = conn.execute('SELECT id FROM roles WHERE name=?', (role_name,)).fetchone()
        if role:
            conn.execute(
                '''INSERT OR IGNORE INTO users
                   (login, password_hash, last_name, first_name, middle_name, role_id)
                   VALUES (?,?,?,?,?,?)''',
                (login, generate_password_hash(pwd), last, first, middle, role['id'])
            )

    conn.commit()
    conn.close()
    print('БД инициализирована.')
    print('Логины: admin/admin123, moder/moder123, user1/user123')


if __name__ == '__main__':
    init()
