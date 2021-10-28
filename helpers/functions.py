import requests
from pyrogram import filters
import pafy

group_only = filters.group & ~filters.private & ~filters.edited & ~filters.forwarded & ~filters.via_bot


def format_count(number: int):
    num = float(f"{number:.3g}")
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return f"{str(num).rstrip('0').rstrip('.')}{['', 'K', 'M', 'B', 'T'][magnitude]}"


def get_audio_link(url: str) -> str:
    pufy = pafy.new(url)
    audios = pufy.getbestaudio()
    return audios.url


def get_yt_details(link: str):
    pufy = pafy.new(link)
    return {
        "thumbnails": pufy.bigthumbhd,
        "title": pufy.title,
        "duration": pufy.duration,
        "views": format_count(pufy.viewcount),
        "likes": format_count(pufy.likes),
        "dislikes": format_count(pufy.dislikes),
        "rating": round(pufy.rating, 2),
        "channel": pufy.author,
        "link": f"https://youtube.com/watch?v={link}"
    }


def download_yt_thumbnails(thumb_url, user_id):
    r = requests.get(thumb_url)
    with open(f"search/thumb{user_id}.jpg", "wb") as file:
        for chunk in r.iter_content(1024):
            file.write(chunk)
    return f"search/thumb{user_id}.jpg"
