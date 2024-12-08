import requests
import re
import logging
import os









# 日志设置
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
        filename = f"{hashlib.md5(filename.encode('utf-8')).hexdigest()}.lrc"
    return f"lyrics/{filename}"

# 处理歌词内容
def process_lyrics(lyrics):
    regular_lines = []
    special_lines = []

    for line in lyrics.splitlines():
        # 匹配时间标签，去掉毫秒部分
        line = re.sub(r'\[(\d{2}:\d{2})\.\d{2,3}\]', r'[\1]', line)

        # 匹配作词/作曲信息行
        match = re.match(r'^\[\d{2}:\d{2}\]\s*(.*?)(作词|作曲|编曲|古筝|二胡|人声调校|混音|母带)\s*[:：]\s*(.*)', line)
        if match:
            content = f"[999:99]{match.group(1).strip()} {match.group(3).strip()}"
            special_lines.append(content)
        else:
            regular_lines.append(line)

    # 去重和整理输出
    return "\n".join(regular_lines).strip() + "\n" + "\n".join(special_lines).strip()

# 下载歌词数据
def fetch_lyrics(lyrics_url):
    try:
        response = requests.get(lyrics_url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching lyrics from {lyrics_url}: {e}")
        return None

# 保存歌词
def save_lyrics(artist, title, lyrics):
    filename = safe_filename(artist, title)
    try:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(lyrics)
        logging.info(f"Lyrics saved: {filename}")
    except IOError as e:
        logging.error(f"Error saving lyrics: {e}")

# 处理每首歌曲
def process_song(song):
    artist = re.sub(r' ?/ ?', ' ', song.get('author', song.get('artist', 'Unknown Artist')))
    title = re.sub(r' ?/ ?', ' ', song.get('title', song.get('name', 'Unknown Title')))
    lyrics_url = song.get('lrc')

    if not lyrics_url:
        logging.warning(f"No lyrics URL found for {title} by {artist}")
        return

    lyrics = fetch_lyrics(lyrics_url)
    if not lyrics or "纯音乐，请欣赏" in lyrics:
        logging.warning(f"No valid lyrics for {title} by {artist}")
        return

    processed_lyrics = process_lyrics(lyrics)
    save_lyrics(artist, title, processed_lyrics)

# 主程序
def main(api_endpoint):
    os.makedirs("lyrics", exist_ok=True)

    try:
        response = requests.get(api_endpoint, headers=headers)
        response.raise_for_status()
        playlist = response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching playlist data: {e}")
        return

    for song in playlist:
        process_song(song)

    logging.info("所有歌词已处理完成。")

# 替换为您的 API 地址
main(api_url)
