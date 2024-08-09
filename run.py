import requests
import re
import os
import time

# 定义API URL
api_url = 

# 获取播放列表数据
response = requests.get(api_url)
playlist_data = response.json()

# 创建保存歌词文件的目录
os.makedirs("lyrics", exist_ok=True)

# 遍历播放列表中的每首歌
for song in playlist_data:
    # 获取艺术家和歌曲名
    artist = re.sub(r'[ / ]', ' ', song['author'])
    title = song['title']
    
    # 获取歌词URL
    lyrics_url = song['lrc']
    
    # 获取歌词数据
    lyrics_response = requests.get(lyrics_url)
    lyrics = lyrics_response.text
    
    # 定义歌词文件名
    filename = f"lyrics/{artist} - {title}.lrc"
    
    # 保存歌词到文件
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(lyrics)


        # リクエストが頻繁になりすぎないように1秒間停止
        time.sleep(1)
    except requests.exceptions.RequestException as e:
        print(f"'{title}' by {artist} の歌詞取得エラー: {e}")

print("歌词已成功下载并保存。")
