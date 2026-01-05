import requests
import re
import logging
import os
import hashlib
import time
from typing import Optional, Dict, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 日志设置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('lyrics_downloader.log', encoding='utf-8')
    ]
)

# 从环境变量获取配置
API_URL = os.getenv('LYRICS_API_URL', '')
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
RETRY_BACKOFF = float(os.getenv('RETRY_BACKOFF', '1.0'))
TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
MAX_FILENAME_LENGTH = int(os.getenv('MAX_FILENAME_LENGTH', '105'))
LYRICS_DIR = os.getenv('LYRICS_DIR', 'lyrics')
RATE_LIMIT_DELAY = float(os.getenv('RATE_LIMIT_DELAY', '0.5'))

headers = {
    "User-Agent": os.getenv(
        'USER_AGENT',
        "Mozilla/5.0 (Linux; Android 14; HBP-AL00 Build/AP2A.240905.003) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.5 Mobile Safari/537.36"
    ),
    "Origin": "https://www.cnblogs.com",
    "X-Requested-With": "mark.via.gp",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://www.cnblogs.com/"
}


def create_session_with_retries() -> requests.Session:
    """创建带重试机制的 requests 会话"""
    session = requests.Session()
    
    # 配置重试策略
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=RETRY_BACKOFF,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session


def safe_filename(artist: str, title: str) -> str:
    """生成安全的文件名"""
    # 移除不安全的字符
    artist = re.sub(r'[<>:"/\\|?*]', '', artist)
    title = re.sub(r'[<>:"/\\|?*]', '', title)
    
    filename = f"{artist} - {title}.lrc"
    
    # 如果文件名过长，使用 MD5 哈希
    if len(filename) > MAX_FILENAME_LENGTH - len(f"{LYRICS_DIR}/"):
        hash_name = hashlib.md5(filename.encode('utf-8')).hexdigest()
        filename = f"{hash_name}.lrc"
        logging.info(f"Filename too long, using hash: {filename}")
    
    return os.path.join(LYRICS_DIR, filename)


def process_lyrics(lyrics: str) -> str:
    """处理歌词内容，整理时间标签和特殊信息"""
    regular_lines = []
    special_lines = []
    
    for line in lyrics.splitlines():
        # 去除空行
        if not line.strip():
            continue
            
        # 匹配时间标签，去掉毫秒部分
        line = re.sub(r'\[(\d{2}:\d{2})\.\d{2,3}\]', r'[\1]', line)
        
        # 匹配作词/作曲等信息行
        match = re.match(
            r'^\[\d{2}:\d{2}\]\s*(.*?)(作词|作曲|编曲|古筝|二胡|人声调校|混音|母带|制作人|吉他)\s*[:：]\s*(.*)',
            line
        )
        
        if match:
            content = f"[999:99]{match.group(1).strip()} {match.group(3).strip()}"
            if content not in special_lines:  # 去重
                special_lines.append(content)
        else:
            regular_lines.append(line)
    
    # 组合输出
    result = "\n".join(regular_lines).strip()
    if special_lines:
        result += "\n" + "\n".join(special_lines)
    
    return result


def fetch_lyrics(session: requests.Session, lyrics_url: str, attempt: int = 1) -> Optional[str]:
    """下载歌词数据，支持重试"""
    try:
        response = session.get(lyrics_url, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        response.encoding = 'utf-8'
        return response.text
        
    except requests.exceptions.Timeout:
        logging.warning(f"Timeout fetching lyrics (attempt {attempt}/{MAX_RETRIES}): {lyrics_url}")
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_BACKOFF * attempt)
            return fetch_lyrics(session, lyrics_url, attempt + 1)
        logging.error(f"Failed to fetch lyrics after {MAX_RETRIES} attempts: {lyrics_url}")
        return None
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching lyrics from {lyrics_url}: {e}")
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_BACKOFF * attempt)
            return fetch_lyrics(session, lyrics_url, attempt + 1)
        return None


def save_lyrics(artist: str, title: str, lyrics: str) -> bool:
    """保存歌词到文件"""
    filename = safe_filename(artist, title)
    
    # 检查文件是否已存在
    if os.path.exists(filename):
        logging.info(f"Lyrics already exist, skipping: {filename}")
        return True
    
    try:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(lyrics)
        logging.info(f"✓ Lyrics saved: {filename}")
        return True
        
    except IOError as e:
        logging.error(f"Error saving lyrics to {filename}: {e}")
        return False


def process_song(session: requests.Session, song: Dict[str, Any]) -> bool:
    """处理单首歌曲"""
    artist = re.sub(r' ?/ ?', ' ', song.get('author', song.get('artist', 'Unknown Artist')))
    title = re.sub(r' ?/ ?', ' ', song.get('title', song.get('name', 'Unknown Title')))
    lyrics_url = song.get('lrc')
    
    if not lyrics_url:
        logging.warning(f"✗ No lyrics URL found for: {title} by {artist}")
        return False
    
    lyrics = fetch_lyrics(session, lyrics_url)
    
    if not lyrics:
        logging.warning(f"✗ Failed to fetch lyrics for: {title} by {artist}")
        return False
    
    # 检查是否为纯音乐
    if "纯音乐，请欣赏" in lyrics or "纯音乐" in lyrics:
        logging.info(f"⊘ Instrumental track, skipping: {title} by {artist}")
        return False
    
    processed_lyrics = process_lyrics(lyrics)
    
    if not processed_lyrics.strip():
        logging.warning(f"✗ Empty lyrics after processing: {title} by {artist}")
        return False
    
    return save_lyrics(artist, title, processed_lyrics)


def fetch_playlist(session: requests.Session, api_endpoint: str) -> Optional[list]:
    """获取播放列表数据"""
    try:
        response = session.get(api_endpoint, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        playlist = response.json()
        
        if not isinstance(playlist, list):
            logging.error("API response is not a list")
            return None
            
        return playlist
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching playlist data: {e}")
        return None
    except ValueError as e:
        logging.error(f"Error parsing JSON response: {e}")
        return None


def main(api_endpoint: Optional[str] = None):
    """主程序"""
    # 使用参数或环境变量
    api_url = api_endpoint or API_URL
    
    if not api_url:
        logging.error("API URL not provided. Set LYRICS_API_URL environment variable or pass as argument.")
        return
    
    # 创建歌词目录
    os.makedirs(LYRICS_DIR, exist_ok=True)
    logging.info(f"Lyrics will be saved to: {os.path.abspath(LYRICS_DIR)}")
    
    # 创建会话
    session = create_session_with_retries()
    
    # 获取播放列表
    logging.info(f"Fetching playlist from: {api_url}")
    playlist = fetch_playlist(session, api_url)
    
    if not playlist:
        logging.error("Failed to fetch playlist or playlist is empty")
        return
    
    logging.info(f"Found {len(playlist)} songs in playlist")
    
    # 统计信息
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    # 处理每首歌曲
    for idx, song in enumerate(playlist, 1):
        logging.info(f"Processing song {idx}/{len(playlist)}")
        
        result = process_song(session, song)
        
        if result:
            success_count += 1
        elif result is False:
            failed_count += 1
        else:
            skipped_count += 1
        
        # 速率限制
        if idx < len(playlist):
            time.sleep(RATE_LIMIT_DELAY)
    
    # 输出统计
    logging.info("=" * 60)
    logging.info("Processing complete!")
    logging.info(f"Total songs: {len(playlist)}")
    logging.info(f"✓ Successfully downloaded: {success_count}")
    logging.info(f"✗ Failed: {failed_count}")
    logging.info(f"⊘ Skipped: {skipped_count}")
    logging.info("=" * 60)


if __name__ == "__main__":
    import sys
    
    # 支持命令行参数
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()