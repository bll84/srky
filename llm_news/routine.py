import json
import logging
import os
import time
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
HEADERS = {"User-Agent": "Mozilla/5.0 (LLM-News-Bot/1.0)"}

# Geçici hata sayılan ve yeniden denenen hata kodları
_RETRIABLE_STATUS = {429, 500, 502, 503, 504}

# Config dosyasını yükle
_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
with open(_CONFIG_PATH) as _f:
    _CFG = json.load(_f)

RSS_FEEDS = _CFG["news"]["feeds"]
KEYWORDS = _CFG["news"]["keywords"]
MAX_STORIES = _CFG["news"]["max_stories"]


# ── HTTP retry + admin alert ─────────────────────────────────────────────────

def _http_post_json(url: str, payload: bytes, timeout: int, retries: int = 3) -> dict:
    """POST JSON; geçici hatada exponential backoff ile yeniden dener.

    Retry koşulları: URLError (timeout/DNS/reset), 429/5xx HTTPError.
    Kalıcı hatalarda (4xx vb.) ilk denemede istisna fırlatır.
    """
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code not in _RETRIABLE_STATUS:
                raise
            logger.warning("HTTP %s, deneme %d/%d: %s", e.code, attempt, retries, url)
        except urllib.error.URLError as e:
            last_err = e
            logger.warning("Bağlantı hatası, deneme %d/%d: %s", attempt, retries, e)
        if attempt < retries:
            time.sleep(2 ** attempt)  # 2s, 4s, 8s
    assert last_err is not None
    raise last_err


def _send_admin_alert(message: str) -> None:
    """Kritik hata olduğunda admin chat'ine Telegram uyarısı yolla.

    Uyarının kendisi başarısız olursa sessizce log'a düşer — aksi halde
    alert loop'una girilir.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_ADMIN_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return
    try:
        payload = json.dumps({
            "chat_id": chat_id,
            "text": f"🚨 <b>Pi Rutinleri Uyarı</b>\n\n{message}",
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=10).read()
    except Exception as e:
        logger.error("Admin alert gönderilemedi: %s", e)


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
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

    try:
        data = _http_post_json(url, payload, timeout=45)
        raw = data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(raw)
    except Exception as e:
        logger.error("Gemini işleme kalıcı hatası: %s", e)
        _send_admin_alert(
            f"Haber özeti Gemini çağrısı başarısız.\n"
            f"Hata: <code>{type(e).__name__}: {e}</code>\n"
            f"Digest çevirisiz/içgörüsüz gönderilecek."
        )
        return {"stories": [], "fayda": "", "proje": ""}


# ── Pi Durumu ────────────────────────────────────────────────────────────────

def get_pi_status() -> str:
    import shutil
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
    # İç IP — abone sistemine geçince müşterilere görünmemeli.
    # SHOW_INTERNAL_IP=1 ile açıkça aç.
    if os.environ.get("SHOW_INTERNAL_IP") == "1":
        try:
            import socket
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
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    result = _http_post_json(url, payload, timeout=15)
    if not result.get("ok"):
        raise RuntimeError(f"Telegram API hatasi: {result}")


_TELEGRAM_LIMIT = 4096


def _split_oversized(block: str, limit: int) -> list[str]:
    """Tek parça limit üstüyse satır → boşluk → hard-cut sırasıyla böl.

    Bu kod tabanındaki HTML etiketleri hep satır içinde kapandığı için
    \\n üzerinden kesmek etiket çiftlerini bozmaz.
    """
    parts: list[str] = []
    remaining = block
    while len(remaining) > limit:
        cut = remaining.rfind("\n", 0, limit)
        if cut < limit // 2:  # satır yoksa kelimeye in
            cut = remaining.rfind(" ", 0, limit)
        if cut < limit // 2:  # çok yapışık → hard cut
            cut = limit
        parts.append(remaining[:cut])
        remaining = remaining[cut:].lstrip()
    if remaining:
        parts.append(remaining)
    return parts


def _chunk_html_safe(text: str, limit: int = _TELEGRAM_LIMIT) -> list[str]:
    """Telegram limit'ine göre HTML-güvenli chunk'lar üret.

    Önce \\n\\n paragraf sınırlarında birleştirir; tek paragraf limit'i
    aşıyorsa _split_oversized ile satır/boşluk sınırında böler. Hiçbir
    chunk > limit olmaz.
    """
    chunks: list[str] = []
    current = ""
    for block in text.split("\n\n"):
        if len(block) > limit:
            if current:
                chunks.append(current)
                current = ""
            parts = _split_oversized(block, limit)
            chunks.extend(parts[:-1])
            current = parts[-1]
            continue
        candidate = f"{current}\n\n{block}" if current else block
        if len(candidate) > limit:
            chunks.append(current)
            current = block
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def send_telegram(text: str) -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    for chunk in _chunk_html_safe(text):
        _telegram_send(token, chat_id, chunk)


# ── Abone migration ──────────────────────────────────────────────────────────

def _bootstrap_admin_subscriber() -> None:
    """İlk çalıştırmada TELEGRAM_CHAT_ID'yi admin abone olarak ekle.

    Bu yumuşak migration: hiç abone yokken env'deki chat_id otomatik kaydolur,
    böylece servis upgrade edildiğinde mevcut kullanıcı `/abone` yazmadan
    digest almaya devam eder.
    """
    from subscribers.db import init_db, count_active, add_subscriber
    init_db()
    admin_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if admin_id and count_active() == 0:
        add_subscriber(admin_id, slot="both")
        logger.info("Admin %s bootstrap abone olarak eklendi", admin_id)


# ── Ana Rutin ─────────────────────────────────────────────────────────────────

def run_news_routine() -> None:
    from subscribers.broadcast import broadcast_html
    from subscribers.db import count_active

    now = datetime.now(ISTANBUL_TZ)
    # DB için slot (morning/evening) — digest filter
    db_slot = "morning" if now.hour < 12 else "evening"
    # Başlık için TR
    slot_tr = "Sabah" if db_slot == "morning" else "Aksam"
    header = f"LLM Haber Ozeti — {now.strftime('%d %B %Y')} ({slot_tr})"
    logger.info("Baslıyor: %s", header)
    try:
        _bootstrap_admin_subscriber()
        if count_active() == 0:
            logger.warning("Hiç abone yok, digest üretilmeyecek")
            return
        stories = fetch_llm_news()
        logger.info("%d haber bulundu", len(stories))
        text = format_for_telegram(stories, header)
        stats = broadcast_html(text, slot=db_slot)
        logger.info(
            "Digest gonderildi: sent=%d blocked=%d failed=%d / toplam=%d",
            stats["sent"], stats["blocked"], stats["failed"], stats["total"],
        )
        # Başarı oranı %50'nin altındaysa admin'e uyar
        if stats["total"] > 0 and stats["sent"] / stats["total"] < 0.5:
            _send_admin_alert(
                f"Digest başarı oranı düşük: {stats['sent']}/{stats['total']} "
                f"gönderildi (blocked={stats['blocked']}, failed={stats['failed']})."
            )
    except urllib.error.URLError as e:
        logger.error("Baglanti hatasi: %s", e)
        _send_admin_alert(f"Haber rutini bağlantı hatasıyla başarısız oldu: <code>{e}</code>")
    except RuntimeError as e:
        logger.error("Hata: %s", e)
        _send_admin_alert(f"Haber rutini hatası: <code>{e}</code>")
    except Exception as e:
        logger.exception("Beklenmeyen hata: %s", e)
        _send_admin_alert(f"Haber rutini beklenmeyen hata: <code>{type(e).__name__}: {e}</code>")
