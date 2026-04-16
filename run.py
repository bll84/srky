"""
Pi Rutinleri — Zamanlayıcı

- LLM Haber Özeti: 07:00 ve 18:00 (Istanbul)
- YouTube Kanal Takibi: her saat başı

Usage:
    python run.py

Tek seferlik test:
    python -c "from llm_news.routine import run_news_routine; run_news_routine()"
    python -c "from youtube_tracker.tracker import run_youtube_tracker; run_youtube_tracker()"
"""

import json
import logging
import os
import time
from datetime import datetime

import pytz
import schedule
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

with open(os.path.join(os.path.dirname(__file__), "config.json")) as _f:
    _CFG = json.load(_f)

from llm_news.routine import run_news_routine  # noqa: E402
from youtube_tracker.tracker import run_youtube_tracker  # noqa: E402

ISTANBUL_TZ = pytz.timezone("Europe/Istanbul")

# Track last run date per hour slot to prevent double-firing
_last_run: dict[int, str] = {}


def run_if_istanbul_time(target_hour: int) -> None:
    """Check Istanbul clock and run the routine exactly once per day per slot."""
    now = datetime.now(ISTANBUL_TZ)
    today = now.strftime("%Y-%m-%d")
    if now.hour == target_hour and _last_run.get(target_hour) != today:
        _last_run[target_hour] = today
        run_news_routine()


if __name__ == "__main__":
    # LLM haberleri: config'den saatleri al
    schedule.every().minute.do(run_if_istanbul_time, target_hour=_CFG["news"]["morning_hour"])
    schedule.every().minute.do(run_if_istanbul_time, target_hour=_CFG["news"]["evening_hour"])

    # YouTube takibi: config'den interval al
    schedule.every(_CFG["youtube"]["check_interval_hours"]).hours.do(run_youtube_tracker)

    logger.info("Zamanlayici basladi.")
    logger.info("LLM haberleri: 07:00 ve 18:00 Istanbul")
    logger.info("YouTube takibi: her saat basi")

    # İlk çalıştırmada YouTube'u hemen kontrol et
    run_youtube_tracker()

    while True:
        schedule.run_pending()
        time.sleep(30)
