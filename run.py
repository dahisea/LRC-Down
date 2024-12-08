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
    """
    生成安全的文件名，确保文件名不会超出最大长度
    """
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
        r'(\d{2}:\d{2})\.(\d{3})',  # 正则匹配时间戳
        r'\1',  # 保留分钟:秒
        lyrics
    )

    # 处理歌词行
    for line in formatted_lyrics.splitlines():
        match = re.match(r'^\[(\d{2}:\d{2})\](.*?)(作词|作詞|作曲|编曲|編曲|演唱|歌|音乐|词曲|词|詞|曲|制作|填词|配器|演奏|作曲者|作词者|监制|录制)', line)
        if match:
            modified_lines.append(f'[999:99]{match.group(2)}')  # 歌手信息行，时间戳替换为 999:99
        else:
            regular_lyrics.append(line)  # 普通歌词行

    # 合并并去除多余空行
    final_lyrics = '\n'.join(regular_lyrics) + '\n' + '\n'.join(modified_lines)
    return re.sub(r'\n+', '\n', final_lyrics).strip()

# 获取播放列表数据
def fetch_playlist_data(api_url):
    """
    获取歌曲列表数据，返回 JSON 格式的响应
    """
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # 如果请求失败，抛出异常
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching playlist data from {api_url}: {e}")
        return None

# 获取歌词
def fetch_lyrics(lyrics_url):
    """
    获取歌词数据，返回歌词文本
    """
    try:
        lyrics_response = requests.get(lyrics_url, headers=headers)
        lyrics_response.raise_for_status()  # 如果请求失败，抛出异常
        return lyrics_response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching lyrics from {lyrics_url}: {e}")
        return None

# 处理播放列表中的每首歌
def process_song(song):
    """
    处理每首歌的歌词，保存歌词到文件
    """
    artist = re.sub(r' ?/ ?', ' ', song.get('author', song.get('artist', '')))
    title = re.sub(r' ?/ ?', ' ', song.get('title', song.get('name', '')))
    lyrics_url = song.get('lrc')

    if not lyrics_url:
        logging.warning(f"Song '{title}' by {artist} does not have lyrics URL.")
        return

    lyrics = fetch_lyrics(lyrics_url)
    if not lyrics or "纯音乐，请欣赏" in lyrics:  # 跳过纯音乐
        return

    final_lyrics = safe_lyrics(lyrics)
    filename = safe_filename(artist, title)

    # 如果文件已存在，覆盖它
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(final_lyrics)
        logging.info(f"Lyrics for {title} by {artist} saved successfully.")
    except IOError as e:
        logging.error(f"Error saving lyrics for {title} by {artist}: {e}")

# 主流程
def main(api_url):
    """
    主流程，获取并处理歌曲数据
    """
    os.makedirs("lyrics", exist_ok=True)  # 确保目录存在

    playlist_data = fetch_playlist_data(api_url)
    if not playlist_data:
        logging.error("No playlist data available, exiting...")
        return

    for song in playlist_data:
        process_song(song)

    logging.info("歌詞已成功下載並保存。")

# 设置你的 API URL
main(api_url)
