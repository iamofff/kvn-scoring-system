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
        'scores': {}
    }

store = get_global_store()
num_judges = 5

# Инициализация структуры оценок
if not store['scores']:
    store['scores'] = {c: {t: [0.0] * num_judges for t in store['teams']} for c in store['contests']}

st.title("🏆 КВН: Система голосования")

role = st.sidebar.radio("Ваша роль:", ["📱 Судья", "📊 Ведущий / Настройки"])

# --- ИНТЕРФЕЙС СУДЬИ ---
if role == "📱 Судья":
    judge_id = st.sidebar.selectbox("Ваш номер судьи:", range(1, num_judges + 1)) - 1
    
    # Кнопка ручного обновления данных из кэша
    if st.button("🔄 Обновить названия команд"):
        st.rerun()

    contest = st.selectbox("Текущий конкурс:", store['contests'])
    
    st.subheader(f"Оценочный лист | Судья №{judge_id + 1}")
    st.write(f"**Конкурс:** {contest}")

    # Форма для оценок
    with st.form("score_form"):
        for team in store['teams']:
            st.write(f"---")
            st.write(f"**{team}**")
            
            # Получаем текущую оценку (приводим к int для индекса в radio)
            current_val = store['scores'][contest][team][judge_id]
            
            # Метод "Нажми на цифру" через горизонтальный radio
            score_options = [1.0, 2.0, 3.0, 4.0, 5.0]
            selected_score = st.radio(
                f"Выберите балл для {team}:",
                score_options,
                index=score_options.index(current_val) if current_val in score_options else 0,
                horizontal=True,
                key=f"radio_{contest}_{team}_{judge_id}"
            )
            # Записываем выбор в хранилище
            store['scores'][contest][team][judge_id] = selected_score
            
        st.write("---")
        if st.form_submit_button("✅ СОХРАНИТЬ ВСЕ ОЦЕНКИ"):
            st.success("Баллы успешно отправлены в систему!")

# --- ИНТЕРФЕЙС ВЕДУЩЕГО ---
else:
    tab1, tab2 = st.tabs(["📈 Итоговая таблица", "⚙️ Настройка команд"])
    
    with tab1:
        results = []
        for team in store['teams']:
            row = {"Команда": team}
            total = 0
            for c in store['contests']:
                marks = store['scores'][c].get(team, [0.0]*num_judges)
                avg = sum(marks) / num_judges
                row[c] = round(avg, 2)
                total += avg
            row["ИТОГО"] = round(total, 2)
            results.append(row)
        
        df = pd.DataFrame(results)
        st.table(df) # Используем простую таблицу для наглядности
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Результаты')
        st.download_button("📥 Скачать Excel отчет", buffer.getvalue(), "kvn_final.xlsx")

    with tab2:
        st.subheader("Изменение названий")
        temp_teams = []
        for i, team in enumerate(store['teams']):
            name = st.text_input(f"Команда {i+1}", value=team, key=f"edit_{i}")
            temp_teams.append(name)
        
        if st.button("Применить новые названия"):
            old_teams = store['teams']
            new_scores = {c: {} for c in store['contests']}
            
            for c in store['contests']:
                for i, old_name in enumerate(old_teams):
                    new_name = temp_teams[i]
                    new_scores[c][new_name] = store['scores'][c].get(old_name, [0.0]*num_judges)
            
            store['teams'] = temp_teams
            store['scores'] = new_scores
            st.success("Названия обновлены у всех!")
            st.rerun()

if st.sidebar.button("⚠️ Сброс всей игры"):
    st.cache_resource.clear()
    st.rerun()
