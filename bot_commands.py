"""
Telegram bot komut işleyici.
n8n tarafından çağrılır, sonucu stdout'a yazar.

Kullanım:
  python3 bot_commands.py /haber
  python3 bot_commands.py "bugün ne var"
"""
import sys
import os
import json
import urllib.request

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()


def _detect_command(text: str) -> str:
    """Use Gemini to detect which command the user wants."""
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
