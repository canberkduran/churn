import sqlite3
from faker import Faker
import random

fake = Faker('tr_TR')

conn = sqlite3.connect('banka.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE customers ADD COLUMN first_name TEXT")
    cursor.execute("ALTER TABLE customers ADD COLUMN last_name TEXT")
    cursor.execute("ALTER TABLE customers ADD COLUMN phone_number TEXT")
    print("Sütunlar başarıyla eklendi.")
except sqlite3.OperationalError:
    print("veriler güncelleniyor")

cursor.execute("SELECT customer_id FROM customers")
ids = cursor.fetchall()

for (c_id,) in ids:
    f_name = fake.first_name()
    l_name = fake.last_name()
    phone = f"05{random.randint(30, 55)}{random.randint(100, 999)}{random.randint(10, 99)}{random.randint(10, 99)}"
    
    cursor.execute("""
        UPDATE customers 
        SET first_name = ?, last_name = ?, phone_number = ? 
        WHERE customer_id = ?
    """, (f_name, l_name, phone, c_id))

conn.commit()
conn.close()
print("10.000 müşteri için isim ve telefon bilgileri başarıyla oluşturuldu!")