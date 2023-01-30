"""Работа с базой данных"""
import datetime
import os
import sqlite3
from sqlite3 import IntegrityError

from strings import DB_CATEGORY_EXIST, DB_CATEGORY_CREATE

conn = sqlite3.connect(os.path.join("expense.db"))
cursor = conn.cursor()


def create_user(user_id: int, user_name: str):
    """Добавляет в БД нового юзера"""
    try:
        cursor.execute("INSERT INTO user(user_id, user_name)  VALUES (?,?)", (user_id, user_name))
        conn.commit()
    except IntegrityError:  # если такой юзер уже есть
        pass


def create_category(name: str, user_id: int) -> str:
    """Создает новую категорию"""
    # проверяем сначала есть ли уже такая категория
    cursor.execute("SELECT id FROM category WHERE name=? and user_id=?", (name, user_id))
    if cursor.fetchone():
        return DB_CATEGORY_EXIST
    else:
        cursor.execute("INSERT INTO category(name, user_id) VALUES (?, ?)", (name, user_id))
        conn.commit()
        return DB_CATEGORY_CREATE


def get_all_name_category(user_id: int) -> list | None:
    """Получает все категории для отображения в /categories"""
    cursor.execute("SELECT name FROM category WHERE user_id=?", (user_id,))
    _all_category = cursor.fetchall()
    if _all_category:
        return _fetchall_to_list(_all_category)


def get_date(category_name: str, user_id: int) -> list | None:
    """Получает все даты, в которых были расходы в данной категории category_name"""
    cursor.execute(
        "SELECT DISTINCT created FROM expense WHERE category=("
        "SELECT id from category WHERE name=? AND user_id=?)"
        " AND user_id=?",
        (category_name, user_id, user_id))
    _all_date = cursor.fetchall()
    if _all_date:
        return _fetchall_to_list(_all_date)


def get_expense(date: str, category: str, user_id: int):
    """Все расходы за определенную дату date в категории category"""
    cursor.execute(
        'SELECT expense_value FROM expense WHERE user_id=? AND created=? AND category=('
        'SELECT id from category WHERE name=? AND user_id=?)',
        (user_id, date, category, user_id))
    _all_expense = cursor.fetchall()
    if _all_expense:
        return _fetchall_to_list(_all_expense)


def del_expense(value: str, category: str, user_id: int) -> None:
    """Удаляет expense по дате и категории"""
    cursor.execute(
        'SELECT id FROM expense WHERE expense_value=? AND category=('
        'SELECT id from category WHERE name=? AND user_id=?)'
        ' AND user_id=?',
        (value, category, user_id, user_id))
    _expense_id = cursor.fetchone()[0]
    cursor.execute('DELETE FROM expense WHERE id=?', (_expense_id,))
    conn.commit()


def add_expense(value: int, category: str, user_id: int) -> None:
    """Добавляет новую запись expense"""
    cursor.execute(
        'INSERT INTO expense(expense_value, created, category, user_id) VALUES (?,?,(SELECT id from category WHERE name=? AND user_id=?),?)',
        (value, datetime.date.today(), category, user_id, user_id))
    conn.commit()


def total_expense(user_id: int) -> int:
    """Все расходы пользователя за все время"""
    cursor.execute('SELECT SUM(expense_value) FROM expense WHERE user_id=?', (user_id,))
    _total = cursor.fetchone()[0]
    if not _total:
        return 0
    return _total


def statistic(user_id: int) -> list:
    """Статистика за день"""
    cursor.execute(
        'SELECT name, SUM(expense_value)  FROM category JOIN expense WHERE expense.category=category.id '
        'GROUP BY name HAVING category.user_id=? AND created=?',
        (user_id, datetime.date.today()))
    _statisctic = cursor.fetchall()
    return _statisctic


def get_all_user_id() -> list:
    """Все user_id в БД для рассылки статистики"""
    cursor.execute('SELECT user_id from user')
    _all_id = cursor.fetchall()
    return _fetchall_to_list(_all_id)


def _init_db():
    """Инициализирует БД"""
    with open("create_db.sql", "r") as f:
        sql = f.read()
    cursor.executescript(sql)
    conn.commit()


def _fetchall_to_list(query: list) -> list:
    """Переделывает [(513781754,),] в [513781754]"""
    fetchall_list = [_[0] for _ in query]
    return fetchall_list


def check_db_exists():
    """Проверяет, инициализирована ли БД, если нет — инициализирует"""
    cursor.execute("SELECT name FROM sqlite_master "
                   "WHERE type='table' AND name='category'")
    table_exists = cursor.fetchall()
    if table_exists:
        return
    _init_db()


check_db_exists()
