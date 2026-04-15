import json
import sqlite3
import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")

def normalize_comment(item):
    """Приводит любой формат комментария к единой структуре"""
    comment = {}

    if isinstance(item, dict):
        if 'text' in item:
            comment['comment_text'] = item.get('text', '')
            comment['comment_date'] = item.get('timestamp')
            comment['comment_author'] = item.get('ownerUsername') or item.get('owner', {}).get('username', '')
            comment['post_url'] = item.get('postUrl') or item.get('post_url', '')
            comment['likes_count'] = item.get('likesCount', 0)
            comment['replies_count'] = item.get('repliesCount', 0)

    if 'id' in item and 'text' in item and 'ownerUsername' in item:
        comment['comment_text'] = item.get('text', '')
        comment['comment_date'] = item.get('timestamp')
        comment['comment_author'] = item.get('ownerUsername', '')
        comment['post_url'] = item.get('postUrl', '')
        comment['likes_count'] = 0
        comment['replies_count'] = 0

    return comment


def load_json_files():
    all_comments = []
    for file in DATA_DIR.glob("*.json"):
        try:
            with open(file, encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                for item in data:
                    norm = normalize_comment(item)
                    if norm and norm.get('comment_text'):
                        all_comments.append(norm)
            elif isinstance(data, dict):
                for key in ['comments', 'data', 'items']:
                    if key in data and isinstance(data[key], list):
                        for item in data[key]:
                            norm = normalize_comment(item)
                            if norm and norm.get('comment_text'):
                                all_comments.append(norm)
        except Exception as e:
            print(f"Ошибка при чтении {file.name}: {e}")
    
    return pd.DataFrame(all_comments)


def create_database():
    df = load_json_files()
    if df.empty:
        print("❌ Не найдено ни одного комментария в папке data/")
        return

    if 'comment_date' in df.columns:
        df['comment_date'] = pd.to_datetime(df['comment_date'], errors='coerce')
    
    conn = sqlite3.connect('instagram_data.db')
    df.to_sql('comments', conn, if_exists='replace', index=False)
    conn.close()
    print(f"✅ База успешно создана! Загружено комментариев: {len(df)}")


if __name__ == "__main__":
    create_database()