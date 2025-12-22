import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="КВН Судья 2.0", layout="wide")

# Глобальный кэш для синхронизации между всеми устройствами
@st.cache_resource
def get_global_store():
    return {
        'teams': ["Команда 1", "Команда 2", "Команда 3", "Команда 4"],
        'contests': ["Приветствие", "Разминка", "СТЭМ", "Музыкалка"],
        'judges_names': ["Судья 1", "Судья 2", "Судья 3", "Судья 4", "Судья 5"],
        'scores': {} # {Конкурс: {Команда: [оценки]}}
    }

store = get_global_store()

# Функция инициализации/обновления структуры оценок
def sync_scores_structure():
    num_judges = len(store['judges_names'])
    for c in store['contests']:
        if c not in store['scores']:
            store['scores'][c] = {}
        for t in store['teams']:
            if t not in store['scores'][c] or len(store['scores'][c][t]) != num_judges:
                store['scores'][c][t] = [0.0] * num_judges

sync_scores_structure()

st.title("🏆 КВН: Профессиональная система")

role = st.sidebar.radio("Ваша роль:", ["📱 Судья", "📊 Ведущий / Настройки"])

# --- ИНТЕРФЕЙС СУДЬИ ---
if role == "📱 Судья":
    # Выбор судьи по имени
    judge_name = st.sidebar.selectbox("Выберите ваше имя:", store['judges_names'])
    judge_id = store['judges_names'].index(judge_name)
    
    if st.button("🔄 Обновить список команд/конкурсов"):
        st.rerun()

    contest = st.selectbox("Текущий конкурс:", store['contests'])
    
    st.subheader(f"Оценочный лист | {judge_name}")
    
    with st.form("score_form"):
        for team in store['teams']:
            st.write(f"---")
            st.write(f"**{team}**")
            
            # Получаем текущую оценку
            current_val = store['scores'][contest][team][judge_id]
            
            score_options = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
            selected_score = st.radio(
                f"Балл для {team}:",
                score_options,
                index=score_options.index(current_val) if current_val in score_options else 0,
                horizontal=True,
                key=f"radio_{contest}_{team}_{judge_id}"
            )
            store['scores'][contest][team][judge_id] = selected_score
            
        if st.form_submit_button("✅ СОХРАНИТЬ ОЦЕНКИ"):
            st.success("Данные успешно синхронизированы!")

# --- ИНТЕРФЕЙС ВЕДУЩЕГО ---
else:
    tab1, tab2, tab3 = st.tabs(["📈 Итоги", "👥 Команды и Судьи", "🎬 Конкурсы"])
    
    with tab1:
        st.header("Результаты игры")
        results = []
        for team in store['teams']:
            row = {"Команда": team}
            total = 0
            for c in store['contests']:
                marks = store['scores'].get(c, {}).get(team, [0.0]*len(store['judges_names']))
                avg = sum(marks) / len(store['judges_names'])
                row[c] = round(avg, 2)
                total += avg
            row["ИТОГО"] = round(total, 2)
            results.append(row)
        
        df = pd.DataFrame(results)
        st.table(df)
        
        # Экспорт в Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Результаты')
            # Лист с именами судей для истории
            pd.DataFrame({"Судьи": store['judges_names']}).to_excel(writer, index=False, sheet_name='Судьи')
            
        st.download_button("📥 Скачать протокол", buffer.getvalue(), "kvn_final_report.xlsx")

    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Названия команд")
            new_teams = []
            for i, team in enumerate(store['teams']):
                name = st.text_input(f"Команда {i+1}", value=team, key=f"t_{i}")
                new_teams.append(name)
            
            if st.button("Обновить команды"):
                store['teams'] = new_teams
                sync_scores_structure()
                st.success("Команды обновлены!")
        
        with col2:
            st.subheader("Имена судей")
            new_judges = []
            for i in range(len(store['judges_names'])):
                j_name = st.text_input(f"Судья {i+1}", value=store['judges_names'][i], key=f"j_{i}")
                new_judges.append(j_name)
            
            if st.button("Обновить судей"):
                store['judges_names'] = new_judges
                sync_scores_structure()
                st.success("Список судей обновлен!")

    with tab3:
        st.subheader("Управление конкурсами")
        
        # Редактирование существующих
        updated_contests = []
        for i, ct in enumerate(store['contests']):
            c_name = st.text_input(f"Конкурс {i+1}", value=ct, key=f"c_{i}")
            updated_contests.append(c_name)
        
        # Добавление нового конкурса
        new_c = st.text_input("Название нового конкурса (например, Биатлон):")
        
        if st.button("Применить настройки конкурсов"):
            if new_c:
                updated_contests.append(new_c)
            store['contests'] = updated_contests
            sync_scores_structure()
            st.success("Список конкурсов обновлен!")
            st.rerun()

if st.sidebar.button("⚠️ Полный сброс игры"):
    st.cache_resource.clear()
    st.rerun()
