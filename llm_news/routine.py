import json
import logging
import os
import urllib.error
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


# ── RSS ──────────────────────────────────────────────────────────────────────

def _fetch_rss(url: str) -> list[dict]:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
        root = ET.fromstring(raw)
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
            items.append({"title": title, "link": link, "source": feed_title, "date": date})
        return items
    except Exception as e:
        logger.warning("RSS alinamadi %s: %s", url, e)
        return []


def fetch_llm_news() -> list[dict]:
    seen_links: set[str] = set()
    stories: list[dict] = []
    for feed_url in RSS_FEEDS:
        for item in _fetch_rss(feed_url):
            if item["link"] in seen_links:
                continue
            if not any(kw in item["title"].lower() for kw in KEYWORDS):
                continue
            seen_links.add(item["link"])
            stories.append(item)
    stories.sort(key=lambda x: x["date"], reverse=True)
    return stories[:MAX_STORIES]


# ── Gemini (tek çağrı) ───────────────────────────────────────────────────────

def _gemini_process_all(stories: list[dict]) -> dict:
    """
    Tek Gemini çağrısıyla:
    - Başlıkları Türkçe'ye çevirir
    - Her haber için içgörü üretir
    - Kişisel fayda + proje fikirleri üretir
    JSON döndürür.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return {"stories": [], "personal": ""}

    story_list = "\n".join(f"{i+1}. {s['title']}" for i, s in enumerate(stories))

    prompt = f"""Aşağıdaki yapay zeka/LLM haber başlıkları için JSON formatında yanıt ver.

Haberler:
{story_list}

Şu JSON yapısını döndür:
{{
  "stories": [
    {{
      "baslik": "Türkçe başlık",
      "icgoru": "💡 Ne anlama geliyor (1 cümle)\\n✅ • Yapabileceklerin (2-3 madde)"
    }}
  ],
  "fayda": "FAYDA:\\n• madde 1\\n• madde 2\\n• madde 3",
  "proje": "PROJE:\\n• Proje fikri — tahmini maliyet\\n• Proje fikri — tahmini maliyet\\n• Proje fikri — tahmini maliyet"
}}

Kurallar:
- stories dizisi haberlerin sırasıyla eşleşmeli
- Tüm metinler Türkçe olmalı
- Sadece JSON döndür, başka hiçbir şey yazma"""

    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 4096,
            "responseMimeType": "application/json",
        },
    }).encode()

    try:
        req = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read())
        raw = data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(raw)
    except Exception as e:
        logger.warning("Gemini isleme hatasi: %s", e)
        return {"stories": [], "personal": ""}


# ── Pi Durumu ────────────────────────────────────────────────────────────────

def get_pi_status() -> str:
    import shutil, socket
    lines = ["🖥️ <b>Pi Durumu</b>"]
    try:
        temp = int(open("/sys/class/thermal/thermal_zone0/temp").read().strip()) / 1000
        icon = "🔴" if temp > 70 else "🟡" if temp > 55 else "🟢"
        lines.append(f"{icon} Sıcaklık: {temp:.0f}°C")
    except Exception:
        pass
    try:
        meminfo = {k.strip(): int(v.strip().split()[0])
                   for line in open("/proc/meminfo")
                   for k, v in [line.split(":", 1)]}
        total, avail = meminfo["MemTotal"], meminfo["MemAvailable"]
        lines.append(f"💾 RAM: %{int((total-avail)/total*100)} ({(total-avail)//1024}MB / {total//1024}MB)")
    except Exception:
        pass
    try:
        u = shutil.disk_usage("/")
        lines.append(f"💿 Disk: %{int(u.used/u.total*100)} ({u.used/1e9:.1f}GB / {u.total/1e9:.1f}GB)")
    except Exception:
        pass
    try:
        sec = float(open("/proc/uptime").read().split()[0])
        d, h, m = int(sec//86400), int(sec%86400//3600), int(sec%3600//60)
        lines.append(f"⏱️ Çalışma: {f'{d}g {h}sa' if d else f'{h}sa {m}dk' if h else f'{m}dk'}")
    except Exception:
        pass
    try:
        lines.append(f"🌐 IP: {socket.gethostbyname(socket.gethostname())}")
    except Exception:
        pass
    return "\n".join(lines)


# ── Telegram ─────────────────────────────────────────────────────────────────

def format_for_telegram(stories: list[dict], header: str) -> str:
    if not stories:
        return f"<b>{header}</b>\n\nBugün LLM haberi bulunamadı."

    def esc(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Tek Gemini çağrısı — çeviri + içgörü + özet
    gemini = _gemini_process_all(stories)
    gemini_stories = gemini.get("stories", [])

    lines = [f"<b>{header}</b>"]
    for i, s in enumerate(stories, 1):
        g = gemini_stories[i-1] if i-1 < len(gemini_stories) else {}
        title = g.get("baslik") or s["title"]
        insight = g.get("icgoru", "")
        date_str = s["date"].astimezone(ISTANBUL_TZ).strftime("%d %b %H:%M")
        block = f"\n<b>{i}. {esc(title)}</b>\n<i>{esc(s['source'])} — {date_str}</i>"
        if insight:
            block += f"\n{esc(insight)}"
        block += f'\n<a href="{s["link"]}">Devamını oku →</a>'
        lines.append(block)

    fayda = gemini.get("fayda", "")
    proje = gemini.get("proje", "")
    if fayda or proje:
        lines.append(
            f"\n\n<b>━━━━━━━━━━━━━━━</b>\n"
            f"<b>💰 BUGÜN SANA NE KAZANDIRIR?</b>\n\n"
            f"{esc(fayda)}\n\n{esc(proje)}"
        )

    pi = get_pi_status()
    if pi:
        lines.append(f"\n\n<b>━━━━━━━━━━━━━━━</b>\n{pi}")

    return "\n".join(lines)


def _telegram_send(token: str, chat_id: str, text: str) -> None:
    payload = json.dumps({
        "chat_id": chat_id, "text": text,
        "parse_mode": "HTML", "disable_web_page_preview": True,
    }).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload, headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read())
    if not result.get("ok"):
        raise RuntimeError(f"Telegram API hatasi: {result}")


def send_telegram(text: str) -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    if len(text) <= 4096:
        _telegram_send(token, chat_id, text)
        return
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


# ── Ana Rutin ─────────────────────────────────────────────────────────────────

def run_news_routine() -> None:
    now = datetime.now(ISTANBUL_TZ)
    slot = "Sabah" if now.hour < 12 else "Aksam"
    header = f"LLM Haber Ozeti — {now.strftime('%d %B %Y')} ({slot})"
    logger.info("Baslıyor: %s", header)
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
