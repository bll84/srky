"""
LLM News Email Routine — Scheduler Entry Point

Runs the LLM news digest twice daily at 07:00 and 18:00 Istanbul time.

Usage:
    python run.py

For a one-off test run:
    python -c "from llm_news.routine import run_news_routine; run_news_routine()"
"""

import logging
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

from llm_news.routine import run_news_routine  # noqa: E402 (after logging setup)

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
    schedule.every().minute.do(run_if_istanbul_time, target_hour=7)
    schedule.every().minute.do(run_if_istanbul_time, target_hour=18)

    logger.info(
        "Zamanlayici basladi. Istanbul saatiyle 07:00 ve 18:00'de calisacak."
    )

    while True:
        schedule.run_pending()
        time.sleep(30)
