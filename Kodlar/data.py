import pandas as pd
import sqlite3

df = pd.read_csv('Bank Customer Churn Prediction.csv')

print(df.columns)

df = df.dropna()

if 'customer_id' in df.columns:
    df['customer_id'] = df['customer_id'].apply(lambda x: str(x)[:4] + "****")

conn = sqlite3.connect('banka.db')
cursor = conn.cursor()

df.to_sql('customers', conn, if_exists='replace', index=False)

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT,
        failed_attempts INTEGER DEFAULT 0,
        is_locked INTEGER DEFAULT 0
    )
''')

try:
    cursor.execute("INSERT INTO users (username, password_hash) VALUES ('admin', '1234')")
except:
    pass 

conn.commit()
conn.close()

print("İşlem Başarili")