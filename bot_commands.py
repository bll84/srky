"""
Telegram bot komut işleyici.
n8n tarafından çağrılır, sonucu stdout'a yazar.

Kullanım:
  python3 bot_commands.py /haber <sender_chat_id>
  python3 bot_commands.py "bugün ne var" <sender_chat_id>

Komut tipleri:
  - Public (herkes): /abone, /iptal, /tercihler, /yardim, /start
  - Admin-only: /haber, /pi, /durum, /youtube
    (TELEGRAM_ADMIN_IDS env'indeki chat_id'ler. Tanımlı değilse dev modu:
    tüm sender'lar admin sayılır.)

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

from subscribers.db import (
    init_db, add_subscriber, remove_subscriber, set_slot,
    get_subscriber, count_active, VALID_SLOTS,
)


# Komut → anahtar kelime eşlemesi. Alt string match (küçük harfli metinde).
# Sıralamanın önemi var: daha spesifik komutlar önce gelmeli.
_KEYWORD_MAP: list[tuple[list[str], str]] = [
    (["abone ol", "katıl", "üye ol", "kaydol"], "/abone"),
    (["iptal", "ayrıl", "çık", "abonelikten"], "/iptal"),
    (["tercih", "ayar", "sabah", "akşam"], "/tercihler"),
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
        "/abone - aboneliğe katılmak, üye olmak\n"
        "/iptal - abonelikten çıkmak\n"
        "/tercihler - sabah/akşam tercih değiştirmek\n"
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


def _is_admin(sender: str) -> bool:
    """TELEGRAM_ADMIN_IDS set'inde sender varsa True. Env yoksa True (dev modu)."""
    allowed_raw = os.environ.get("TELEGRAM_ADMIN_IDS", "").strip()
    if not allowed_raw:
        return True  # dev modu: allowlist tanımlı değil
    allowed = {x.strip() for x in allowed_raw.split(",") if x.strip()}
    return sender in allowed


# ── Public komutlar ──────────────────────────────────────────────────────────

def cmd_abone(sender: str):
    if not sender:
        print("⚠️ Chat ID alınamadı, tekrar deneyin.")
        return
    created = add_subscriber(sender)
    total = count_active()
    if created:
        print(
            "✅ <b>Hoş geldin!</b>\n\n"
            "Artık LLM haber özeti sabah ve akşam sana düşecek.\n\n"
            "Komutlar:\n"
            "• /tercihler — sadece sabah veya sadece akşam al\n"
            "• /iptal — aboneliği sonlandır\n"
            "• /yardim — tüm komutlar\n\n"
            f"<i>Toplam abone: {total}</i>"
        )
    else:
        print(f"ℹ️ Zaten abonesin. Toplam abone: {total}.\n/yardim — komutlar")


def cmd_iptal(sender: str):
    if not sender:
        print("⚠️ Chat ID alınamadı.")
        return
    removed = remove_subscriber(sender)
    if removed:
        print(
            "👋 Aboneliğin iptal edildi.\n"
            "Tekrar katılmak için <code>/abone</code> yaz."
        )
    else:
        print("ℹ️ Zaten abone değilsin.")


def cmd_tercihler(sender: str, arg: str = ""):
    """/tercihler → mevcut tercihi göster; /tercihler sabah|aksam|ikisi → değiştir."""
    if not sender:
        print("⚠️ Chat ID alınamadı.")
        return
    sub = get_subscriber(sender)
    if not sub or not sub["active"]:
        print("❌ Önce <code>/abone</code> ol.")
        return

    # Exact + substring match: "/tercihler sabah" veya doğal dilden
    # "tercihi sabaha çevir" gibi ifadeleri de yakalar.
    mapping = {
        "sabah": "morning", "morning": "morning",
        "akşam": "evening", "aksam": "evening", "evening": "evening",
        "ikisi": "both", "both": "both", "tümü": "both", "hepsi": "both",
    }
    arg_lower = arg.strip().lower()
    slot: str | None = None
    if arg_lower:
        slot = mapping.get(arg_lower)
        if slot is None:
            # Substring tarama — "tercihleri sabaha çevir" gibi doğal dilde
            for key, val in mapping.items():
                if key in arg_lower:
                    slot = val
                    break
    if slot is not None:
        set_slot(sender, slot)
        pretty = {"morning": "sadece sabah", "evening": "sadece akşam", "both": "sabah ve akşam"}
        print(f"✅ Tercih güncellendi: <b>{pretty[slot]}</b>")
        return
    if arg_lower and arg_lower != "/tercihler" and not arg_lower.startswith("tercih"):
        # Argüman var ama anlamlı değil — sadece açıkça geçersiz ifadelerde uyar
        print(
            "⚠️ Geçersiz tercih. Kullanım:\n"
            "<code>/tercihler sabah</code>\n"
            "<code>/tercihler akşam</code>\n"
            "<code>/tercihler ikisi</code>"
        )
        return

    # Mevcut tercihi göster
    pretty = {"morning": "sadece sabah", "evening": "sadece akşam", "both": "sabah ve akşam"}
    print(
        f"⚙️ Mevcut tercih: <b>{pretty[sub['slot']]}</b>\n\n"
        "Değiştirmek için:\n"
        "<code>/tercihler sabah</code>\n"
        "<code>/tercihler akşam</code>\n"
        "<code>/tercihler ikisi</code>"
    )


def cmd_yardim(sender: str, is_admin: bool):
    """Yardım — public ve (varsa) admin komutları listeler."""
    lines = [
        "🤖 <b>Komutlar:</b>",
        "",
        "<b>Abonelik:</b>",
        "/abone — LLM haber özetine abone ol",
        "/iptal — aboneliği sonlandır",
        "/tercihler — sabah/akşam/ikisi seç",
    ]
    if is_admin:
        lines += [
            "",
            "<b>Admin:</b>",
            "/haber — LLM haberlerini şimdi tetikle",
            "/pi — Raspberry Pi durumu",
            "/durum — Servis durumu",
            "/youtube — YouTube kanallarını kontrol et",
        ]
    lines.append("\n/yardim — bu mesaj")
    print("\n".join(lines))


# ── Admin-only komutlar ──────────────────────────────────────────────────────

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


# Komutları kategorilere ayır: public (herkes) vs admin-only.
PUBLIC_COMMANDS = {"/abone", "/iptal", "/tercihler", "/yardim", "/start"}
ADMIN_COMMANDS = {"/haber", "/pi", "/durum", "/youtube"}


if __name__ == "__main__":
    # Argümanlar: text + sender + (opsiyonel) ek argümanlar (/tercihler için)
    text = sys.argv[1].strip() if len(sys.argv) > 1 else "/yardim"
    sender = sys.argv[2].strip() if len(sys.argv) > 2 else ""

    # DB'yi garanti et (ilk çalıştırmada tablo yoksa oluştur)
    init_db()

    # Slash komutu mu yoksa doğal dil mi?
    if text.startswith("/"):
        parts = text.split(maxsplit=1)
        cmd = parts[0].lower().split("@")[0]
        cmd_arg = parts[1] if len(parts) > 1 else ""
    else:
        cmd = _detect_command(text)
        cmd_arg = text  # doğal dilden gelen argüman (tercih için "sabah" vb.)

    is_admin = _is_admin(sender)

    # Admin komutuna yetkisiz erişim
    if cmd in ADMIN_COMMANDS and not is_admin:
        print("🚫 Bu komut yalnızca yetkili kullanıcılara açıktır.")
        sys.exit(1)

    # Komut yönlendirme
    if cmd == "/abone":
        cmd_abone(sender)
    elif cmd == "/iptal":
        cmd_iptal(sender)
    elif cmd == "/tercihler":
        cmd_tercihler(sender, cmd_arg)
    elif cmd in ("/yardim", "/start"):
        cmd_yardim(sender, is_admin)
    elif cmd == "/haber":
        cmd_haber()
    elif cmd == "/pi":
        cmd_pi()
    elif cmd == "/durum":
        cmd_durum()
    elif cmd == "/youtube":
        cmd_youtube()
    else:
        print(f"❓ Bilinmeyen komut: {cmd}\n/yardim yazarak komutları görebilirsin.")
