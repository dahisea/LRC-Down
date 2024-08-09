import requests
import re
import os
import time

# 定义API URL
api_url = 

# 获取播放列表数据
response = requests.get(api_url)

# 打印响应状态码和内容以进行调试
print(f"Response Status Code: {response.status_code}")
print(f"Response Text: {response.text}")

try:
    playlist_data = response.json()
except requests.exceptions.JSONDecodeError as e:
    print(f"JSONDecodeError: {e}")
    playlist_data = []

# 创建保存歌词文件的目录
os.makedirs("lyrics", exist_ok=True)

# 遍历播放列表中的每首歌
for song in playlist_data:
    try:
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
        
        # 打印成功消息
        print(f"'{title}' by {artist} 的歌词已成功下载并保存。")
        
    except Exception as e:
        print(f"'{title}' by {artist} の歌詞取得エラー: {e}")
    
    # リクエストが頻繁になりすぎないように1秒間停止
    time.sleep(1)

print("歌词已成功下载并保存。")
