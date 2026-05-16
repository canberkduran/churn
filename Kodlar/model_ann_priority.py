import pandas as pd
import numpy as np
import joblib
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.preprocessing import StandardScaler
import sqlite3

conn = sqlite3.connect('banka.db')
df = pd.read_sql("SELECT * FROM customers", conn)
conn.close()

try:
    rf = joblib.load('rf_churn_model.pkl')
except:
    print("HATA: rf_churn_model.pkl bulunamadı! Önce model_rf.py dosyasını çalıştırın.")
    exit()

features_rf = ['credit_score', 'age', 'tenure', 'balance', 'products_number', 'credit_card', 'active_member', 'estimated_salary']
X_rf = df[features_rf]

churn_probs = rf.predict_proba(X_rf)[:, 1]

X_ann = np.column_stack((churn_probs, df['balance'], df['estimated_salary'], df['products_number']))
priority_labels = (churn_probs * 0.6) + (df['balance'] / df['balance'].max() * 0.4)

X_train, X_test, y_train, y_test = train_test_split(X_ann, priority_labels, test_size=0.2, random_state=42)

scaler_ann = StandardScaler()
X_train_scaled = scaler_ann.fit_transform(X_train)
X_test_scaled = scaler_ann.transform(X_test)

ann_priority = MLPRegressor(hidden_layer_sizes=(128, 64, 32, 16), 
                            activation='relu', 
                            solver='adam', 
                            max_iter=1000, 
                            random_state=42)

print("Yapay Sinir Ağı (ANN Öncelik Modeli) eğitimi başladı...")
ann_priority.fit(X_train_scaled, y_train)

y_pred = ann_priority.predict(X_test_scaled)
r2 = r2_score(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)

print("\n" + "="*40)
print("=== YAPAY SİNİR AĞI (ANN) MODEL DEĞERLENDİRMESİ ===")
print(f"R2 Skor (Belirlenme Katsayısı): %{r2 * 100:.2f}")
print(f"Ortalama Mutlak Hata (MAE): {mae:.4f}")
print(f"Ortalama Kare Hata (MSE): {mse:.4f}")
print("="*40)

joblib.dump(ann_priority, 'ann_priority_model.pkl')
joblib.dump(scaler_ann, 'scaler_ann.pkl')  # Arayüzün kullanması için scaler'ı da paketliyoruz
print("\nBaşarılı: ann_priority_model.pkl ve scaler_ann.pkl test edilerek oluşturuldu!")