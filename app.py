import streamlit as st
import plotly.graph_objects as go
import numpy as np
import folium
from streamlit_folium import st_folium
import google.generativeai as genai

# --- КОНФИГУРАЦИЯ ИИ ---
# Вставь свой ключ сюда (получи на aistudio.google.com)
API_KEY = "AIzaSyCNR93IXF2oGPYlfuI345Xh0FvUMF8WTHI" 
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- НАСТРОЙКА СТРАНИЦЫ ---
st.set_page_config(page_title="SuVision Global AI", layout="wide")

# --- БАЗА ДАННЫХ ВОДОЕМОВ (10 ОБЪЕКТОВ) ---
LAKES_DB = {
    "Каспийское море": {"coords": [43.6500, 51.1500], "type": "Морской", "risk": "Нефтяные загрязнения"},
    "Озеро Балхаш": {"coords": [46.5400, 74.8700], "type": "Бессточный", "risk": "Тяжелые металлы"},
    "БАО (Алматы)": {"coords": [43.0506, 76.9849], "type": "Высокогорный", "risk": "Бактериальное загрязнение"},
    "Озеро Алаколь": {"coords": [46.1200, 81.7400], "type": "Соленое", "risk": "Антропогенная нагрузка"},
    "Боровое": {"coords": [53.0800, 70.3000], "type": "Пресноводный", "risk": "Цветение воды (эвтрофикация)"},
    "Река Иртыш": {"coords": [49.9500, 82.6100], "type": "Речной", "risk": "Промышленные стоки"},
    "Озеро Маркаколь": {"coords": [48.5100, 85.8000], "type": "Заповедный", "risk": "Изменение климата"},
    "Озеро Сайран": {"coords": [43.2389, 76.8897], "type": "Городской", "risk": "Ливневые стоки"},
    "Шардаринское вдхр.": {"coords": [41.2500, 67.9800], "type": "Ирригационный", "risk": "Пестициды"},
    "Озеро Тенгиз": {"coords": [50.4000, 68.9000], "type": "Соленое/Заболоченное", "risk": "Гидрологический баланс"}
}

# --- БОКОВАЯ ПАНЕЛЬ ---
with st.sidebar:
    st.title("🚀 SuVision AI Core")
    st.write("Система глобального мониторинга v2.0")
    st.divider()
    
    selected_name = st.selectbox("🎯 Выберите станцию", list(LAKES_DB.keys()))
    lake = LAKES_DB[selected_name]
    
    st.subheader("📡 Данные датчиков")
    ph = st.slider("Уровень pH", 0.0, 14.0, 7.2, 0.1)
    temp = st.slider("Температура воды (°C)", 0.0, 40.0, 18.0, 0.5)
    turb = st.slider("Мутность (NTU)", 0.0, 100.0, 4.0, 1.0)
    
    st.divider()
    st.caption("Статус системы: В сети 🟢")

# --- ЛОГИКА SRI ---
def calculate_sri(p, t, tr):
    penalty = abs(p - 7) * 1.5 + (t / 10) * 0.8 + (tr / 20) * 1.2
    return max(round(10 - penalty, 2), 0.0)

sri = calculate_sri(ph, temp, turb)

# --- ФУНКЦИЯ ИИ (GEMINI API) ---
def get_ai_report(lake_name, ph, temp, turb, sri, risk):
    prompt = f"""
    Действуй как профессиональный эксперт-эколог. Проанализируй данные воды для объекта {lake_name} (тип: {lake['type']}).
    Параметры: pH {ph}, Температура {temp}C, Мутность {turb} NTU. 
    Рассчитанный индекс устойчивости (SRI): {sri}/10. 
    Основной локальный риск: {risk}.
    Дай краткий научный анализ на РУССКОМ языке (макс. 60 слов). 
    Сфокусируйся на связи между текущими данными и рисками региона.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "ИИ-анализ временно недоступен. Проверьте API-ключ или интернет-соединение."

# --- ОСНОВНОЙ ИНТЕРФЕЙС ---
st.title("🌊 SuVision: Интеллектуальный эко-мониторинг")
st.markdown(f"**Текущий объект:** {selected_name} | **Профиль риска:** {lake['risk']}")

col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("🗺️ Геопространственный анализ")
    # Профессиональная темная карта
    m = folium.Map(location=lake["coords"], zoom_start=7, tiles="CartoDB dark_matter")
    
    for name, info in LAKES_DB.items():
        is_target = (name == selected_name)
        color = "cyan" if not is_target else ("green" if sri > 7 else "orange" if sri > 4 else "red")
        folium.CircleMarker(
            location=info["coords"],
            radius=12 if is_target else 6,
            color=color,
            fill=True,
            popup=name
        ).add_to(m)
    st_folium(m, width="100%", height=500, key=f"map_{selected_name}")

with col_right:
    st.subheader("🤖 ИИ-Диагностика")
    
    if st.button("Сгенерировать отчет ИИ"):
        with st.spinner("Запрос к Gemini AI..."):
            ai_report = get_ai_report(selected_name, ph, temp, turb, sri, lake['risk'])
            st.markdown(f"**Заключение эксперта ИИ:**\n\n{ai_report}")
    else:
        st.info("Нажмите кнопку выше для запуска нейросетевого анализа состояния среды.")

    st.divider()
    st.metric("Индекс устойчивости (SRI)", f"{sri}/10", delta=round(sri-7, 2))
    
    # Визуализация Gauge
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=sri,
        gauge={'axis': {'range': [0, 10]},
               'bar': {'color': "#00f2fe"},
               'steps': [{'range': [0, 4], 'color': "#330000"},
                         {'range': [4, 7], 'color': "#443300"},
                         {'range': [7, 10], 'color': "#003311"}]}
    ))
    fig.update_layout(height=230, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="rgba(0,0,0,0)", font={'color':"white"})
    st.plotly_chart(fig, use_container_width=True)

# --- НАУЧНЫЕ РЕКОМЕНДАЦИИ ---
st.header("💡 Научные рекомендации")
rec_col1, rec_col2, rec_col3 = st.columns(3)

with rec_col1:
    if ph < 6.5 or ph > 8.5:
        st.error(f"**Химическая угроза:** pH {ph} нестабилен для типа '{lake['type']}'. Проверьте наличие промышленных стоков.")
    else:
        st.success("Химический баланс в норме.")

with rec_col2:
    if temp > 25:
        st.warning("**Тепловой риск:** Высокая температура снижает уровень растворенного кислорода.")
    else:
        st.success("Температурный режим стабилен.")

with rec_col3:
    if turb > 10:
        st.error("**Предупреждение о мутности:** Обнаружено высокое содержание взвесей.")
    else:
        st.success("Прозрачность воды в пределах нормы.")

st.markdown("---")
st.caption("Проект SuVision | На базе Gemini AI | Разработано для международных соревнований 2026")
