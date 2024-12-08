import requests
import re
import hashlib
import logging
import os

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 14; HBP-AL00 Build/AP2A.240905.003) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.5 Mobile Safari/537.36",
    "Origin": "https://www.cnblogs.com",
    "X-Requested-With": "mark.via.gp",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://www.cnblogs.com/"
}

MAX_FILENAME_LENGTH = 105

# 安全文件名生成
def safe_filename(artist, title):
    filename = f"{artist} - {title}.lrc"
    if len(filename) > MAX_FILENAME_LENGTH - len("lyrics/"):
        hash_obj = hashlib.md5(filename.encode('utf-8'))
        hash_str = hash_obj.hexdigest()
        filename = f"{hash_str}.lrc"
    return f"lyrics/{filename}"

# 處理歌詞
def safe_lyrics(lyrics):
    """
    格式化歌词，修改歌手信息行的时间戳，去除毫秒部分，并调整格式
    """
    modified_lines = []  # 用來存儲修改過的行（歌手信息行）
    regular_lyrics = []  # 用來存儲正常的歌詞行

    # 只保留分钟:秒，移除毫秒部分
    formatted_lyrics = re.sub(
        r'(\d{2}:\d{2})\.(\d{2,3})',  # 正则匹配时间戳
        r'\1',  # 保留分钟:秒
        lyrics
    )

    # 处理歌词行
    for line in formatted_lyrics.splitlines():
        # 修改正则表达式，支持中文冒号与英文冒号
        match = re.match(r'^\[(\d{2}:\d{2})\](.*?)(作词|作詞|作曲|编曲|編曲|演唱|歌|音乐|词曲|词|詞|曲|制作|填词|配器|演奏|作曲者|作词者|监制|录制|古筝|二胡|人声调校|混音|母带)(:|：)', line)
        if match:
            # 保留歌手信息行内容，将时间戳替换为 [999:99]
            modified_lines.append(f'[999:99]{match.group(2)}')
        else:
            # 普通歌词行保留原时间戳
            regular_lyrics.append(line)

    # 合并并去除多余空行
    final_lyrics = '\n'.join(regular_lyrics) + '\n' + '\n'.join(modified_lines)
    return re.sub(r'\n+', '\n', final_lyrics).strip()

# 獲取播放列表數據
def fetch_playlist_data(api_url):
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching playlist data from {api_url}: {e}")
        return None

# 獲取歌詞
def fetch_lyrics(lyrics_url):
    try:
        lyrics_response = requests.get(lyrics_url, headers=headers)
        lyrics_response.raise_for_status()
        return lyrics_response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching lyrics from {lyrics_url}: {e}")
        return None

# 處理播放列表中的每首歌
def process_song(song):
    artist = re.sub(r' ?/ ?', ' ', song.get('author', song.get('artist', '')))
    title = re.sub(r' ?/ ?', ' ', song.get('title', song.get('name', '')))
    lyrics_url = song['lrc']

    lyrics = fetch_lyrics(lyrics_url)
    if not lyrics or "纯音乐，请欣赏" in lyrics:
        return

    final_lyrics = safe_lyrics(lyrics)
    filename = safe_filename(artist, title)

    try:
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(final_lyrics)
        logging.info(f"Lyrics for {title} by {artist} saved successfully.")
    except IOError as e:
        logging.error(f"Error saving lyrics for {title} by {artist}: {e}")

# 主流程
def main(api_url):
    os.makedirs("lyrics", exist_ok=True)  # 确保目录存在

    playlist_data = fetch_playlist_data(api_url)
    if not playlist_data:
        logging.error("No playlist data available, exiting...")
        return

    for song in playlist_data:
        process_song(song)

    logging.info("歌詞已成功下載並保存。")

# 替换为实际的 API 地址
main(api_url)
