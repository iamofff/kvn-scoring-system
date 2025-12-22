import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import io
import time

st.set_page_config(page_title="КВН Google Cloud", layout="wide")

# Вставьте сюда ссылку на вашу таблицу
url = "https://docs.google.com/spreadsheets/d/1YPHgLZ9582qXQkemxYosp7CKClPR8HRw5-f98kdDHmk/edit?usp=sharing"

# Создаем подключение
conn = st.connection("gsheets", type=GSheetsConnection)

# Инициализация сессии для настроек
if 'teams' not in st.session_state:
    st.session_state.teams = ["Команда 1", "Команда 2", "Команда 3", "Команда 4"]
if 'contests' not in st.session_state:
    st.session_state.contests = ["Приветствие", "Разминка", "СТЭМ", "Музыкалка"]
if 'judges' not in st.session_state:
    st.session_state.judges = ["Судья 1", "Судья 2", "Судья 3", "Судья 4", "Судья 5"]

# --- ФУНКЦИИ ---
def load_data():
    try:
        # Читаем данные из первого листа
        return conn.read(spreadsheet=url, usecols=[0,1,2,3], ttl=0)
    except:
        return pd.DataFrame(columns=['contest', 'team', 'judge_id', 'score'])

def save_data(df):
    conn.update(spreadsheet=url, data=df)

# --- ИНТЕРФЕЙС ---
st.sidebar.title("🔐 Вход")
password = st.sidebar.text_input("Пароль:", type="password")

if password in ["admin", "kvn"]:
    role = st.sidebar.radio("Меню:", ["📱 Судья", "📊 Табло", "⚙️ Настройки"])

    if role == "📱 Судья":
        judge_name = st.sidebar.selectbox("Имя:", st.session_state.judges)
        judge_idx = st.session_state.judges.index(judge_name)
        contest = st.selectbox("Конкурс:", st.session_state.contests)
        
        df = load_data()
        
        with st.form("vote_form"):
            for team in st.session_state.teams:
                # Ищем старую оценку
                mask = (df['contest'] == contest) & (df['team'] == team) & (df['judge_id'] == judge_idx)
                current_val = float(df[mask]['score'].values[0]) if not df[mask].empty else 0.0
                
                st.write(f"**{team}**")
                score = st.radio(f"Балл", [0.0, 1.0, 2.0, 3.0, 4.0, 5.0], 
                                 index=[0.0, 1.0, 2.0, 3.0, 4.0, 5.0].index(current_val), 
                                 horizontal=True, key=f"v_{team}_{contest}")
                
                if st.form_submit_button(f"Сохранить {team}"):
                    # Обновляем DataFrame
                    df = df[~((df['contest'] == contest) & (df['team'] == team) & (df['judge_id'] == judge_idx))]
                    new_row = pd.DataFrame([{'contest': contest, 'team': team, 'judge_id': judge_idx, 'score': score}])
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_data(df)
                    st.success(f"Сохранено!")

    elif role == "📊 Табло":
        st.header("🏆 Рейтинг")
        if st.button("🔄 Обновить сейчас"):
            st.rerun()
            
        df = load_data()
        if not df.empty:
            df['score'] = pd.to_numeric(df['score'])
            results = []
            for team in st.session_state.teams:
                total = 0
                for c in st.session_state.contests:
                    marks = df[(df['contest']==c) & (df['team']==team)]['score'].tolist()
                    avg = sum(marks) / len(st.session_state.judges) if marks else 0
                    total += avg
                results.append({"Команда": team, "Балл": round(total, 2)})
            
            res_df = pd.DataFrame(results).sort_values(by="Балл", ascending=False)
            st.bar_chart(res_df.set_index("Команда"))
            st.table(res_df)
        
    elif role == "⚙️ Настройки":
        st.subheader("Настройки игры")
        if st.button("❌ Очистить всю таблицу Google"):
            save_data(pd.DataFrame(columns=['contest', 'team', 'judge_id', 'score']))
            st.success("Таблица очищена")

else:
    st.info("Введите пароль")
