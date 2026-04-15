import re
import pymorphy3
import pickle
import os

morph = pymorphy3.MorphAnalyzer()


if os.path.exists('my_model.pkl'):
    with open('my_model.pkl', 'rb') as f:
        vectorizer, model = pickle.load(f)
else:
    vectorizer, model = None, None

def get_lemmas(text):
    if not text:
        return []
    words = re.findall(r'\b[а-яёa-z0-9]+\b', str(text).lower())
  
    return [morph.parse(w)[0].normal_form for w in words]

def analyze_sentiment(texts):
    """Анализ настроения через Machine Learning (Logistic Regression)"""
    if model and vectorizer:
       
        texts_lower = [str(t).lower() for t in texts]
        
        X = vectorizer.transform(texts_lower)
        
        preds = model.predict(X)
        
        mapping = {1: 'Позитивный 😊', 0: 'Негативный 😡', 2: 'Нейтральный 😐'}
        return [mapping.get(p, "Нейтральный 😐") for p in preds]
        
    return ["Модель не загружена"] * len(texts)

def classify_theme(text):
    """Определение темы сообщения."""
    t_lower = str(text).lower()
    themes_map = {
        'Деньги / Билеты': ['цена', 'скольк', 'стоимост', 'купит', 'билет', 'продат', 'прайс', 'чек', 'дорог', 'дешев'],
        'Логистика / Города': ['минск', 'гомел', 'брест', 'витебск', 'гродн', 'могилев', 'когда', 'где', 'приезд', 'тур'],
        'Качество / Эмоции': ['красив', 'мощн', 'крут', 'шикарн', 'голос', 'концерт', 'шоу', 'артист', 'восторг', 'атмосфер']
    }
    for theme, keywords in themes_map.items():
        if any(k in t_lower for k in keywords):
            return theme
    return 'Общее'

def calculate_priority_score(row):
    """Оценка важности комментария (1-5)."""
    text = str(row.get('comment_text', '')).lower()
    score = 1.0
    if len(text) > 80: score += 1.0
    if '?' in text: score += 1.0
    if any(k in text for k in ['цена', 'купить', 'билет', 'заказать', 'сколько', 'стоимость']): 
        score += 2.0
    return min(round(score, 1), 5.0)
