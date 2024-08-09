import requests
import re
import os
import time
import hashlib





# カスタムリクエストヘッダー
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}

# プレイリストデータの取得
response = requests.get(api_url, headers=headers)
playlist_data = response.json()

# 歌詞ファイルを保存するディレクトリを作成
os.makedirs("lyrics", exist_ok=True)

# ファイル名の最大長（Windowsシステムでは通常260文字に制限されています）
MAX_FILENAME_LENGTH = 100

# 安全なファイル名を生成する関数
def safe_filename(artist, title):
    filename = f"{artist} - {title}.lrc"
    if len(filename) > MAX_FILENAME_LENGTH - len("lyrics/"):
        hash_obj = hashlib.md5(filename.encode('utf-8'))
        hash_str = hash_obj.hexdigest()
        filename = f"{hash_str}.lrc"
    return f"lyrics/{filename}"

# 無効な歌詞行を削除し、作曲情報を除去し、タイムスタンプの小数点をコロンに置き換え、ミリ秒部分を2桁に保つ
def clean_and_format_lyrics(lyrics):
    # 作曲情報を削除する
    lyrics = re.sub(r'^\[\d{2}:\d{2}.\d{3}\] *[作词|作曲|编曲|制作人] *:.*$', '', lyrics, flags=re.MULTILINE)
    
    # タイムスタンプの小数点をコロンに置き換え、ミリ秒部分の最初の2桁を保持
    formatted_lyrics = re.sub(r'(\d{2}:\d{2})\.(\d{3})', lambda m: f"{m.group(1)}:{m.group(2)[:2]}", lyrics)
    
    # 「[時間] 空行」の無効な行を削除
    cleaned_lyrics = re.sub(r'^\[\d{2}:\d{2}:\d{2}\]\s*$', '', formatted_lyrics, flags=re.MULTILINE)
    
    # 連続する余分な空行を削除
    cleaned_lyrics = re.sub(r'\n+', '\n', cleaned_lyrics)
    
    return cleaned_lyrics.strip()

# プレイリスト内の各曲を処理
for song in playlist_data:
    artist = re.sub(r' ?/ ?', ' ', song['author'])
    title = re.sub(r' ?/ ?', ' ', song['title'])
    lyrics_url = song['lrc']
    lyrics_response = requests.get(lyrics_url, headers=headers)
    lyrics = lyrics_response.text

    # 歌詞に「純音楽、お楽しみください」が含まれているか確認
    if "純音楽、お楽しみください" not in lyrics:
        cleaned_lyrics = clean_and_format_lyrics(lyrics)
        filename = safe_filename(artist, title)
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(cleaned_lyrics)
        time.sleep(1)

print("歌詞は正常にダウンロードされ、保存されました。")
