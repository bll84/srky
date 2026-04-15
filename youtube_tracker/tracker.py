import json
import logging
import os
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import pytz
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
ISTANBUL_TZ = pytz.timezone("Europe/Istanbul")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; YT-Tracker/1.0)"}
STATE_FILE = os.path.join(os.path.dirname(__file__), "seen_videos.json")

# Takip edilecek kanallar: @handle veya UC... channel ID
CHANNELS = [
    "@omergcmen",
]


def _resolve_channel_id(handle: str) -> str:
    """Resolve @handle to UC... channel ID by fetching the channel page."""
    if handle.startswith("UC"):
        return handle
    url = f"https://www.youtube.com/{handle}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
    match = re.search(r'"channelId":"(UC[^"]+)"', html)
    if not match:
        raise ValueError(f"Channel ID bulunamadi: {handle}")
    return match.group(1)


def _load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def _save_state(state: dict) -> None:
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def _fetch_channel_videos(channel_id: str) -> list[dict]:
    """Fetch latest videos from a YouTube channel via RSS."""
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as resp:
        raw = resp.read()

    root = ET.fromstring(raw)
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "yt": "http://www.youtube.com/xml/schemas/2015",
        "media": "http://search.yahoo.com/mrss/",
    }

    channel_name = root.findtext("atom:author/atom:name", "", ns)
    videos = []
    for entry in root.findall("atom:entry", ns):
        video_id = entry.findtext("yt:videoId", "", ns)
        title = entry.findtext("atom:title", "", ns)
        link = entry.findtext("atom:link[@rel='alternate']", "", ns)
        if not link:
            link_el = entry.find("atom:link", ns)
            link = link_el.get("href", "") if link_el is not None else ""
        published = entry.findtext("atom:published", "", ns)
        try:
            date = datetime.fromisoformat(published.replace("Z", "+00:00"))
        except Exception:
            date = datetime.now(timezone.utc)
        if video_id:
            videos.append({
                "id": video_id,
                "title": title,
                "link": f"https://www.youtube.com/watch?v={video_id}",
                "channel": channel_name,
                "date": date,
            })
    return videos


def _telegram_send(text: str) -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read())
    if not result.get("ok"):
        raise RuntimeError(f"Telegram hatasi: {result}")


def run_youtube_tracker() -> None:
    """Check all channels for new videos and send Telegram notifications."""
    state = _load_state()
    new_videos_found = False

    for handle in CHANNELS:
        try:
            channel_id = _resolve_channel_id(handle)
            videos = _fetch_channel_videos(channel_id)
            seen = set(state.get(channel_id, []))
            new_videos = [v for v in videos if v["id"] not in seen]

            for video in reversed(new_videos):  # Eskiden yeniye gönder
                date_str = video["date"].astimezone(ISTANBUL_TZ).strftime("%d %b %H:%M")
                msg = (
                    f"🎬 <b>Yeni Video!</b>\n\n"
                    f"<b>{video['channel']}</b>\n"
                    f"{video['title']}\n\n"
                    f"<i>{date_str}</i>\n"
                    f'<a href="{video["link"]}">İzle →</a>'
                )
                _telegram_send(msg)
                logger.info("Yeni video bildirimi: %s", video["title"])
                new_videos_found = True

            # Durumu güncelle (son 50 video ID sakla)
            all_ids = list(seen | {v["id"] for v in videos})
            state[channel_id] = all_ids[-50:]

        except Exception as e:
            logger.error("Kanal hatasi %s: %s", handle, e)

    _save_state(state)
    if not new_videos_found:
        logger.info("Yeni video yok")
