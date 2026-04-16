"""Tek seferlik test çalıştırması."""
import logging
from llm_news.routine import run_news_routine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
run_news_routine()
