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

# 获取播放列表数据
response = requests.get(api_url, headers=headers)
playlist_data = response.json()

# 创建保存歌词文件的目录
os.makedirs("lyrics", exist_ok=True)

# 文件名最大长度（Windows系统通常限制为260个字符）
MAX_FILENAME_LENGTH = 100

# 生成安全的文件名
def safe_filename(artist, title):
    filename = f"{artist} - {title}.lrc"
    if len(filename) > MAX_FILENAME_LENGTH - len("lyrics/"):
        hash_obj = hashlib.md5(filename.encode('utf-8'))
        hash_str = hash_obj.hexdigest()
        filename = f"{hash_str}.lrc"
    return f"lyrics/{filename}"

# 清理并格式化歌词，删除无效的歌词行和作曲信息，替换时间戳的小数点为冒号，保留毫秒部分的2位数
def clean_and_format_lyrics(lyrics):
    # 删除作曲信息
    lyrics = re.sub(r'^\[\d{2}:\d{2}.\d{3}\] *[作词|作曲|编曲|制作人] *:.*$', '', lyrics, flags=re.MULTILINE)
    
    # 替换时间戳的小数点为冒号，保留毫秒部分的前两位
    formatted_lyrics = re.sub(r'(\d{2}:\d{2})\.(\d{3})', lambda m: f"{m.group(1)}:{m.group(2)[:2]}", lyrics)
    
    # 删除无效的“[时间] 空行”行
    cleaned_lyrics = re.sub(r'^\[\d{2}:\d{2}:\d{2}\]\s*$', '', formatted_lyrics, flags=re.MULTILINE)
    
    # 删除连续的多余空行
    cleaned_lyrics = re.sub(r'\n+', '\n', cleaned_lyrics)
    
    return cleaned_lyrics.strip()

# 处理播放列表中的每首歌
for song in playlist_data:
    artist = re.sub(r' ?/ ?', ' ', song['author'])
    title = re.sub(r' ?/ ?', ' ', song['title'])
    lyrics_url = song['lrc']
    lyrics_response = requests.get(lyrics_url, headers=headers)
    lyrics = lyrics_response.text

    # 检查歌词中是否包含“纯音乐，请欣赏”
    if "纯音乐，请欣赏" not in lyrics:
        cleaned_lyrics = clean_and_format_lyrics(lyrics)
        filename = safe_filename(artist, title)
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(cleaned_lyrics)
        time.sleep(1)

print("歌词已成功下载并保存。")
