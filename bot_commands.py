"""
Telegram bot komut işleyici.
n8n tarafından çağrılır, sonucu stdout'a yazar.

Kullanım:
  python3 bot_commands.py /haber
  python3 bot_commands.py /pi
  python3 bot_commands.py /durum
  python3 bot_commands.py /youtube
"""
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

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
    cmd = sys.argv[1].strip().lower() if len(sys.argv) > 1 else "/yardim"
    # "@botismi" kısmını temizle (örn: /haber@bll9_bot)
    cmd = cmd.split("@")[0]
    handler = COMMANDS.get(cmd)
    if handler:
        handler()
    else:
        print(f"❓ Bilinmeyen komut: {cmd}\n/yardim yazarak komutları görebilirsin.")
