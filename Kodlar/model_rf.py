import pandas as pd
import sqlite3
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

conn = sqlite3.connect('banka.db')
df = pd.read_sql("SELECT * FROM customers", conn)
conn.close()

X = df[['credit_score', 'age', 'tenure', 'balance', 'products_number', 'credit_card', 'active_member', 'estimated_salary']]
y = df['churn']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
print("Random Forest (Churn Modeli) eğitimi başladı...")
rf_model.fit(X_train, y_train)

y_pred = rf_model.predict(X_test)
dogruluk = accuracy_score(y_test, y_pred)

print("\n" + "="*40)
print("=== RANDOM FOREST MODEL DEĞERLENDİRMESİ ===")
print(f"Modelin Doğruluk Oranı (Accuracy): %{dogruluk * 100:.2f}")
print("="*40)
print("\nDetaylı Sınıflandırma Raporu:")
print(classification_report(y_test, y_pred))
print("="*40)

joblib.dump(rf_model, 'rf_churn_model.pkl')
print("\nBaşarılı: rf_churn_model.pkl test edilerek oluşturuldu!")