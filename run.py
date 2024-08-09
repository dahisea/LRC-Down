import requests
import re
import os
import time
import hashlib







headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}

# プレイリストデータを取得
response = requests.get(api_url, headers=headers)
playlist_data = response.json()

# 歌詞ファイルを保存するディレクトリを作成
os.makedirs("lyrics", exist_ok=True)

# ファイル名の最大長 (Windows システムでは通常 260 文字に制限される)
MAX_FILENAME_LENGTH = 100

# 安全なファイル名を生成する関数を定義
def safe_filename(artist, title):
    # 初期のファイル名
    filename = f"{artist} - {title}.lrc"
    
    # ファイル名が長すぎる場合、ハッシュを生成してファイル名を短縮
    if len(filename) > MAX_FILENAME_LENGTH - len("lyrics/"):
        hash_obj = hashlib.md5(filename.encode('utf-8'))
        hash_str = hash_obj.hexdigest()
        filename = f"{hash_str}.lrc"
    
    return f"lyrics/{filename}"

# プレイリスト内の各曲をループ
for song in playlist_data:
    # アーティスト名と曲名を取得
    artist = re.sub(r' ?/ ?', ' ', song['author'])
    title = re.sub(r' ?/ ?', ' ', song['title'])
    
    # 歌詞のURLを取得
    lyrics_url = song['lrc']
    
    # 歌詞データを取得
    lyrics_response = requests.get(lyrics_url, headers=headers)
    lyrics = lyrics_response.text
    
    # 正規表現を使用して「作词」、「作曲」、「编曲」、「制作人」を含む行を削除
    lyrics = re.sub(r'^\[\d{2}:\d{2}:\d{2}\] *[作词|作曲|编曲|制作人] *:.*$', '', lyrics, flags=re.MULTILINE)
    
    # 歌詞に「纯音乐，请欣赏」が含まれている場合、保存をスキップ
    if "纯音乐，请欣赏" in lyrics:
        continue
    
    # 安全なファイル名を使用
    filename = safe_filename(artist, title)
    
    # 歌詞をファイルに保存
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(lyrics)
    
    # 1 秒の時間間隔を追加
    time.sleep(1)

print("歌詞は正常にダウンロードされ、保存されました。")
