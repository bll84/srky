import json
import logging
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import pytz
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
ISTANBUL_TZ = pytz.timezone("Europe/Istanbul")

RSS_FEEDS = [
    "https://news.google.com/rss/search?q=Claude+GPT+Gemini+Anthropic+OpenAI+LLM&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=yapay+zeka+LLM+Claude+GPT+Gemini&hl=tr&gl=TR&ceid=TR:tr",
    "https://venturebeat.com/category/ai/feed/",
    "https://techcrunch.com/category/artificial-intelligence/feed/",
]

KEYWORDS = [
    "llm", "large language model", "claude", "chatgpt", "gpt-4", "gpt-5", "gpt-6",
    "gemini", "anthropic", "openai", "deepmind", "mistral", "llama", "meta ai",
    "generative ai", "yapay zeka", "language model", "foundation model", "ai model",
]

MAX_STORIES = 10
HEADERS = {"User-Agent": "Mozilla/5.0 (LLM-News-Bot/1.0)"}


def _fetch_rss(url: str) -> list[dict]:
    """Fetch and parse a single RSS feed. Returns list of items."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
        root = ET.fromstring(raw)
        ns = {"media": "http://search.yahoo.com/mrss/"}
        channel = root.find("channel")
        if channel is None:
            return []
        feed_title = channel.findtext("title", "")
        items = []
        for item in channel.findall("item"):
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            pub_date = item.findtext("pubDate", "")
            try:
                date = parsedate_to_datetime(pub_date).astimezone(timezone.utc)
            except Exception:
                date = datetime.now(timezone.utc)
            items.append({
                "title": title,
                "link": link,
                "source": feed_title,
                "date": date,
            })
        return items
    except Exception as e:
        logger.warning("RSS alinamadi %s: %s", url, e)
        return []


def _is_relevant(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in KEYWORDS)


def fetch_llm_news() -> list[dict]:
    """Fetch LLM news from RSS feeds. Returns up to MAX_STORIES sorted by date."""
    seen_links: set[str] = set()
    stories: list[dict] = []

    for feed_url in RSS_FEEDS:
        for item in _fetch_rss(feed_url):
            if item["link"] in seen_links:
                continue
            if not _is_relevant(item["title"]):
                continue
            seen_links.add(item["link"])
            stories.append(item)

    stories.sort(key=lambda x: x["date"], reverse=True)
    return stories[:MAX_STORIES]


def _translate_to_turkish(text: str) -> str:
    """Translate text to Turkish using MyMemory free API."""
    try:
        params = urllib.parse.urlencode({"q": text, "langpair": "en|tr"})
        url = f"https://api.mymemory.translated.net/get?{params}"
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
        translated = data.get("responseData", {}).get("translatedText", "")
        if translated and translated.upper() != text.upper():
            return translated
    except Exception as e:
        logger.debug("Ceviri basarisiz: %s", e)
    return text


def format_for_telegram(stories: list[dict], header: str) -> str:
    """Format stories as Telegram-compatible HTML, translating titles to Turkish."""
    if not stories:
        return f"<b>{header}</b>\n\nBugün LLM haberi bulunamadı."

    def esc(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    lines = [f"<b>{header}</b>"]
    for i, s in enumerate(stories, 1):
        title = s["title"]
        # Başlık Türkçe karakter içermiyorsa çevir
        if not any(tr_char in title for tr_char in "çğışöüÇĞİŞÖÜ"):
            title = _translate_to_turkish(title)
            time.sleep(0.3)  # API rate limit için kısa bekleme
        date_str = s["date"].astimezone(ISTANBUL_TZ).strftime("%d %b %H:%M")
        lines.append(
            f"\n<b>{i}. {esc(title)}</b>\n"
            f"<i>{esc(s['source'])} — {date_str}</i>\n"
            f'<a href="{s["link"]}">Devamını oku →</a>'
        )

    return "\n".join(lines)


def _telegram_send(token: str, chat_id: str, text: str) -> None:
    """Send a single Telegram message (max 4096 chars)."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }).encode()
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read())
    if not result.get("ok"):
        raise RuntimeError(f"Telegram API hatasi: {result}")


def send_telegram(text: str) -> None:
    """Send to Telegram, chunking if > 4096 chars."""
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    if len(text) <= 4096:
        _telegram_send(token, chat_id, text)
        return

    # Bölümlere ayır — her haber bloğu "\n\n" ile ayrılıyor
    chunks, current = [], ""
    for block in text.split("\n\n"):
        candidate = current + "\n\n" + block if current else block
        if len(candidate) > 4096:
            if current:
                chunks.append(current)
            current = block
        else:
            current = candidate
    if current:
        chunks.append(current)

    for chunk in chunks:
        _telegram_send(token, chat_id, chunk)


def run_news_routine() -> None:
    """Orchestrate fetch + format + send. Never crashes the scheduler."""
    now = datetime.now(ISTANBUL_TZ)
    slot = "Sabah" if now.hour < 12 else "Aksam"
    header = f"LLM Haber Ozeti — {now.strftime('%d %B %Y')} ({slot})"

    logger.info("LLM haber rutini basliyor: %s", header)
    try:
        stories = fetch_llm_news()
        logger.info("%d haber bulundu", len(stories))
        text = format_for_telegram(stories, header)
        send_telegram(text)
        logger.info("Telegram'a gonderildi")
    except urllib.error.URLError as e:
        logger.error("Baglanti hatasi: %s", e)
    except RuntimeError as e:
        logger.error("Hata: %s", e)
    except Exception as e:
        logger.exception("Beklenmeyen hata: %s", e)
