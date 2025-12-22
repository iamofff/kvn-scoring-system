import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="КВН Судья Про", layout="wide")

# Глобальное хранилище данных
@st.cache_resource
def get_global_store():
    return {
        'teams': ["Команда 1", "Команда 2", "Команда 3", "Команда 4"],
        'contests': ["Приветствие", "Разминка", "СТЭМ", "Музыкалка"],
        'judges_names': ["Судья 1", "Судья 2", "Судья 3", "Судья 4", "Судья 5"],
        'scores': {} 
    }

store = get_global_store()

def sync_scores_structure():
    num_judges = len(store['judges_names'])
    for c in store['contests']:
        if c not in store['scores']:
            store['scores'][c] = {}
        for t in store['teams']:
            if t not in store['scores'][c] or len(store['scores'][c][t]) != num_judges:
                # Если судья был добавлен/удален, корректируем список оценок
                old_marks = store['scores'][c].get(t, [])
                if len(old_marks) < num_judges:
                    store['scores'][c][t] = old_marks + [0.0] * (num_judges - len(old_marks))
                else:
                    store['scores'][c][t] = old_marks[:num_judges]

sync_scores_structure()

st.title("🏆 КВН: Система прозрачного судейства")

role = st.sidebar.radio("Ваша роль:", ["📱 Судья", "📊 Ведущий / Протокол"])

# --- ИНТЕРФЕЙС СУДЬИ ---
if role == "📱 Судья":
    judge_name = st.sidebar.selectbox("Выберите ваше имя:", store['judges_names'])
    judge_id = store['judges_names'].index(judge_name)
    
    if st.button("🔄 Синхронизировать списки"):
        st.rerun()

    contest = st.selectbox("Конкурс:", store['contests'])
    st.subheader(f"Оценочный лист: {judge_name}")
    
    with st.form("score_form"):
        for team in store['teams']:
            st.write(f"**{team}**")
            current_val = store['scores'][contest][team][judge_id]
            
            score_options = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
            selected_score = st.radio(
                f"Балл:", score_options,
                index=score_options.index(current_val) if current_val in score_options else 0,
                horizontal=True, key=f"r_{contest}_{team}_{judge_id}"
            )
            store['scores'][contest][team][judge_id] = selected_score
            
        if st.form_submit_button("✅ ОТПРАВИТЬ БАЛЛЫ"):
            st.success("Оценки сохранены в системе!")

# --- ИНТЕРФЕЙС ВЕДУЩЕГО ---
else:
    t_results, t_details, t_config = st.tabs(["📈 Итоговое Табло", "🕵️ Детализация (Кто что поставил)", "⚙️ Настройки"])
    
    # 1. Сводная таблица (Средние баллы)
    with t_results:
        summary_data = []
        for team in store['teams']:
            row = {"Команда": team}
            total = 0
            for c in store['contests']:
                marks = store['scores'].get(c, {}).get(team, [0.0]*len(store['judges_names']))
                avg = sum(marks) / len(store['judges_names'])
                row[c] = round(avg, 2)
                total += avg
            row["ИТОГО"] = round(total, 2)
            summary_data.append(row)
        
        df_summary = pd.DataFrame(summary_data)
        st.header("Сводный протокол (средние баллы)")
        st.table(df_summary.style.highlight_max(axis=0, subset=['ИТОГО'], color='#CFFFCC'))

    # 2. Детальный протокол (Все оценки)
    with t_details:
        st.header("Детальная ведомость оценок")
        
        detailed_rows = []
        for c in store['contests']:
            for t in store['teams']:
                row = {"Конкурс": c, "Команда": t}
                marks = store['scores'].get(c, {}).get(t, [0.0]*len(store['judges_names']))
                # Добавляем оценку каждого судьи в колонку
                for i, name in enumerate(store['judges_names']):
                    row[name] = marks[i]
                row["Средний балл"] = round(sum(marks)/len(marks), 2)
                detailed_rows.append(row)
        
        df_detailed = pd.DataFrame(detailed_rows)
        st.dataframe(df_detailed, use_container_width=True)

        # Кнопка скачивания Excel с двумя листами
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_summary.to_excel(writer, index=False, sheet_name='Итоги')
            df_detailed.to_excel(writer, index=False, sheet_name='Детализация_по_судьям')
        
        st.download_button("📥 Скачать полный Excel-отчет", buffer.getvalue(), "kvn_full_report.xlsx")

    # 3. Настройки
    with t_config:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Команды")
            store['teams'] = [st.text_input(f"Команда {i+1}", value=t, key=f"t_{i}") for i, t in enumerate(store['teams'])]
        with col2:
            st.subheader("Судьи")
            store['judges_names'] = [st.text_input(f"Судья {i+1}", value=j, key=f"j_{i}") for i, j in enumerate(store['judges_names'])]
        
        st.subheader("Конкурсы")
        new_contests = []
        for i, ct in enumerate(store['contests']):
            new_contests.append(st.text_input(f"Конкурс {i+1}", value=ct, key=f"c_{i}"))
        
        add_c = st.text_input("Добавить новый конкурс:")
        if st.button("Сохранить все изменения"):
            if add_c: new_contests.append(add_c)
            store['contests'] = new_contests
            sync_scores_structure()
            st.success("Настройки успешно обновлены!")
            st.rerun()

if st.sidebar.button("⚠️ СБРОСИТЬ ВСЮ ИГРУ"):
    st.cache_resource.clear()
    st.rerun()
