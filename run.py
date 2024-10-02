import requests
import re
import os
import time
import hashlib
import logging




# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

headers = {
    "Connection": "keep-alive",
    "sec-ch-ua-platform": "Android",
    "User-Agent": "Mozilla/5.0 (Linux; Android 14; HBP-AL00 Build/AP2A.240905.003) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.5 Mobile Safari/537.36",
    "sec-ch-ua": 'Chromium";v="130", "Android WebView";v="130", "Not?A_Brand";v="99"',
    "sec-ch-ua-mobile": "?1",
    "Accept": "*/*",
    "Origin": "https://www.cnblogs.com",
    "X-Requested-With": "mark.via.gp",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://www.cnblogs.com/",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-TW,zh-SG;q=0.9,zh;q=0.8,en-US;q=0.7,en;q=0.6,ja-JP;q=0.5,ja;q=0.4"
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

# 文件名最大长度
MAX_FILENAME_LENGTH = 105

# 生成安全的文件名
def safe_filename(artist, title):
    filename = f"{artist} - {title}.lrc"
    if len(filename) > MAX_FILENAME_LENGTH - len("lyrics/"):
        hash_obj = hashlib.md5(filename.encode('utf-8'))
        hash_str = hash_obj.hexdigest()
        filename = f"{hash_str}.lrc"
    return f"lyrics/{filename}"

    # 删除信息
    no_header_lyrics = re.sub(r'^\[.*?]( |)*(作词|作詞|作曲|编曲|編曲|演唱|歌|音乐|词曲|词|詞|曲|制作|填词|配器|演奏|作曲者|作词者|监制|录制)( |)*(:|：).*', '', lyrics, flags=re.MULTILINE)

    # 保留毫秒部分的前两位
    formatted_lyrics = re.sub(
    r'(\d{2}:\d{2})\.(\d{3})',
    lambda m: f"{m.group(1)}.{m.group(2)[:2]}",  # 仅取毫秒的前两位
    no_header_lyrics
)
    # 处理连续的多余空行
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

    # 检查歌词是否纯音乐
    if "纯音乐，请欣赏" not in lyrics:
        final_lyrics = clean_and_format_lyrics(lyrics)
        filename = safe_filename(artist, title)
        try:
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(final_lyrics)
            logging.info(f"Lyrics for {title} by {artist} saved successfully.")
        except IOError as e:
            logging.error(f"Error saving lyrics for {title} by {artist}: {e}")
        time.sleep(1)

print("歌词已成功下载并保存。")
