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
MAX_FILENAME_LENGTH = 105

# 生成安全的文件名
def safe_filename(artist, title):
    filename = f"{artist} - {title}.lrc"
    if len(filename) > MAX_FILENAME_LENGTH - len("lyrics/"):
        hash_obj = hashlib.md5(filename.encode('utf-8'))
        hash_str = hash_obj.hexdigest()
        filename = f"{hash_str}.lrc"
    return f"lyrics/{filename}"


def clean_and_format_lyrics(lyrics):
    # 使用正则表达式删除
    no_header_lyrics = re.sub(r'^\[\d{2}:\d{2}\.\d{3}\]( |)*(作词|作詞|作曲|编曲|編曲|编曲 Arranger|制作人|制作人 Producer|演唱|歌|音乐|词曲|词|詞|曲|制作|填词|配器|演奏|作曲者|作词者|主唱|吉他手|鼓手|贝斯手|合成器|混音|录音|监制|录制|出品 Produced by|母带制作 Mastering Engineer|混音师 Mixing Engineer|录音师 Recording Engineer|乐器录音师 Instrumental Recording Engineer|乐器录音棚 Instrumental Recording Studio|人声录音师 Vocal Recording Engineer|人声录音棚 Vocal Recording Studio|和声 Backing Vocal|架子鼓 Drums|电吉他 Electric Guitar|木吉他 Acoustic Guitar|人声 Vocal Artist|筝 Koto|二胡 Erhu|尺八 Shakuhachi|津轻三味线 Tsugaru-Shamisen|乐队配器 Orchestrator|乐队 Orchestra|指挥 Conductor|录音棚 Recording Studio|舞台监督 Orchestra Stage Manager|乐团经理 Orchestra Manager|音乐监制 Music Supervisor|联合制作 Co-produced by|录音现场指导 Scoring Sessions Director)( |)*(:|：).*', '', lyrics, flags=re.MULTILINE)
    # 替换时间戳的小数点为冒号，保留毫秒部分的前两位
    formatted_lyrics = re.sub(r'(\d{2}:\d{2})\.(\d{3})', lambda m: f"{m.group(1)}:{str(round(int(m.group(2)) / 10)).zfill(2)}", no_header_lyrics)
    # 删除连续的多余空行
    final_lyrics = re.sub(r'\n+', '\n', formatted_lyrics)
    return final_lyrics.strip()


# 处理播放列表中的每首歌
for song in playlist_data:
    artist = re.sub(r' ?/ ?', ' ', song.get('author', song.get('artist', '')))
    title = re.sub(r' ?/ ?', ' ', song.get('title', song.get('name', '')))
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
        final_lyrics = clean_and_format_lyrics(lyrics)
        filename = safe_filename(artist, title)
        try:
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(final_lyrics)
            logging.info(f"Lyrics for {title} by {artist} saved successfully.")
        except IOError as e:
            logging.error(f"Error saving lyrics for {title} by {artist}: {e}")
        time.sleep(0.2)

print("歌词已成功下载并保存。")
