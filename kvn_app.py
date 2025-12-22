import streamlit as st
import pandas as pd
import io
import time

# --- НАСТРОЙКИ СТРАНИЦЫ ---
st.set_page_config(page_title="КВН LIVE: Центр управления", layout="wide")

# --- ГЛОБАЛЬНОЕ ХРАНИЛИЩЕ (Синхронизация между устройствами) ---
@st.cache_resource
def get_global_data():
    return {
        'scores': pd.DataFrame(columns=['contest', 'team', 'judge_id', 'score']),
        'teams': ["Технари", "Кофеиновые кайтики", "Сборная Пятого подъезда", "Нейросетевые коты"],
        'judges': ["Судья 1", "Судья 2", "Судья 3", "Судья 4", "Судья 5"],
        'contests': ["Приветствие", "Разминка", "СТЭМ", "Музыкалка"],
        'timer_start': None
    }

data = get_global_data()

# --- БЕЗОПАСНОСТЬ ---
st.sidebar.title("🔐 Авторизация")
pwd = st.sidebar.text_input("Введите пароль:", type="password")

if pwd not in ["admin", "kvn"]:
    st.info("Добро пожаловать! Введите пароль в боковой панели (например, 'kvn' для судей или 'admin' для настроек).")
    st.stop()

# --- ГЛАВНОЕ МЕНЮ ---
menu = st.sidebar.radio("Разделы:", ["📱 Пульт Судьи", "📊 Табло (Зал)", "🕵️ Протокол", "⚙️ Админ-панель"])

# --- 1. ПУЛЬТ СУДЬИ ---
if menu == "📱 Пульт Судьи":
    j_name = st.sidebar.selectbox("Ваше имя:", data['judges'])
    j_id = data['judges'].index(j_name)
    
    # Кнопка обновления, если админ поменял названия команд
    if st.button("🔄 Обновить список команд"):
        st.rerun()

    current_contest = st.selectbox("Конкурс:", data['contests'])
    st.subheader(f"Голосование: {j_name}")

    with st.form("voting_form"):
        for team in data['teams']:
            st.write(f"---")
            st.write(f"**{team}**")
            
            # Поиск текущей оценки
            df = data['scores']
            mask = (df['contest'] == current_contest) & (df['team'] == team) & (df['judge_id'] == j_id)
            current_val = float(df[mask]['score'].values[0]) if not df[mask].empty else 0.0
            
            score_opts = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
            val = st.radio(f"Оценка для {team}", score_opts, index=score_opts.index(current_val), horizontal=True, key=f"r_{team}")
            
            if st.form_submit_button(f"Сохранить балл: {team}"):
                # Обновление данных
                new_df = df[~((df['contest'] == current_contest) & (df['team'] == team) & (df['judge_id'] == j_id))]
                new_row = pd.DataFrame([{'contest': current_contest, 'team': team, 'judge_id': j_id, 'score': val}])
                data['scores'] = pd.concat([new_df, new_row], ignore_index=True)
                st.success(f"Балл для {team} принят!")

# --- 2. ТАБЛО (ВИЗУАЛИЗАЦИЯ) ---
elif menu == "📊 Табло (Зал)":
    st.header("🏆 ТЕКУЩИЙ РЕЙТИНГ")
    
    # Авто-обновление экрана раз в 5 секунд
    if st.sidebar.checkbox("Включить живое обновление", value=True):
        time.sleep(5)
        st.rerun()

    df = data['scores']
    if not df.empty:
        results = []
        for team in data['teams']:
            team_total = 0
            for c in data['contests']:
                marks = df[(df['contest'] == c) & (df['team'] == team)]['score'].tolist()
                
                # Олимпийская система (если проголосовали минимум 5 судей)
                if len(marks) >= 5:
                    marks.sort()
                    avg = sum(marks[1:-1]) / (len(marks) - 2)
                else:
                    avg = sum(marks) / len(data['judges']) if marks else 0
                team_total += avg
            results.append({"Команда": team, "Сумма баллов": round(team_total, 2)})
        
        res_df = pd.DataFrame(results).sort_values(by="Сумма баллов", ascending=False)
        st.bar_chart(res_df.set_index("Команда"))
        st.table(res_df)
    else:
        st.info("Ожидание первых оценок от судей...")

# --- 3. ДЕТАЛЬНЫЙ ПРОТОКОЛ ---
elif menu == "🕵️ Протокол":
    st.header("Детальная ведомость")
    st.dataframe(data['scores'], use_container_width=True)
    
    # Кнопка скачивания для отчетности
    buffer = io.BytesIO()
    data['scores'].to_excel(buffer, index=False)
    st.download_button("📥 Скачать результаты в Excel", buffer.getvalue(), "kvn_report.xlsx")

# --- 4. АДМИН-ПАНЕЛЬ ---
elif menu == "⚙️ Админ-панель":
    if pwd != "admin":
        st.error("Доступ запрещен!")
    else:
        st.subheader("Настройки команд и судей")
        data['teams'] = st.text_area("Команды (через запятую)", ",".join(data['teams'])).split(",")
        data['judges'] = st.text_area("Судьи (через запятую)", ",".join(data['judges'])).split(",")
        data['contests'] = st.text_area("Конкурсы (через запятую)", ",".join(data['contests'])).split(",")
        
        if st.button("Сбросить все данные"):
            data['scores'] = pd.DataFrame(columns=['contest', 'team', 'judge_id', 'score'])
            st.rerun()
