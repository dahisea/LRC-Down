import requests
import re
import os
import time
import hashlib
import logging






# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}

# 获取播放列表数据
try:
    response = requests.get(api_url, headers=headers)
    response.raise_for_status()
    playlist_data = response.json()
except requests.exceptions.RequestException as e:
    logging.error(f"Error fetching playlist data: {e}")
    exit(1)

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


def clean_and_format_lyrics(lyrics):
    # 删除作曲信息
    no_header_lyrics = re.sub(r'^\[\d{2}:\d{2}.\d{3}\] *(作词|作曲|编曲|制作人|演唱|音乐|词曲|编曲|制作|填词|配器|编曲|演奏|作曲者|作词者|主唱|吉他手|鼓手|贝斯手|合成器|混音|录音|监制|录制) *:.*$', '', lyrics, flags=re.MULTILINE)
    
    # 替换时间戳的小数点为冒号，保留毫秒部分的前两位
    formatted_lyrics = re.sub(r'(\d{2}:\d{2})\.(\d{3})', lambda m: f"{m.group(1)}:{m.group(2)[:2]}", no_header_lyrics)
    
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
    try:
        lyrics_response = requests.get(lyrics_url, headers=headers)
        lyrics_response.raise_for_status()
        lyrics = lyrics_response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching lyrics for {title} by {artist}: {e}")
        continue

    # 检查歌词中是否包含“纯音乐，请欣赏”
    if "纯音乐，请欣赏" not in lyrics:
        cleaned_lyrics = clean_and_format_lyrics(lyrics)
        filename = safe_filename(artist, title)
        try:
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(cleaned_lyrics)
            logging.info(f"Lyrics for {title} by {artist} saved successfully.")
        except IOError as e:
            logging.error(f"Error saving lyrics for {title} by {artist}: {e}")
        time.sleep(1)

print("歌词已成功下载并保存。")
