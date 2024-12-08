import requests
import re
import os
import hashlib










# 设置请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 14; HBP-AL00 Build/AP2A.240905.003) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.5 Mobile Safari/537.36",
    "Origin": "https://www.cnblogs.com",
    "X-Requested-With": "mark.via.gp",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://www.cnblogs.com/"
}

# 确保歌词目录存在
os.makedirs("lyrics", exist_ok=True)

# 下载并保存歌词
def download_lyrics(api_url):
    try:
        playlist_data = requests.get(api_url, headers=HEADERS).json()
    except Exception as e:
        print(f"无法获取播放列表: {e}")
        return

    for song in playlist_data:
        artist = re.sub(r' ?/ ?', ' ', song.get('author', song.get('artist', '')))
        title = re.sub(r' ?/ ?', ' ', song.get('title', song.get('name', '')))
        lyrics_url = song.get('lrc')

        try:
            lyrics = requests.get(lyrics_url, headers=HEADERS).text
        except Exception as e:
            print(f"无法获取歌词: {e}")
            continue

        if not lyrics or "纯音乐，请欣赏" in lyrics:
            continue

        # 格式化歌词
        lyrics = re.sub(r'(\d{2}:\d{2})\.(\d{3})', r'\1', lyrics)  # 去掉毫秒
        regular_lyrics = []
        metadata_lines = []

        for line in lyrics.splitlines():
            # 匹配作词作曲等信息的行，要求包含中文或英文冒号
            if re.match(r'^\[\d{2}:\d{2}\].*?[:：].*$', line):
                metadata_lines.append(re.sub(r'^\[\d{2}:\d{2}\]', '[999:99]', line))
            else:
                regular_lyrics.append(line)

        # 拼接歌词，元数据行移动到最后
        lyrics = '\n'.join(regular_lyrics).strip() + '\n' + '\n'.join(metadata_lines).strip()

        # 生成安全文件名
        filename = f"{artist} - {title}.lrc"
        if len(filename) > 105 - len("lyrics/"):
            filename = f"{hashlib.md5(filename.encode('utf-8')).hexdigest()}.lrc"
        filepath = f"lyrics/{filename}"

        try:
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(lyrics)
            print(f"已保存歌词: {filepath}")
        except Exception as e:
            print(f"保存失败: {e}")

download_lyrics(api_url)
