import sqlite3
import config

db = sqlite3.connect('users_database')
cursor = db.cursor()


def init_table():
    cursor.execute('''CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY UNIQUE NOT NULL,
    user_id INTEGER UNIQUE NOT NULL,
    name STRING,
    second_name STRING,
    nickname STRING,
    choosen_amount INTEGER,
    left_days INTEGER CHECK(left_days >= 0)
    )''')


def add_user_to_db(entity):
    cursor.execute('INSERT OR IGNORE INTO users(user_id, name, second_name, nickname, left_days) VALUES('
                   '?, ?, ?, ?, ?)', (entity.id,
                                      entity.first_name,
                                      entity.last_name,
                                      entity.username,
                                      config.trial_limit
                                      ))
    db.commit()


def add_days_to_user(user_id):
    cursor.execute('SELECT choosen_amount FROM users WHERE user_id = ?', (user_id, ))
    days = int(cursor.fetchone()[0])
    cursor.execute('UPDATE OR REPLACE users SET left_days = left_days + ? WHERE user_id = ?', (days, user_id))
    db.commit()


def daytimer():
    cursor.execute('UPDATE or ignore users set left_days = left_days - 1')
    db.commit()


def how_much_days_left(user_id):
    cursor.execute('SELECT left_days FROM users WHERE user_id = ?', (user_id, ))
    days = cursor.fetchone()[0]
    return days


def get_user_info(user_id):
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id, ))
    info = cursor.fetchone()
    return info


def choosen_amount(amount, user_id):
    cursor.execute('UPDATE OR REPLACE users SET choosen_amount = ? WHERE user_id = ?', (amount, user_id))
    db.commit()
