import os
import sqlite3
import json
import shutil
import datetime
from crypto import encrypt_password, decrypt_password

DB_PATH = os.path.join(os.path.expanduser("~"), ".passman.db")


# Инициализация базы данных
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY,
            service TEXT UNIQUE NOT NULL,  -- UNIQUE ограничение
            username TEXT NOT NULL,
            encrypted_password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def add_password(service, username, password, key):
    encrypted_password = encrypt_password(password, key)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO passwords (service, username, encrypted_password) VALUES (?, ?, ?)",
                       (service, username, encrypted_password))
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"Сервис '{service}' уже существует. Используйте редактирование.")
    finally:
        conn.close()

def get_password(service, key):  # Убраны параметр username
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username, encrypted_password FROM passwords WHERE service=?", (service,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            'username': row[0],
            'password': decrypt_password(row[1], key)
        }
    return None



# Новые функции для обновления и удаления
def update_password(service, new_password, key):
    encrypted_password = encrypt_password(new_password, key)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE passwords SET encrypted_password=? WHERE service=?",
                   (encrypted_password, service))
    conn.commit()
    conn.close()

def delete_password(service):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM passwords WHERE service=?", (service,))
    conn.commit()
    conn.close()

# Бэкап базы данных
def backup_db():
    backup_file = f"passwords_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy(DB_PATH, backup_file)
    print(f"Бэкап создан: {backup_file}")


# Экспорт данных в JSON
def export_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT service, username, encrypted_password FROM passwords")
    data = [{"service": row[0], "username": row[1], "password": row[2]} for row in cursor.fetchall()]
    conn.close()

    with open("export.json", "w") as f:
        json.dump(data, f, indent=4)
    print("Данные экспортированы в export.json")

def get_all_services():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT service FROM passwords")
    services = [row[0] for row in cursor.fetchall()]
    conn.close()
    return services

def get_users_by_service(service):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM passwords WHERE service=?", (service,))
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users


# Импорт данных из JSON
def import_data():
    with open("export.json", "r") as f:
        data = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for entry in data:
        cursor.execute("INSERT INTO passwords (service, username, encrypted_password) VALUES (?, ?, ?)",
                       (entry["service"], entry["username"], entry["password"]))
    conn.commit()
    conn.close()
    print("Данные импортированы.")