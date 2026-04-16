"""
Throttle'lı Telegram broadcast.

`broadcast_html(text, slot)` — metni `_chunk_html_safe` ile parçalar,
seçili slot'taki aktif abonelere sırayla yollar.

Rate limit stratejisi:
- Telegram global: ≤30 msg/sn. İki çağrı arası 0.05s sleep (20 msg/sn
  tavanı — güvenli kenar).
- 429 Too Many Requests: response'taki `retry_after` kadar bekle, yeniden dene.
- 403 Forbidden (kullanıcı botu engellemiş): aboneyi pasifleştir.
- Diğer hatalar: log'la, sıradakine geç; admin alert yollamaz (bcast
  sırasında alert fırtınası istemiyoruz — admin alert'i çağıran taraf
  broadcast yüzdesi çok düşükse fırlatabilir).
"""
from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request

from subscribers.db import list_active, remove_subscriber

logger = logging.getLogger(__name__)

_TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
_THROTTLE_SEC = 0.05  # 20 msg/sn üst sınır
_RATE_LIMIT_RETRIES = 3


def _send_one(token: str, chat_id: str, text: str) -> str:
    """Tek mesaj yolla. Dönen değerler:
    - "ok"          : başarılı
    - "blocked"     : 403 — kullanıcı botu engellemiş, pasifleştirilmeli
    - "error:<msg>" : diğer hatalar, sıradakine geçilir
    """
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }).encode()
    url = _TELEGRAM_API.format(token=token)
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    for attempt in range(_RATE_LIMIT_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read())
            if result.get("ok"):
                return "ok"
            return f"error:{result}"
        except urllib.error.HTTPError as e:
            if e.code == 403:
                return "blocked"
            if e.code == 429:
                # Telegram retry_after veriyor, response body'den oku
                try:
                    body = json.loads(e.read())
                    retry_after = int(body.get("parameters", {}).get("retry_after", 1))
                except Exception:
                    retry_after = 1
                logger.warning("429 rate limit, %ds bekle (chat %s)", retry_after, chat_id)
                time.sleep(retry_after)
                continue
            return f"error:HTTP {e.code}"
        except urllib.error.URLError as e:
            return f"error:{e}"
    return "error:429 retry exhausted"


def broadcast_html(text: str, slot: str | None = None) -> dict:
    """Metni tüm aktif abonelere (slot filtresine göre) parçalayarak gönder.

    Args:
        text: HTML parse_mode için tam metin
        slot: "morning" | "evening" | None (tümü)

    Returns:
        dict: {"sent": int, "blocked": int, "failed": int, "total": int}
    """
    # Chunking'i routine.py'den import et (circular import'u önlemek için lazy)
    from llm_news.routine import _chunk_html_safe

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN set değil, broadcast yapılamıyor")
        return {"sent": 0, "blocked": 0, "failed": 0, "total": 0}

    recipients = list_active(slot=slot)
    chunks = _chunk_html_safe(text)
    if not recipients:
        logger.warning("Aktif abone yok (slot=%s), broadcast atlanıyor", slot)
        return {"sent": 0, "blocked": 0, "failed": 0, "total": 0}

    stats = {"sent": 0, "blocked": 0, "failed": 0, "total": len(recipients)}
    logger.info("Broadcast başlıyor: %d abone, %d chunk", len(recipients), len(chunks))

    for chat_id in recipients:
        all_chunks_ok = True
        for chunk in chunks:
            status = _send_one(token, chat_id, chunk)
            if status == "ok":
                time.sleep(_THROTTLE_SEC)
                continue
            if status == "blocked":
                logger.info("Abone %s botu engellemiş, pasifleştiriliyor", chat_id)
                remove_subscriber(chat_id)
                stats["blocked"] += 1
                all_chunks_ok = False
                break
            logger.warning("Abone %s'ye gönderilemedi: %s", chat_id, status)
            stats["failed"] += 1
            all_chunks_ok = False
            break
        if all_chunks_ok:
            stats["sent"] += 1

    logger.info(
        "Broadcast tamam: sent=%d blocked=%d failed=%d total=%d",
        stats["sent"], stats["blocked"], stats["failed"], stats["total"],
    )
    return stats
