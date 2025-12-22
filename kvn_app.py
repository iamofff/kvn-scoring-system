import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- НАСТРОЙКИ ---
st.set_page_config(page_title="КВН LIVE", layout="wide")

# Подключение через секреты
@st.cache_resource
def get_gsheet_client():
    # Читаем данные из Secrets
    info = st.secrets["gcp_service_account"]
    credentials = Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return gspread.authorize(credentials)

client = get_gsheet_client()
# Вставьте имя ВАШЕЙ таблицы здесь
SHEET_NAME = "KVN_Live" 
sheet = client.open(SHEET_NAME).sheet1

# --- ФУНКЦИИ ---
def load_data():
    data = sheet.get_all_records()
    return pd.DataFrame(data)

def update_data(df):
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())

# --- ИНТЕРФЕЙС ---
# (Используйте логику ролей: Судья, Табло, Настройки из предыдущих ответов)
# Для записи оценки используйте:
# df = load_data()
# ... манипуляции с df ...
# update_data(df)

st.title("🏆 КВН: Система с облачной синхронизацией")
st.info("Данные синхронизируются через Google Sheets")

# Пример вывода табло
if st.button("🔄 Обновить результаты"):
    df = load_data()
    st.table(df)
