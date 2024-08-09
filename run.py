import requests
import re
import os
import time





# 自定义请求头
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}

# 获取播放列表数据
response = requests.get(api_url, headers=headers)
playlist_data = response.json()

# 创建保存歌词文件的目录
os.makedirs("lyrics", exist_ok=True)

# 遍历播放列表中的每首歌
for song in playlist_data:
    # 获取艺术家和歌曲名
    artist = re.sub(r' ?/ ?', ' ', song['author'])
    title = re.sub(r' ?/ ?', ' ', song['title'])

    
    # 获取歌词URL
    lyrics_url = song['lrc']
    
    # 获取歌词数据
    lyrics_response = requests.get(lyrics_url, headers=headers)
    lyrics = lyrics_response.text
    
    # 定义歌词文件名
    filename = f"lyrics/{artist} - {title}.lrc"
    
    # 保存歌词到文件
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(lyrics)
    
    # 增加时间间隔1秒
    time.sleep(1)

print("歌词已成功下载并保存。")
