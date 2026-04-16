"""
Telegram bot komut işleyici.
n8n tarafından çağrılır, sonucu stdout'a yazar.

Kullanım:
  python3 bot_commands.py /haber <sender_chat_id>
  python3 bot_commands.py "bugün ne var" <sender_chat_id>

Güvenlik: TELEGRAM_ADMIN_IDS env var'ı tanımlıysa sadece oradaki
chat_id'ler komut çalıştırabilir. Tanımlı değilse (geliştirme modu)
tüm sender'lar kabul edilir.

Verimlilik: _detect_command önce keyword match dener, eşleşme yoksa
Gemini'ye düşer — her doğal dil mesajı API kotası yemez.
"""
import sys
import os
import json
import urllib.request

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()


# Komut → anahtar kelime eşlemesi. Alt string match (küçük harfli metinde).
# Sıralamanın önemi var: daha spesifik komutlar önce gelmeli.
_KEYWORD_MAP: list[tuple[list[str], str]] = [
    (["haber", "gündem", "llm", "yapay zeka", "ai haber"], "/haber"),
    # Türkçe ek almaları için kökler: "sıcakl" → sıcaklık/sıcaklığı/…
    (["sıcakl", "ram", "disk", "uptime", "pi durum", "raspberry"], "/pi"),
    (["servis", "çalışıyor", "ayakta", "durum"], "/durum"),
    (["youtube", "video", "kanal"], "/youtube"),
    (["yardım", "komut", "ne yapabilir", "nasıl", "start"], "/yardim"),
]


def _keyword_match(text: str) -> str | None:
    """Keyword tabanlı komut router. Eşleşme yoksa None."""
    t = text.lower()
    for keywords, cmd in _KEYWORD_MAP:
        if any(k in t for k in keywords):
            return cmd
    return None


def _gemini_detect_command(text: str) -> str:
    """Keyword match başarısız olduğunda Gemini'ye sor."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return "/yardim"

    prompt = (
        "Kullanıcının mesajına göre aşağıdaki komutlardan birini seç:\n"
        "/haber - haber, gündem, LLM, yapay zeka haberleri\n"
        "/pi - raspberry pi durumu, sıcaklık, ram, disk, sistem\n"
        "/durum - servis çalışıyor mu, sistem durumu\n"
        "/youtube - youtube, video, kanal, yeni video\n"
        "/yardim - yardım, komutlar, ne yapabilirsin\n\n"
        f"Kullanıcı mesajı: {text}\n\n"
        "Sadece komutu yaz, başka hiçbir şey yazma. Örnek: /haber"
    )
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 10},
    }).encode()
    try:
        req = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        result = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return result if result.startswith("/") else "/yardim"
    except Exception:
        return "/yardim"


def _detect_command(text: str) -> str:
    """Önce keyword match, sonra Gemini fallback."""
    matched = _keyword_match(text)
    if matched:
        return matched
    return _gemini_detect_command(text)


def _is_authorized(sender: str) -> bool:
    """TELEGRAM_ADMIN_IDS set'inde sender varsa True. Env yoksa True (dev modu)."""
    allowed_raw = os.environ.get("TELEGRAM_ADMIN_IDS", "").strip()
    if not allowed_raw:
        return True  # dev modu: allowlist tanımlı değil
    allowed = {x.strip() for x in allowed_raw.split(",") if x.strip()}
    return sender in allowed

def cmd_pi():
    from llm_news.routine import get_pi_status
    print(get_pi_status())

def cmd_durum():
    import subprocess
    result = subprocess.run(
        ["systemctl", "status", "llm_news", "--no-pager", "-l"],
        capture_output=True, text=True
    )
    lines = result.stdout.strip().split("\n")[:8]
    status = "\n".join(lines)
    # Aktif mi değil mi?
    if "active (running)" in result.stdout:
        icon = "✅"
    elif "failed" in result.stdout:
        icon = "❌"
    else:
        icon = "⚠️"
    print(f"{icon} <b>Servis Durumu</b>\n\n<code>{status}</code>")

def cmd_haber():
    from llm_news.routine import run_news_routine
    print("⏳ Haberler hazırlanıyor, birazdan gelecek...")
    run_news_routine()

def cmd_youtube():
    from youtube_tracker.tracker import run_youtube_tracker
    print("⏳ YouTube kontrol ediliyor...")
    run_youtube_tracker()

def cmd_yardim():
    print(
        "🤖 <b>Komutlar:</b>\n\n"
        "/haber — LLM haberlerini şimdi gönder\n"
        "/pi — Raspberry Pi durumu\n"
        "/durum — Servis çalışıyor mu?\n"
        "/youtube — YouTube kanallarını kontrol et\n"
        "/yardim — Bu mesaj"
    )

COMMANDS = {
    "/haber": cmd_haber,
    "/pi": cmd_pi,
    "/durum": cmd_durum,
    "/youtube": cmd_youtube,
    "/yardim": cmd_yardim,
    "/start": cmd_yardim,
}

if __name__ == "__main__":
    text = sys.argv[1].strip() if len(sys.argv) > 1 else "/yardim"
    sender = sys.argv[2].strip() if len(sys.argv) > 2 else ""

    if not _is_authorized(sender):
        print("🚫 Yetkisiz erişim. Bu bot yalnızca yetkili kullanıcılara açıktır.")
        sys.exit(1)

    # Slash komutu mu yoksa doğal dil mi?
    if text.startswith("/"):
        cmd = text.lower().split("@")[0]
    else:
        cmd = _detect_command(text)

    handler = COMMANDS.get(cmd)
    if handler:
        handler()
    else:
        print(f"❓ Bilinmeyen komut: {cmd}\n/yardim yazarak komutları görebilirsin.")
