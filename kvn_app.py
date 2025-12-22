import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="КВН Судья 2.0", layout="wide")

# Инициализация настроек в сессии, чтобы изменения не пропадали
if 'teams' not in st.session_state:
    st.session_state.teams = ["Команда 1", "Команда 2", "Команда 3", "Команда 4"]

if 'contests' not in st.session_state:
    st.session_state.contests = ["Приветствие", "Разминка", "СТЭМ", "Музыкалка"]

num_judges = 5

# Инициализация базы оценок
if 'scores' not in st.session_state:
    st.session_state.scores = {c: {t: [0.0] * num_judges for t in st.session_state.teams} for c in st.session_state.contests}

st.title("🏆 Панель управления КВН")

# Боковая панель
role = st.sidebar.radio("Выберите интерфейс:", ["📱 Судья", "📊 Ведущий / Настройки"])

# --- ИНТЕРФЕЙС СУДЬИ ---
if role == "📱 Судья":
    judge_id = st.sidebar.selectbox("Ваш номер судьи:", range(1, num_judges + 1)) - 1
    contest = st.selectbox("Текущий конкурс:", st.session_state.contests)
    
    st.info(f"Судья №{judge_id + 1}. Выставляйте баллы:")
    
    with st.form("score_form"):
        for team in st.session_state.teams:
            # Безопасно получаем текущую оценку
            current_score = st.session_state.scores.get(contest, {}).get(team, [0.0]*num_judges)[judge_id]
            st.session_state.scores[contest][team][judge_id] = st.slider(
                f"Команда: {team}", 1.0, 5.0, float(current_score), 0.5
            )
        if st.form_submit_button("Сохранить мои оценки"):
            st.success("Оценки успешно переданы!")

# --- ИНТЕРФЕЙС ВЕДУЩЕГО / АДМИНА ---
else:
    tab1, tab2 = st.tabs(["📈 Табло результатов", "⚙️ Настройки команд"])
    
    with tab1:
        st.header("Результаты игры")
        results = []
        for team in st.session_state.teams:
            row = {"Команда": team}
            total = 0
            for c in st.session_state.contests:
                marks = st.session_state.scores.get(c, {}).get(team, [0.0]*num_judges)
                avg = sum(marks) / num_judges
                row[c] = round(avg, 2)
                total += avg
            row["ИТОГО"] = round(total, 2)
            results.append(row)
        
        df = pd.DataFrame(results)
        st.dataframe(df.style.highlight_max(axis=0, subset=['ИТОГО'], color='#2ecc71'), use_container_width=True)
        
        # Скачивание Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Итоги')
        
        st.download_button("📥 Скачать протокол Excel", buffer.getvalue(), "kvn_results.xlsx")

    with tab2:
        st.header("Управление составом")
        st.write("Здесь вы можете изменить названия команд. Оценки привязываются к названию.")
        
        new_teams = []
        for i, team in enumerate(st.session_state.teams):
            new_name = st.text_input(f"Команда {i+1}:", value=team)
            new_teams.append(new_name)
        
        if st.button("Обновить названия команд"):
            # Логика обновления: если имя изменилось, переносим оценки
            old_teams = st.session_state.teams
            new_scores = {c: {} for c in st.session_state.contests}
            
            for c in st.session_state.contests:
                for i, old_name in enumerate(old_teams):
                    new_name = new_teams[i]
                    # Берем старые оценки или создаем пустые
                    new_scores[c][new_name] = st.session_state.scores.get(c, {}).get(old_name, [0.0]*num_judges)
            
            st.session_state.teams = new_teams
            st.session_state.scores = new_scores
            st.success("Названия обновлены!")
            st.rerun()

if st.sidebar.button("⚠️ Сбросить всё"):
    st.session_state.clear()
    st.rerun()
