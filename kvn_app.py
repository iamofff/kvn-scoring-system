import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="КВН Судья 2.0", layout="wide")

st.title("🏆 Цифровая система КВН")

# Настройки
teams = ["Технари", "Кофеиновые кайтики", "Сборная Пятого подъезда", "Нейросетевые коты"]
contests = ["Приветствие", "Разминка", "СТЭМ", "Музыкалка"]
num_judges = 5

if 'scores' not in st.session_state:
    st.session_state.scores = {c: {t: [0.0] * num_judges for t in teams} for c in contests}

role = st.sidebar.radio("Выберите интерфейс:", ["📱 Судья", "📊 Ведущий / Результаты"])

if role == "📱 Судья":
    judge_id = st.sidebar.selectbox("Ваш номер судьи:", range(1, num_judges + 1)) - 1
    contest = st.selectbox("Текущий конкурс:", contests)
    
    st.info(f"Судья №{judge_id + 1}. Выставляйте баллы командам:")
    
    with st.form("score_form"):
        for team in teams:
            current_score = st.session_state.scores[contest][team][judge_id]
            st.session_state.scores[contest][team][judge_id] = st.slider(
                f"Команда: {team}", 1.0, 5.0, float(current_score), 0.5
            )
        if st.form_submit_button("Сохранить мои оценки"):
            st.success("Данные успешно переданы на сервер!")

else:
    st.header("Результаты игры в реальном времени")
    
    # Формируем данные для таблицы
    results = []
    for team in teams:
        row = {"Команда": team}
        total = 0
        for c in contests:
            avg = sum(st.session_state.scores[c][team]) / num_judges
            row[c] = round(avg, 2)
            total += avg
        row["ИТОГО"] = round(total, 2)
        results.append(row)
    
    df = pd.DataFrame(results)
    
    # Визуализация данных
    st.dataframe(df.style.highlight_max(axis=0, subset=['ИТОГО'], color='#2ecc71'), use_container_width=True)
    
    # --- СЕКЦИЯ EXCEL ---
    st.markdown("---")
    st.subheader("Экспорт данных")
    
    # Создаем буфер в памяти для Excel файла
    buffer = io.BytesIO()
    
    # Используем xlsxwriter как движок
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Итоги_КВН')
        
        # Можно добавить детальный лист с оценками каждого судьи
        detailed_data = []
        for c in contests:
            for t in teams:
                marks = st.session_state.scores[c][t]
                detailed_data.append([c, t] + marks)
        
        detail_df = pd.DataFrame(detailed_data, columns=["Конкурс", "Команда"] + [f"Судья {i+1}" for i in range(num_judges)])
        detail_df.to_excel(writer, index=False, sheet_name='Детальные_оценки')

    st.download_button(
        label="📥 Скачать протокол игры в Excel",
        data=buffer.getvalue(),
        file_name="kvn_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if st.sidebar.button("⚠️ Сбросить всё"):
    st.session_state.scores = {c: {t: [0.0] * num_judges for t in teams} for c in contests}
    st.rerun()