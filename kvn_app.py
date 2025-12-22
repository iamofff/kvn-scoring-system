import streamlit as st
import pandas as pd
import io
import sqlite3
import time

# --- НАСТРОЙКИ СТРАНИЦЫ ---
st.set_page_config(page_title="КВН СУПЕР-ПРО", layout="wide", initial_sidebar_state="expanded")

# --- БАЗА ДАННЫХ (Пункт 3: Сохранение) ---
def init_db():
    conn = sqlite3.connect('kvn_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS scores 
                 (contest TEXT, team TEXT, judge_id INTEGER, score REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS config 
                 (key TEXT PRIMARY KEY, value TEXT)''')
    conn.commit()
    return conn

conn = init_db()

def save_score(contest, team, j_id, val):
    c = conn.cursor()
    c.execute("REPLACE INTO scores (contest, team, judge_id, score) VALUES (?, ?, ?, ?)", 
              (contest, team, j_id, val))
    conn.commit()

def load_scores():
    return pd.read_sql("SELECT * FROM scores", conn)

# --- ГЛОБАЛЬНОЕ СОСТОЯНИЕ ---
if 'teams' not in st.session_state:
    st.session_state.teams = ["Команда 1", "Команда 2", "Команда 3", "Команда 4"]
if 'contests' not in st.session_state:
    st.session_state.contests = ["Приветствие", "Разминка", "СТЭМ", "Музыкалка"]
if 'judges' not in st.session_state:
    st.session_state.judges = ["Судья 1", "Судья 2", "Судья 3", "Судья 4", "Судья 5"]

# --- АВТОРИЗАЦИЯ (Пункт 2: Пароли) ---
st.sidebar.title("🔐 Вход в систему")
password = st.sidebar.text_input("Введите пароль доступа:", type="password")

# Простые пароли для примера
ADMIN_PWD = "admin"
JUDGE_PWD = "kvn"

if password not in [ADMIN_PWD, JUDGE_PWD]:
    st.warning("Пожалуйста, введите пароль в боковой панели для доступа к системе.")
    st.stop()

# --- ОСНОВНОЕ МЕНЮ ---
role = st.sidebar.radio("Перейти к:", ["📱 Судейство", "📊 Табло для зала", "🕵️ Детальный отчет", "⚙️ Настройки (Админ)"])

# --- ПУНКТ 5: ТАЙМЕР РАЗМИНКИ ---
def run_timer():
    placeholder = st.empty()
    for i in range(30, -1, -1):
        placeholder.metric("Осталось времени", f"{i} сек")
        time.sleep(1)
    st.balloons()
    st.error("ВРЕМЯ ВЫШЛО!")

# --- ИНТЕРФЕЙС СУДЬИ ---
if role == "📱 Судейство":
    judge_name = st.sidebar.selectbox("Ваше имя:", st.session_state.judges)
    judge_idx = st.session_state.judges.index(judge_name)
    contest = st.selectbox("Текущий конкурс:", st.session_state.contests)
    
    st.subheader(f"Оценочный лист: {judge_name}")
    
    # Загружаем существующие оценки из БД
    db_df = load_scores()
    
    with st.form("judge_form"):
        for team in st.session_state.teams:
            # Ищем оценку в БД
            mask = (db_df['contest'] == contest) & (db_df['team'] == team) & (db_df['judge_id'] == judge_idx)
            val = db_df[mask]['score'].values[0] if not db_df[mask].empty else 0.0
            
            st.write(f"**{team}**")
            score = st.radio(f"Балл для {team}", [0.0, 1.0, 2.0, 3.0, 4.0, 5.0], 
                             index=[0.0, 1.0, 2.0, 3.0, 4.0, 5.0].index(val), 
                             horizontal=True, key=f"s_{team}")
            if st.form_submit_button(f"Сохранить {team}"):
                save_score(contest, team, judge_idx, score)
                st.success(f"Оценка для {team} сохранена!")

# --- ПУНКТ 1: ВИЗУАЛИЗАЦИЯ ДЛЯ ЗАЛА ---
elif role == "📊 Табло для зала":
    st.header("🏆 ТЕКУЩИЙ РЕЙТИНГ КОМАНД")
    
    # Олимпийская система (Пункт 4)
    use_olympic = st.sidebar.checkbox("Олимпийская система (без min/max)")
    
    db_df = load_scores()
    results = []
    for team in st.session_state.teams:
        row = {"Команда": team}
        total = 0
        for c in st.session_state.contests:
            marks = [db_df[(db_df['contest']==c) & (db_df['team']==team) & (db_df['judge_id']==i)]['score'].values[0] 
                     if not db_df[(db_df['contest']==c) & (db_df['team']==team) & (db_df['judge_id']==i)].empty else 0.0 
                     for i in range(len(st.session_state.judges))]
            
            if use_olympic and len(marks) > 2:
                marks.sort()
                calc_marks = marks[1:-1] # Убираем первый и последний
                avg = sum(calc_marks) / len(calc_marks)
            else:
                avg = sum(marks) / len(marks) if marks else 0
            
            total += avg
        row["Сумма"] = round(total, 2)
        results.append(row)
    
    res_df = pd.DataFrame(results).sort_values(by="Сумма", ascending=False)
    
    # Красивый график (Пункт 1)
    st.bar_chart(res_df.set_index("Команда")["Сумма"])
    st.table(res_df)
    
    if st.button("⏱️ Запустить таймер разминки (30 сек)"):
        run_timer()

# --- ДЕТАЛЬНЫЙ ОТЧЕТ ---
elif role == "🕵️ Детальный отчет":
    st.header("Полная ведомость")
    db_df = load_scores()
    st.dataframe(db_df)
    
    buffer = io.BytesIO()
    db_df.to_excel(buffer, index=False)
    st.download_button("📥 Скачать БД в Excel", buffer.getvalue(), "kvn_db.xlsx")

# --- НАСТРОЙКИ (АДМИН) ---
elif role == "⚙️ Настройки (Админ)":
    if password != ADMIN_PWD:
        st.error("Доступ только для Администратора!")
    else:
        st.session_state.teams = st.text_area("Команды (через запятую)", ",".join(st.session_state.teams)).split(",")
        st.session_state.judges = st.text_area("Судьи (через запятую)", ",".join(st.session_state.judges)).split(",")
        st.session_state.contests = st.text_area("Конкурсы (через запятую)", ",".join(st.session_state.contests)).split(",")
        if st.button("Обновить конфигурацию"):
            st.success("Настройки обновлены!")

if st.sidebar.button("🧹 Очистить базу данных"):
    if password == ADMIN_PWD:
        c = conn.cursor()
        c.execute("DELETE FROM scores")
        conn.commit()
        st.rerun()
