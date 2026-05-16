import streamlit as st
import sqlite3
import hashlib
import pandas as pd
import joblib
import numpy as np
import time
import random  

st.set_page_config(page_title="Banka Karar Destek ", layout="wide")

# --- CSS ENJEKSİYONU  ---
st.markdown("""
    <style>
    /* Streamlit'in sayı giriş alanlarındaki + ve - butonlarını tamamen gizler */
    button[data-testid="stNumberInputStepUp"], 
    button[data-testid="stNumberInputStepDown"] {
        display: none !important;
    }
    /* Butonlar gizlenince oluşan sağ boşluğu dengeler */
    div[data-testid="stNumberInput"] input {
        padding-right: 12px !important;
    }
    /* Tarayıcıların kendi varsayılan yukarı/aşağı oklarını temizler */
    input[type=number]::-webkit-inner-spin-button, 
    input[type=number]::-webkit-outer-spin-button {
        -webkit-appearance: none;
        margin: 0;
    }
    input[type=number] {
        -moz-appearance: textfield;
    }
    </style>
""", unsafe_allow_html=True)

try:
    rf_model = joblib.load('rf_churn_model.pkl')
    ann_model = joblib.load('ann_priority_model.pkl')
    scaler_ann = joblib.load('scaler_ann.pkl')
except:
    st.error("Model dosyaları (pkl) bulunamadı! Lütfen önce eğitim dosyalarını çalıştırın.")

def save_log(username, action):
    conn = sqlite3.connect('banka.db')
    c = conn.cursor()
    c.execute("INSERT INTO logs (username, action) VALUES (?, ?)", (username, action))
    conn.commit()
    conn.close()

def hash_sifre(sifre):
    return hashlib.sha256(str.encode(sifre)).hexdigest()

def giris_kontrol(kullanici, sifre):
    conn = sqlite3.connect('banka.db')
    c = conn.cursor()
    c.execute("SELECT password_hash, failed_attempts, is_locked FROM users WHERE username=?", (kullanici,))
    user = c.fetchone()
    
    if not user:
        conn.close()
        return "yok"
    
    p_hash, failed, locked = user
    if locked == 1:
        conn.close()
        return "kilitli"
    
    if p_hash == hash_sifre(sifre):
        c.execute("UPDATE users SET failed_attempts = 0 WHERE username=?", (kullanici,))
        conn.commit()
        conn.close()
        return "basarili"
    else:
        new_failed = failed + 1
        if new_failed >= 3:
            c.execute("UPDATE users SET is_locked = 1 WHERE username=?", (kullanici,))
        else:
            c.execute("UPDATE users SET failed_attempts = ? WHERE username=?", (new_failed, kullanici))
        conn.commit()
        conn.close()
        return "hatali"

def musterileri_getir_hibrit():
    conn = sqlite3.connect('banka.db')
    df = pd.read_sql("SELECT * FROM customers", conn)
    conn.close()

    features_rf = ['credit_score', 'age', 'tenure', 'balance', 'products_number', 'credit_card', 'active_member', 'estimated_salary']
    churn_probs = rf_model.predict_proba(df[features_rf])[:, 1]

    X_ann = np.column_stack((churn_probs, df['balance'], df['estimated_salary'], df['products_number']))
    X_ann_scaled = scaler_ann.transform(X_ann)
    
    priority_scores = ann_model.predict(X_ann_scaled)
    df['Oncelik_Skoru'] = (priority_scores * 100).round(2)

    df['Müşteri ID'] = df['customer_id'].astype(str).apply(lambda x: x[:4] + "****")
    df['Müşteri'] = df['first_name'] + " " + df['last_name'].str[0] + "***"
    
    return df.sort_values(by='Oncelik_Skoru', ascending=False)

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'last_request_time' not in st.session_state:
    st.session_state['last_request_time'] = 0
if 'last_added_customer' not in st.session_state:
    st.session_state['last_added_customer'] = None

if not st.session_state['logged_in']:
    st.title("🏦 Bankacı Paneli")
    with st.form("login"):
        user_input = st.text_input("Kullanıcı Adı")
        pwd_input = st.text_input("Şifre", type="password")
        if st.form_submit_button("Giriş Yap"):
            status = giris_kontrol(user_input, pwd_input)
            if status == "basarili":
                st.session_state['logged_in'] = True
                st.session_state['user'] = user_input
                save_log(user_input, "Sisteme giriş yapıldı")
                st.rerun()
            elif status == "kilitli":
                st.error("Hesap kilitli! Güvenlik nedeniyle erişim reddedildi.")
            else:
                st.error("Hatalı giriş denemesi!")

else:
    st.sidebar.title(f"Hoş Geldin, {st.session_state['user']}")
    if st.sidebar.button("Güvenli Çıkış"):
        save_log(st.session_state['user'], "Sistemden çıkış yapıldı")
        st.session_state['logged_in'] = False
        st.session_state['last_added_customer'] = None
        st.rerun()

    menu = st.tabs(["📊 Analiz Paneli", "➕ Yeni Müşteri Ekle", "📜 Sistem Logları"])

    with menu[0]:
        st.subheader("Stratejik Müdahale Listesi (Hibrit Model)")
        data_all = musterileri_getir_hibrit()
        top_10 = data_all.head(10)
        
        c1, c2 = st.columns(2)
        c1.metric("Toplam VIP Müşteri", len(data_all))
        c2.metric("Ortalama VIP Skoru", f"{data_all['Oncelik_Skoru'].mean():.2f}")

        st.dataframe(top_10[['Müşteri ID', 'Müşteri', 'phone_number', 'balance', 'Oncelik_Skoru']].rename(
            columns={'phone_number': 'Telefon', 'balance': 'Bakiye (TL)', 'Oncelik_Skoru': 'Puan'}),
            use_container_width=True, hide_index=True)

    with menu[1]:
        st.subheader("Müşteri Kaydı ve Anlık Skorlama")
        with st.form("new_customer"):
            col1, col2 = st.columns(2)
            with col1:
                f_name = st.text_input("İsim")
                l_name = st.text_input("Soyisim")
                c_score = st.number_input("Kredi Skoru", 300, 850, 600)
                age = st.number_input("Yaş", 18, 100, 35)
                tenure = st.slider("Çalışma Yılı (Tenure)", 0, 10, 5)
            with col2:
                balance = st.number_input("Hesap Bakiyesi", 0.0, 1000000.0, 10000.0)
                prods = st.selectbox("Ürün Sayısı", [1, 2, 3, 4])
                salary = st.number_input("Tahmini Maaş", 0.0, 500000.0, 20000.0)
                active = st.checkbox("Aktif Üyelik")
                card = st.checkbox("Kredi Kartı Mevcut")
            
            submit = st.form_submit_button("Sisteme İşle ve Puanla")

        if submit:
            if time.time() - st.session_state['last_request_time'] < 5:
                st.warning("Lütfen işlemler arasında 5 saniye bekleyin.")
            else:
                st.session_state['last_request_time'] = time.time()
                
                new_df = pd.DataFrame([{
                    'credit_score': c_score, 'age': age, 'tenure': tenure, 'balance': balance,
                    'products_number': prods, 'credit_card': int(card), 'active_member': int(active),
                    'estimated_salary': salary
                }])
                
                p_churn = rf_model.predict_proba(new_df)[:, 1]
                X_ann_new = np.column_stack((p_churn, balance, salary, prods))
                X_ann_new_scaled = scaler_ann.transform(X_ann_new)
                
                new_score = round(ann_model.predict(X_ann_new_scaled)[0] * 100, 2)
                
                all_scores = data_all['Oncelik_Skoru'].tolist()
                all_scores.append(new_score)
                all_scores.sort(reverse=True)
                rank = all_scores.index(new_score) + 1
                
                new_id = random.randint(15600000, 15699999)
                fake_phone = f"05{random.randint(30, 55)}{random.randint(100, 999)}{random.randint(10, 99)}{random.randint(10, 99)}"
                
                conn = sqlite3.connect('banka.db')
                c = conn.cursor()
                c.execute("""
                    INSERT INTO customers 
                    (customer_id, first_name, last_name, credit_score, age, tenure, balance, 
                     products_number, credit_card, active_member, estimated_salary, phone_number, churn)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """, (new_id, f_name, l_name, c_score, age, tenure, balance, 
                      prods, int(card), int(active), salary, fake_phone))
                conn.commit()
                conn.close()
                
                st.session_state['last_added_customer'] = {
                    'f_name': f_name,
                    'l_name': l_name,
                    'new_score': new_score,
                    'rank': rank
                }
                
                save_log(st.session_state['user'], f"Müşteri eklendi: {f_name}, Skor: {new_score}")
                
                st.rerun()

        if st.session_state['last_added_customer'] is not None:
            info = st.session_state['last_added_customer']
            st.success(f"Müşteri {info['f_name']} {info['l_name'][0]}*** başarıyla veritabanına eklendi.")
            
            c_res1, c_res2 = st.columns(2)
            c_res1.metric("Hesaplanan Öncelik Puanı", info['new_score'])
            c_res2.metric("Genel Sıralama", f"{info['rank']}. Sırada")

    with menu[2]:
        st.subheader("Güvenlik ve İşlem Kayıtları")
        conn = sqlite3.connect('banka.db')
        logs = pd.read_sql("SELECT * FROM logs ORDER BY timestamp DESC LIMIT 100", conn)
        conn.close()
        st.table(logs)