import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Настройка страницы
st.set_page_config(page_title="Калькулятор TG (Final)", layout="wide")
st.title("📊 Калькулятор экономики рассылок в Telegram")

# --- УЛУЧШЕННАЯ ФУНКЦИЯ СИНХРОНИЗАЦИИ ---
def sync_widget(label, min_v, max_v, default_v, step_v, base_key, is_int=False):
    """
    Создает пару (Input + Slider).
    is_int=True убирает дробную часть и запятые.
    """
    input_key = base_key + "_input"
    slider_key = base_key + "_slider"

    # Определяем тип данных (int или float)
    cast_func = int if is_int else float
    fmt = "%d" if is_int else "%.2f"

    # Инициализация
    if input_key not in st.session_state:
        st.session_state[input_key] = cast_func(default_v)
    if slider_key not in st.session_state:
        st.session_state[slider_key] = cast_func(default_v)

    # Callback: Ввод -> Слайдер
    def update_slider():
        val = st.session_state[input_key]
        if val < min_v: val = min_v
        if val > max_v: val = max_v
        st.session_state[slider_key] = cast_func(val)

    # Callback: Слайдер -> Ввод
    def update_input():
        val = st.session_state[slider_key]
        st.session_state[input_key] = cast_func(val)

    st.sidebar.subheader(label)
    
    # 1. Поле ввода
    val = st.sidebar.number_input(
        "Точное значение", 
        min_value=cast_func(min_v), 
        max_value=cast_func(max_v), 
        value=cast_func(st.session_state[input_key]), 
        step=cast_func(step_v),
        format=fmt,  # Применяем формат (целое или дробное)
        key=input_key, 
        on_change=update_slider,
        label_visibility="collapsed"
    )
    
    # 2. Слайдер
    st.sidebar.slider(
        "", 
        min_value=cast_func(min_v), 
        max_value=cast_func(max_v), 
        value=cast_func(st.session_state[slider_key]), 
        step=cast_func(step_v),
        key=slider_key, 
        on_change=update_input,
        label_visibility="collapsed"
    )
    
    return val

# --- БОКОВАЯ ПАНЕЛЬ ---
st.sidebar.header("🎛 Управляемые параметры")

# ЦЕНА: Оставляем дробной (is_int=False)
price_per_msg = sync_widget("💰 Цена за 1 сообщение (руб)", 1.0, 15.0, 5.0, 0.1, "price", is_int=False)

# ОБЪЕМ: Делаем целым (is_int=True)
target_msgs_month = sync_widget("📨 План сообщений (мес)", 10000, 2000000, 60000, 1000, "volume", is_int=True)

# ЖИВУЧЕСТЬ: Делаем целой (is_int=True) !!! ИСПРАВЛЕНО ЗДЕСЬ !!!
msgs_per_account = sync_widget("🔋 Живучесть аккаунта (сообщений)", 10, 200, 50, 1, "life", is_int=True)

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Стоимость ресурсов")
cost_raw_account = st.sidebar.number_input("Цена номера/регистрации (руб)", value=55.0, step=1.0)
cost_token_per_acc = st.sidebar.number_input("Цена токенов на 1 аккаунт (руб)", value=5.0, step=0.5) 

st.sidebar.markdown("---")
st.sidebar.header("🏢 Постоянные расходы")
opex_fixed = st.sidebar.number_input("Сервер/Прокси/ПО (OpEx)", value=67020.0, step=100.0)
salary_fixed = st.sidebar.number_input("ФОТ (Зарплаты)", value=250000.0, step=1000.0)

# --- РАСЧЕТЫ ---

# 1. Физические показатели
accounts_needed = target_msgs_month / msgs_per_account

# 2. Unit-экономика
full_account_cost = cost_raw_account + cost_token_per_acc
unit_cost = full_account_cost / msgs_per_account 
unit_margin = price_per_msg - unit_cost          
unit_margin_percent = (unit_margin / price_per_msg) * 100 if price_per_msg > 0 else 0

# 3. Общая экономика (P&L)
revenue = target_msgs_month * price_per_msg
total_variable_costs = accounts_needed * full_account_cost 

gross_profit = revenue - total_variable_costs 
total_fixed_costs = opex_fixed + salary_fixed
net_profit = gross_profit - total_fixed_costs 
net_margin_percent = (net_profit / revenue) * 100 if revenue > 0 else 0

# --- ВИЗУАЛИЗАЦИЯ ---

col1, col2, col3, col4 = st.columns(4)

col1.metric("Выручка", f"{revenue:,.0f} ₽")
col2.metric("Нужно аккаунтов", f"{int(accounts_needed)} шт") # int гарантирует отсутствие дробей здесь

col3.metric(
    "Unit-маржа (с 1 смс)", 
    f"{unit_margin:.2f} ₽ ({unit_margin_percent:.0f}%)",
    delta_color="normal" if unit_margin > 0 else "inverse"
)

col4.metric(
    "Чистая прибыль (Рентабельность)", 
    f"{net_profit:,.0f} ₽ ({net_margin_percent:.1f}%)", 
    delta=f"{net_profit:,.0f} ₽",
    delta_color="normal" if net_profit > 0 else "inverse"
)

st.markdown("---")

c1, c2 = st.columns([1, 2])

with c1:
    st.info(f"""
    **🧩 Структура 1 сообщения:**
    * Цена продажи: **{price_per_msg:.2f} ₽**
    * Себестоимость: **-{unit_cost:.2f} ₽**
    * **Маржа:** **{unit_margin:.2f} ₽**
    
    *Расход на покупку {int(accounts_needed)} аккаунтов: {total_variable_costs:,.0f} ₽*
    """)

with c2:
    if net_profit >= 0:
        st.success(f"✅ **Бизнес прибылен!** Рентабельность: **{net_margin_percent:.1f}%**")
    else:
        st.error(f"⚠️ **Убыток: {net_profit:,.0f} руб.**")
        st.write("**Как выйти в 0 (Безубыточность)?**")
        
        break_even_price = (total_fixed_costs + total_variable_costs) / target_msgs_month
        st.write(f"1️⃣ Поднять цену до **{break_even_price:.2f} ₽**")
        
        if unit_margin > 0:
            needed_volume = total_fixed_costs / unit_margin
            st.write(f"2️⃣ Увеличить объем до **{int(needed_volume):,}** сообщений")
        else:
            st.write(f"2️⃣ ❌ Масштабирование не поможет (Unit-маржа отрицательная)")

        money_available_for_vars = revenue - total_fixed_costs
        if money_available_for_vars > 0:
            needed_lifespan = (target_msgs_month * full_account_cost) / money_available_for_vars
            st.write(f"3️⃣ Увеличить живучесть аккаунта до **{int(needed_lifespan)}** сообщений")
        else:
             st.write(f"3️⃣ ❌ Нужно снижать постоянные расходы (ФОТ/Серверы)")

fig = go.Figure(go.Waterfall(
    name = "Finance", orientation = "v",
    measure = ["relative", "relative", "relative", "total"],
    x = ["Выручка", "Аккаунты (COGS)", "Постоянные (OpEx+ФОТ)", "Чистая прибыль"],
    textposition = "outside",
    text = [f"{revenue/1000:.0f}k", f"-{total_variable_costs/1000:.0f}k", f"-{total_fixed_costs/1000:.0f}k", f"{net_profit/1000:.0f}k"],
    y = [revenue, -total_variable_costs, -total_fixed_costs, net_profit],
    connector = {"line":{"color":"rgb(63, 63, 63)"}},
    decreasing = {"marker":{"color":"#EF553B"}},
    increasing = {"marker":{"color":"#00CC96"}},
    totals = {"marker":{"color":"#636EFA"}}
))
st.plotly_chart(fig, use_container_width=True)