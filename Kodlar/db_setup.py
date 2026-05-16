import sqlite3
import hashlib

def setup_database():
    conn = sqlite3.connect('banka.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            action TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            failed_attempts INTEGER DEFAULT 0,
            is_locked INTEGER DEFAULT 0
        )
    ''')

    admin_hash = hashlib.sha256("1234".encode()).hexdigest()
    try:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES ('admin', ?)", (admin_hash,))
    except sqlite3.IntegrityError:
        cursor.execute("UPDATE users SET is_locked = 0, failed_attempts = 0 WHERE username = 'admin'") 

    conn.commit()
    conn.close()
    print("Veritabanı altyapısı ve log sistemi hazır.")

setup_database()