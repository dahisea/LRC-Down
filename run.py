import requests
import re
import os
import time
import hashlib




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

# 文件名最大长度（Windows系统通常限制为260个字符）
MAX_FILENAME_LENGTH = 55

# 定义一个函数来生成安全的文件名
def safe_filename(artist, title):
    # 初始文件名
    filename = f"{artist} - {title}.lrc"
    
    # 如果文件名长度过长，则生成一个hash并缩短文件名
    if len(filename) > MAX_FILENAME_LENGTH - len("lyrics/"):
        hash_obj = hashlib.md5(filename.encode('utf-8'))
        hash_str = hash_obj.hexdigest()
        filename = f"{hash_str}.lrc"
    
    return f"lyrics/{filename}"

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
    
    # 使用安全的文件名
    filename = safe_filename(artist, title)
    
    # 保存歌词到文件
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(lyrics)
    
    # 增加时间间隔1秒
    time.sleep(1)

print("歌词已成功下载并保存。")
