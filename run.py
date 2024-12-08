import requests
import re
import hashlib
import logging

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

def safe_lyrics(lyrics):
    modified_lines = []  # 用來存儲修改過的行（歌手信息行）
    regular_lyrics = []  # 用來存儲正常的歌詞行

    formatted_lyrics = re.sub(
        r'(\d{2}:\d{2})\.(\d{3})',
        lambda m: f"{m.group(1)}.{m.group(2)[:2]}",  # 僅取毫秒的前兩位
        lyrics
    )

    for line in formatted_lyrics.splitlines():
        match = re.match(r'^\[(\d{2}:\d{2})\](.*?)(作词|作詞|作曲|编曲|編曲|演唱|歌|音乐|词曲|词|詞|曲|制作|填词|配器|演奏|作曲者|作词者|监制|录制)', line)
        if match:
            modified_lines.append(f'[999:99]{match.group(2)}')
        else:
            regular_lyrics.append(line)

    final_lyrics = re.sub(r'\n+', '\n', '\n'.join(regular_lyrics))
    final_lyrics += '\n' + '\n'.join(modified_lines)

    return final_lyrics.strip()

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
    playlist_data = fetch_playlist_data(api_url)
    if not playlist_data:
        logging.error("No playlist data available, exiting...")
        return

    for song in playlist_data:
        process_song(song)

    logging.info("歌詞已成功下載並保存。")

main(api_url)
