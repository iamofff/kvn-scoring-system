import streamlit as st
import pandas as pd
import io
import time
from gspread_pandas import Spread, Client

# --- НАСТРОЙКИ СТРАНИЦЫ ---
st.set_page_config(page_title="КВН Google Sync", layout="wide")

# --- ПОДКЛЮЧЕНИЕ К GOOGLE SHEETS ---
# ВАЖНО: Вставьте сюда URL вашей созданной таблицы
SHEET_URL = "https://docs.google.com/spreadsheets/d/1YPHgLZ9582qXQkemxYosp7CKClPR8HRw5-f98kdDHmk/edit?usp=sharing" 

def get_google_sheet():
    try:
        # Для упрощения используем доступ по ссылке (таблица должна быть открыта на редактирование)
        # В профессиональной среде лучше использовать JSON-ключ сервисного аккаунта
        spread = Spread(SHEET_URL)
        return spread
    except Exception as e:
        st.error(f"Ошибка подключения к Google Sheets: {e}")
        return None

# --- ГЛОБАЛЬНОЕ СОСТОЯНИЕ (Инициализация) ---
if 'teams' not in st.session_state:
    st.session_state.teams = ["Команда 1", "Команда 2", "Команда 3", "Команда 4"]
if 'contests' not in st.session_state:
    st.session_state.contests = ["Приветствие", "Разминка", "СТЭМ", "Музыкалка"]
if 'judges' not in st.session_state:
    st.session_state.judges = ["Судья 1", "Судья 2", "Судья 3", "Судья 4", "Судья 5"]

# --- АВТОРИЗАЦИЯ ---
st.sidebar.title("🔐 Вход")
password = st.sidebar.text_input("Пароль:", type="password")
if password not in ["admin", "kvn"]:
    st.warning("Введите пароль для работы с системой.")
    st.stop()

spread = get_google_sheet()

# --- ФУНКЦИИ РАБОТЫ С ДАННЫМИ ---
def load_all_scores():
    if spread:
        df = spread.sheet_to_df(index=0, sheet='Scores')
        if df.empty:
            return pd.DataFrame(columns=['contest', 'team', 'judge_id', 'score'])
        return df
    return pd.DataFrame()

def save_score_to_google(contest, team, j_id, val):
    df = load_all_scores()
    # Удаляем старую оценку, если она была
    df = df[~((df['contest'] == contest) & (df['team'] == team) & (df['judge_id'] == str(j_id)))]
    # Добавляем новую
    new_row = pd.DataFrame([{'contest': contest, 'team': team, 'judge_id': str(j_id), 'score': val}])
    df = pd.concat([df, new_row], ignore_index=True)
    spread.df_to_sheet(df, index=False, sheet='Scores', replace=True)

# --- ИНТЕРФЕЙСЫ ---
role = st.sidebar.radio("Меню:", ["📱 Судья", "📊 Общее Табло", "⚙️ Настройки"])

if role == "📱 Судья":
    judge_name = st.sidebar.selectbox("Имя:", st.session_state.judges)
    judge_idx = st.session_state.judges.index(judge_name)
    contest = st.selectbox("Конкурс:", st.session_state.contests)
    
    st.subheader(f"Голосование: {judge_name}")
    
    # Кнопка ручного обновления, если названия команд изменились
    if st.button("🔄 Обновить список команд"):
        st.rerun()

    with st.form("vote_form"):
        db_df = load_all_scores()
        for team in st.session_state.teams:
            mask = (db_df['contest'] == contest) & (db_df['team'] == team) & (db_df['judge_id'] == str(judge_idx))
            current_val = float(db_df[mask]['score'].values[0]) if not db_df[mask].empty else 0.0
            
            st.write(f"**{team}**")
            score = st.radio(f"Балл", [0.0, 1.0, 2.0, 3.0, 4.0, 5.0], 
                             index=[0.0, 1.0, 2.0, 3.0, 4.0, 5.0].index(current_val), 
                             horizontal=True, key=f"v_{team}")
            
            if st.form_submit_button(f"Сохранить {team}"):
                save_score_to_google(contest, team, judge_idx, score)
                st.success(f"Балл для {team} отправлен в Google Таблицу!")

elif role == "📊 Общее Табло":
    st.header("🏆 Итоговый рейтинг (LIVE)")
    
    # Авто-обновление каждые 10 секунд
    if st.sidebar.checkbox("Включить авто-обновление (10 сек)", value=True):
        time.sleep(10)
        st.rerun()

    db_df = load_all_scores()
    if not db_df.empty:
        db_df['score'] = pd.to_numeric(db_df['score'])
        results = []
        for team in st.session_state.teams:
            total = 0
            for c in st.session_state.contests:
                marks = db_df[(db_df['contest']==c) & (db_df['team']==team)]['score'].astype(float).tolist()
                avg = sum(marks) / len(st.session_state.judges) if marks else 0
                total += avg
            results.append({"Команда": team, "Общий балл": round(total, 2)})
        
        res_df = pd.DataFrame(results).sort_values(by="Общий балл", ascending=False)
        st.bar_chart(res_df.set_index("Команда"))
        st.table(res_df)
    else:
        st.info("Данных пока нет. Судьи должны выставить первые оценки.")

elif role == "⚙️ Настройки":
    st.subheader("Глобальные настройки")
    st.write("После изменения нажмите 'Применить' и судьи увидят новые данные.")
    # Тут код для редактирования команд (как в прошлом примере)
    if st.button("Очистить все данные в Google Таблице"):
        spread.df_to_sheet(pd.DataFrame(columns=['contest', 'team', 'judge_id', 'score']), sheet='Scores', replace=True)
        st.success("Таблица очищена!")

