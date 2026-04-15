import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from analyzer import analyze_sentiment, calculate_priority_score, classify_theme, get_lemmas


st.set_page_config(page_title="Insta Analytics Search", layout="wide", initial_sidebar_state="collapsed")


st.markdown("""
<style>
    /* Убираем боковую панель полностью */
    [data-testid="collapsedControl"] { display: none; }
    section[data-testid="stSidebar"] { display: none; }

    /* Стилизация строки поиска (инпута) - адаптивно под тему */
    .stTextInput input {
        border: 2px solid var(--text-color) !important;
        border-radius: 30px !important;
        padding: 15px 25px !important;
        font-size: 18px !important;
        background-color: transparent !important;
        color: var(--text-color) !important;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.05);
    }
    .stTextInput input:focus {
        border: 2px solid #E83E8C !important;
        box-shadow: 0px 0px 10px rgba(232, 62, 140, 0.3) !important;
    }

    /* Кнопка поиска - ВСЕГДА РОЗОВАЯ, ТЕКСТ ВСЕГДА БЕЛЫЙ */
    .stButton>button, .stButton>button p {
        background-color: #E83E8C !important;
        color: #FFFFFF !important;
        border-radius: 30px !important;
        padding: 10px 30px !important;
        font-weight: bold !important;
        font-size: 18px !important;
        border: none !important;
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #C2185B !important; }

    /* Карточки метрик - используют системный цвет фона */
    .metric-card {
        background-color: var(--secondary-background-color); 
        padding: 20px; 
        border-radius: 15px;
        border-left: 5px solid #E83E8C;
        text-align: left; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        color: var(--text-color);
    }
    .metric-card span { font-size: 14px; opacity: 0.7; text-transform: uppercase;}
    .metric-card b { color: #E83E8C !important; font-size: 28px; display: block; margin-top: 5px;}
    
    /* Центрирование радио-кнопок */
    div[role="radiogroup"] { justify-content: center; margin-top: 10px; }
    
    /* Прячем лишние элементы таблиц */
    [data-testid="stDataFrame"] { width: 100% !important; }
</style>
""", unsafe_allow_html=True)



@st.cache_data
def load_data():
    try:
        conn = sqlite3.connect('instagram_data.db')
        c = pd.read_sql("SELECT * FROM comments", conn)
        conn.close()
        c['comment_date'] = pd.to_datetime(c['comment_date'], errors='coerce')
        return c
    except:
        return pd.DataFrame()

comments_all = load_data()





st.markdown("<h1 style='text-align: center; font-size: 48px; margin-bottom: 0;'>Insight Search</h1>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; max-width: 700px; margin: 10px auto 40px auto; font-size: 16px; opacity: 0.9;'>
    Умный анализатор комментариев Instagram. Введите запрос, чтобы мгновенно собрать мнения аудитории, 
    определить тональность (негатив/позитив), выявить главные темы обсуждений (цена, качество, логистика) 
    и найти инсайты для вашего бизнеса.
</div>
""", unsafe_allow_html=True)


col_spacer1, col_search, col_spacer2 = st.columns([1, 4, 1])
with col_search:
    search_query = st.text_input(
        "Поиск", 
        placeholder="Введите URL поста, ключевые слова (через запятую) или текст...",
        label_visibility="collapsed"
    )

    mode = st.radio(
        "Режим", 
        ["🔗 Поиск по URL поста", "🔑 Поиск по ключевым словам", "✍️ Анализ одного текста"],
        label_visibility="collapsed",
        horizontal=True
    )

    st.write("") 
    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
    with btn_col2:
        search_clicked = st.button("Анализировать", use_container_width=True)


st.divider()




if search_clicked:
    if not search_query.strip():
        st.warning("Пожалуйста, введите запрос в строку поиска.")
    else:
        filtered = pd.DataFrame()
        is_manual = False

        if mode == "🔗 Поиск по URL поста":
            term = search_query.strip().lower()
            filtered = comments_all[comments_all['post_url'].astype(str).str.contains(term, na=False, case=False)].copy()
            if filtered.empty:
                st.error("Комментарии к этому посту не найдены в базе.")
        
        elif mode == "🔑 Поиск по ключевым словам":
            keys = []
            for k in search_query.split(','):
                lemmas = get_lemmas(k.strip())
                if lemmas:
                    keys.extend(lemmas)
            
            if not keys:
                st.warning("Введенные слова слишком короткие (нужно больше 2-х букв) или не распознаны.")
            else:
                filtered = comments_all[comments_all['comment_text'].apply(lambda x: any(k in get_lemmas(x) for k in keys))].copy()
                if filtered.empty:
                    st.error("По вашим ключевым словам ничего не найдено.")
                
        elif mode == "✍️ Анализ одного текста":
            is_manual = True
            filtered = pd.DataFrame([{'comment_text': search_query, 'comment_author': 'Вы', 'comment_date': pd.Timestamp.now()}])


        if not filtered.empty:
            with st.spinner('Анализируем данные...'):
                filtered['sentiment'] = analyze_sentiment(filtered['comment_text'].tolist())
                filtered['theme'] = filtered['comment_text'].apply(classify_theme)
                filtered['priority'] = filtered.apply(calculate_priority_score, axis=1)

            st.markdown("<h2 style='margin-bottom: 20px;'>Результаты анализа</h2>", unsafe_allow_html=True)

   
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.markdown(f'<div class="metric-card"><span>Проанализировано</span><b>{len(filtered)} шт.</b></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="metric-card"><span>Общий настрой</span><b>{filtered["sentiment"].mode()[0]}</b></div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="metric-card"><span>Главная тема</span><b>{filtered["theme"].mode()[0]}</b></div>', unsafe_allow_html=True)
            with c4: st.markdown(f'<div class="metric-card"><span>Ср. приоритет (1-5)</span><b>{filtered["priority"].mean():.1f}</b></div>', unsafe_allow_html=True)

            st.write("<br>", unsafe_allow_html=True)

           
            if not is_manual and len(filtered) > 1:
                g_col1, g_col2 = st.columns(2)
                
                theme_colors = ['#E83E8C', '#8884d8', '#82ca9d'] 

                with g_col1:
                    fig_pie = px.pie(filtered, names='sentiment', title="Распределение настроений",
                                     color_discrete_sequence=theme_colors)
                    fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig_pie, use_container_width=True)

                with g_col2:
                    text_for_cloud = " ".join(filtered['comment_text'].astype(str))
                    wc = WordCloud(width=800, height=500, background_color=None, mode="RGBA", colormap="RdPu").generate(text_for_cloud)
                    fig, ax = plt.subplots(figsize=(8, 5))
                    fig.patch.set_alpha(0) 
                    ax.imshow(wc, interpolation='bilinear')
                    ax.axis("off")
                    st.pyplot(fig)

            
            if 'comment_date' in filtered.columns and not filtered['comment_date'].isna().all() and not is_manual:
                st.markdown("<h3>Динамика упоминаний</h3>", unsafe_allow_html=True)
                timeline = filtered.groupby(filtered['comment_date'].dt.date).size().reset_index(name='Количество')
                fig_line = px.line(timeline, x='comment_date', y='Количество', markers=True, 
                                   color_discrete_sequence=['#E83E8C'])
                fig_line.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': "var(--text-color)"})
                st.plotly_chart(fig_line, use_container_width=True)

            
            if not is_manual and len(filtered) > 0:
                st.markdown("<h3>Автоматические инсайты</h3>", unsafe_allow_html=True)
                
              
                negatives = filtered[filtered['sentiment'].str.contains("Негатив", case=False, na=False)]
                if not negatives.empty:
                    top_neg_theme = negatives['theme'].mode()[0]
                    neg_percent = round((len(negatives) / len(filtered)) * 100)
                    insight_text = f"🔴 Обнаружено <b>{neg_percent}%</b> негативных комментариев. Основной негатив аудитории связан с темой: <b>«{top_neg_theme}»</b>."
                else:
                    insight_text = "🟢 Негативных комментариев не обнаружено. Аудитория настроена лояльно!"
                
               
                positives = filtered[filtered['sentiment'].str.contains("Позитив", case=False, na=False)]
                if not positives.empty:
                    top_pos_theme = positives['theme'].mode()[0]
                    insight_text += f"<br><br>🟢 Главный позитив и похвала от пользователей связаны с темой: <b>«{top_pos_theme}»</b>."

                st.markdown(f"""
                <div style='background-color: var(--secondary-background-color); padding: 20px; border-radius: 10px; border-left: 5px solid #E83E8C; color: var(--text-color); margin-bottom: 30px;'>
                    {insight_text}
                </div>
                """, unsafe_allow_html=True)

         
            st.markdown("<h3>Детализация комментариев</h3>", unsafe_allow_html=True)
            
            display_cols = ['priority', 'sentiment', 'theme', 'comment_text', 'comment_author', 'comment_date']
            df_display = filtered[display_cols].sort_values(by='priority', ascending=False)
            df_display.columns = ['Приоритет', 'Тональность', 'Тема', 'Текст комментария', 'Автор', 'Дата']

            st.dataframe(df_display, use_container_width=True, hide_index=True, height=400)

           
            if not is_manual:
                csv = df_display.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="Скачать отчет (CSV)",
                    data=csv,
                    file_name="insight_report.csv",
                    mime="text/csv"
                )