import streamlit as st
import pandas as pd
import sqlite3
import io
import time

# --- НАСТРОЙКИ СТРАНИЦЫ ---
st.set_page_config(page_title="КВН LIVE: Система судейства", layout="wide")

# --- ИНИЦИАЛИЗАЦИЯ СОСТОЯНИЯ АВТОРИЗАЦИИ ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None

# --- РАБОТА С БАЗОЙ ДАННЫХ (SQLite) ---
DB_FILE = 'kvn_pro.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS scores 
                 (contest TEXT, team TEXT, judge_idx INTEGER, score REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS config 
                 (key TEXT PRIMARY KEY, value TEXT)''')
    conn.commit()
    conn.close()

def get_db_connection():
    return sqlite3.connect(DB_FILE)

init_db()

# --- ФУНКЦИИ КОНФИГУРАЦИИ ---
def save_config(key, items_list):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("REPLACE INTO config (key, value) VALUES (?, ?)", (key, ",".join(items_list)))
    conn.commit()
    conn.close()

def load_config(key, default):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM config WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0].split(",") if row else default

# Загружаем актуальные списки из БД
teams = load_config('teams', ["Команда 1", "Команда 2", "Команда 3", "Команда 4"])
judges = load_config('judges', ["Судья 1", "Судья 2", "Судья 3", "Судья 4", "Судья 5"])
contests = load_config('contests', ["Приветствие", "Разминка", "СТЭМ", "Музыкалка"])

# --- БЛОК АВТОРИЗАЦИИ ---
def login_ui():
    st.sidebar.title("🔐 Вход")
    pwd_input = st.sidebar.text_input("Введите пароль:", type="password")
    if st.sidebar.button("Войти"):
        if pwd_input == "admin":
            st.session_state.authenticated = True
            st.session_state.user_role = "admin"
            st.rerun()
        elif pwd_input == "kvn":
            st.session_state.authenticated = True
            st.session_state.user_role = "kvn"
            st.rerun()
        else:
            st.sidebar.error("Неверный пароль")

if not st.session_state.authenticated:
    login_ui()
    st.info("Пожалуйста, авторизуйтесь в боковой панели (пароль 'kvn' для судей или 'admin' для управления).")
    st.stop()

# Кнопка выхода внизу сайдбара
if st.sidebar.button("🚪 Выйти"):
    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.rerun()

# --- ОСНОВНОЕ МЕНЮ (доступно после входа) ---
st.sidebar.divider()
role = st.sidebar.radio("Разделы:", ["📱 Судейство", "📊 Табло для зала", "🕵️ Отчет", "⚙️ Настройки"])

# --- 1. ИНТЕРФЕЙС СУДЬИ ---
if role == "📱 Судейство":
    j_name = st.sidebar.selectbox("Ваше имя:", judges)
    j_id = judges.index(j_name)
    current_c = st.selectbox("Текущий конкурс:", contests)
    
    st.subheader(f"Оценочный лист: {j_name}")
    
    conn = get_db_connection()
    with st.form("vote_form"):
        for team in teams:
            # Читаем текущую оценку из базы
            curr_score = pd.read_sql(f"SELECT score FROM scores WHERE contest='{current_c}' AND team='{team}' AND judge_idx={j_id}", conn)
            val = float(curr_score['score'].values[0]) if not curr_score.empty else 0.0
            
            st.write(f"**{team}**")
            score_opts = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
            score = st.radio(f"Балл для {team}", score_opts, index=score_opts.index(val), horizontal=True, key=f"{team}_{current_c}")
            
            if st.form_submit_button(f"Сохранить: {team}"):
                c = conn.cursor()
                c.execute("DELETE FROM scores WHERE contest=? AND team=? AND judge_idx=?", (current_c, team, j_id))
                c.execute("INSERT INTO scores VALUES (?, ?, ?, ?)", (current_c, team, j_id, score))
                conn.commit()
                st.success(f"Оценка {team} сохранена!")
    conn.close()

# --- 2. ТАБЛО (ВИЗУАЛИЗАЦИЯ) ---
elif role == "📊 Табло для зала":
    st.header("🏆 ТЕКУЩИЙ РЕЙТИНГ")
    
    if st.sidebar.checkbox("Живое обновление (5 сек)", value=True):
        time.sleep(5)
        st.rerun()

    conn = get_db_connection()
    df_scores = pd.read_sql("SELECT * FROM scores", conn)
    conn.close()

    if not df_scores.empty:
        results = []
        for team in teams:
            team_total = 0
            for c in contests:
                marks = df_scores[(df_scores['contest'] == c) & (df_scores['team'] == team)]['score'].tolist()
                
                # Олимпийская система (если судей 5 и более)
                if len(marks) >= 5:
                    marks.sort()
                    avg = sum(marks[1:-1]) / (len(marks) - 2)
                else:
                    avg = sum(marks) / len(judges) if marks else 0
                team_total += avg
            results.append({"Команда": team, "Сумма": round(team_total, 2)})
        
        res_df = pd.DataFrame(results).sort_values(by="Сумма", ascending=False)
        st.bar_chart(res_df.set_index("Команда"))
        st.table(res_df)
    else:
        st.info("Ждем первых оценок...")

# --- 3. ОТЧЕТ ---
elif role == "🕵️ Отчет":
    st.header("Детальный протокол (все оценки)")
    conn = get_db_connection()
    df_all = pd.read_sql("SELECT * FROM scores", conn)
    conn.close()
    
    st.dataframe(df_all, use_container_width=True)
    
    buffer = io.BytesIO()
    df_all.to_excel(buffer, index=False)
    st.download_button("📥 Скачать протокол Excel", buffer.getvalue(), "kvn_pro.xlsx")

# --- 4. АДМИН-ПАНЕЛЬ ---
elif role == "⚙️ Настройки":
    if st.session_state.user_role != "admin":
        st.error("Доступ только для Администратора!")
    else:
        st.subheader("Управление параметрами игры")
        
        new_teams = st.text_area("Команды (через запятую):", ",".join(teams)).split(",")
        new_judges = st.text_area("Судьи (через запятую):", ",".join(judges)).split(",")
        new_contests = st.text_area("Конкурсы (через запятую):", ",".join(contests)).split(",")
        
        if st.button("Применить изменения"):
            save_config('teams', [x.strip() for x in new_teams])
            save_config('judges', [x.strip() for x in new_judges])
            save_config('contests', [x.strip() for x in new_contests])
            st.success("Настройки обновлены!")
            st.rerun()
            
        st.divider()
        if st.button("🔴 ОЧИСТИТЬ ВСЕ ОЦЕНКИ"):
            conn = get_db_connection()
            conn.cursor().execute("DELETE FROM scores")
            conn.commit()
            conn.close()
            st.warning("База данных оценок очищена!")
