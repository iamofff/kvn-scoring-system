import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="КВН Судья 2.0", layout="wide")

# Глобальный кэш для синхронизации между разными устройствами
@st.cache_resource
def get_global_store():
    return {
        'teams': ["Команда 1", "Команда 2", "Команда 3", "Команда 4"],
        'contests': ["Приветствие", "Разминка", "СТЭМ", "Музыкалка"],
        'scores': {} # Структура будет заполняться динамически
    }

store = get_global_store()
num_judges = 5

# Инициализация структуры оценок, если она пуста
if not store['scores']:
    store['scores'] = {c: {t: [0.0] * num_judges for t in store['teams']} for c in store['contests']}

st.title("🏆 Синхронная система КВН")

role = st.sidebar.radio("Выберите интерфейс:", ["📱 Судья", "📊 Ведущий / Настройки"])

# --- ИНТЕРФЕЙС СУДЬИ ---
if role == "📱 Судья":
    judge_id = st.sidebar.selectbox("Ваш номер судьи:", range(1, num_judges + 1)) - 1
    # Судья всегда видит актуальный список команд из глобального хранилища
    contest = st.selectbox("Текущий конкурс:", store['contests'])
    
    st.info(f"Судья №{judge_id + 1}. Команды обновляются автоматически.")
    
    with st.form("score_form"):
        for team in store['teams']:
            current_score = store['scores'][contest][team][judge_id]
            # Обновляем прямо в глобальном хранилище
            store['scores'][contest][team][judge_id] = st.slider(
                f"Команда: {team}", 1.0, 5.0, float(current_score), 0.5, key=f"{contest}_{team}_{judge_id}"
            )
        if st.form_submit_button("Сохранить оценки"):
            st.success("Данные синхронизированы!")

# --- ИНТЕРФЕЙС ВЕДУЩЕГО ---
else:
    tab1, tab2 = st.tabs(["📈 Табло результатов", "⚙️ Настройки"])
    
    with tab1:
        results = []
        for team in store['teams']:
            row = {"Команда": team}
            total = 0
            for c in store['contests']:
                marks = store['scores'][c][team]
                avg = sum(marks) / num_judges
                row[c] = round(avg, 2)
                total += avg
            row["ИТОГО"] = round(total, 2)
            results.append(row)
        
        df = pd.DataFrame(results)
        st.dataframe(df.style.highlight_max(axis=0, subset=['ИТОГО'], color='#2ecc71'), use_container_width=True)
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Итоги')
        st.download_button("📥 Скачать протокол Excel", buffer.getvalue(), "kvn_results.xlsx")

    with tab2:
        st.subheader("Переименование команд")
        temp_teams = []
        for i, team in enumerate(store['teams']):
            name = st.text_input(f"Команда {i+1}", value=team, key=f"edit_{i}")
            temp_teams.append(name)
        
        if st.button("Применить новые названия для всех"):
            old_teams = store['teams']
            new_scores = {c: {} for c in store['contests']}
            
            for c in store['contests']:
                for i, old_name in enumerate(old_teams):
                    new_name = temp_teams[i]
                    new_scores[c][new_name] = store['scores'][c].get(old_name, [0.0]*num_judges)
            
            store['teams'] = temp_teams
            store['scores'] = new_scores
            st.success("Названия изменены у всех судей!")
            st.rerun()

if st.sidebar.button("⚠️ Полный сброс системы"):
    st.cache_resource.clear()
    st.rerun()
