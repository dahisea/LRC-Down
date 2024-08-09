import requests
import re
import os
import time

# API URLを定義
api_url = 

# リクエストヘッダーを定義（User-Agentを含む）
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

try:
    # プレイリストデータを取得
    response = requests.get(api_url, headers=headers)
    response.raise_for_status()
    playlist_data = response.json()
except requests.exceptions.RequestException as e:
    print(f"プレイリストデータの取得エラー: {e}")
    playlist_data = []

# 歌詞ファイルを保存するディレクトリを作成
os.makedirs("lyrics", exist_ok=True)

# プレイリスト内の各曲をループ
for song in playlist_data:
    try:
        # アーティスト名と曲名を取得
        artist = re.sub(r'[ / ]', ' ', song['author'])
        title = re.sub(r'[ / ]', ' ', song['title'])
        
        # 歌詞URLを取得
        lyrics_url = song['lrc']
        
        # 歌詞データを取得
        lyrics_response = requests.get(lyrics_url, headers=headers)
        lyrics_response.raise_for_status()
        lyrics = lyrics_response.text
        
        # 歌詞ファイル名を定義
        filename = f"lyrics/{artist} - {title}.lrc"
        
        # 歌詞をファイルに保存
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(lyrics)
        
        print(f"'{title}' by {artist} の歌詞を正常に保存しました。")
        
        # リクエストが頻繁になりすぎないように1秒間停止
        time.sleep(1)
    except requests.exceptions.RequestException as e:
        print(f"'{title}' by {artist} の歌詞取得エラー: {e}")

print("歌詞が正常にダウンロードされ、保存されました。")
