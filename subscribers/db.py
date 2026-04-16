"""
Abone veritabanı — SQLite wrapper.

Tek dosya (`subscribers.db`), stdlib'den `sqlite3`. Migration için küçük
bir şema sürümü tablosu var; gelecekte tier/ödeme sütunları eklenirken
patlatmadan genişler.

Kullanım:
    from subscribers.db import (
        init_db, add_subscriber, remove_subscriber,
        set_slot, list_active, count_active, get_subscriber,
    )

Tüm fonksiyonlar thread-safe değil; mevcut mimaride tek bir süreç
(run.py) yazar, bot_commands.py da tek seferlik subprocess olarak
çağrıldığı için eşzamanlı yazım olmuyor. İleride asyncio broadcast
eklenirse her fonksiyon kendi connection'ını açıp kapattığı için
sorun çıkmaz.
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from typing import Iterator

_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "subscribers.db")

VALID_SLOTS = {"morning", "evening", "both"}
VALID_TIERS = {"free", "pro"}

SCHEMA_VERSION = 1


@contextmanager
def _conn() -> Iterator[sqlite3.Connection]:
    """SQLite bağlantısı — foreign keys + row factory açık, her zaman commit/close."""
    conn = sqlite3.connect(_DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Şemayı kur (idempotent). run.py ve bot_commands.py başlangıcında çağrılır."""
    with _conn() as c:
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS subscribers (
                chat_id    TEXT PRIMARY KEY,
                joined_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                active     INTEGER NOT NULL DEFAULT 1,
                slot       TEXT NOT NULL DEFAULT 'both'
                              CHECK (slot IN ('morning', 'evening', 'both')),
                tier       TEXT NOT NULL DEFAULT 'free'
                              CHECK (tier IN ('free', 'pro'))
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_meta (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        c.execute(
            "INSERT OR IGNORE INTO schema_meta(key, value) VALUES ('version', ?)",
            (str(SCHEMA_VERSION),),
        )


def add_subscriber(chat_id: str, slot: str = "both") -> bool:
    """Yeni abone ekle veya reaktive et. Zaten aktifse False, yeni/reaktive ise True.

    Aynı chat_id daha önce `/iptal` etmiş olabilir; `/abone` tekrar ederse
    active=1 yapılır ama slot tercihi korunur.
    """
    if slot not in VALID_SLOTS:
        raise ValueError(f"Geçersiz slot: {slot}")
    with _conn() as c:
        row = c.execute(
            "SELECT active FROM subscribers WHERE chat_id = ?", (chat_id,)
        ).fetchone()
        if row is None:
            c.execute(
                "INSERT INTO subscribers(chat_id, slot) VALUES (?, ?)",
                (chat_id, slot),
            )
            return True
        if row["active"]:
            return False
        c.execute(
            "UPDATE subscribers SET active = 1 WHERE chat_id = ?", (chat_id,)
        )
        return True


def remove_subscriber(chat_id: str) -> bool:
    """Soft delete — active=0. Kayıt korunur (istatistik, reaktive için).

    True: daha önce aktifti ve iptal edildi. False: zaten iptal veya kayıt yok.
    """
    with _conn() as c:
        cur = c.execute(
            "UPDATE subscribers SET active = 0 WHERE chat_id = ? AND active = 1",
            (chat_id,),
        )
        return cur.rowcount > 0


def set_slot(chat_id: str, slot: str) -> bool:
    """Slot tercihini değiştir. Abone yoksa False."""
    if slot not in VALID_SLOTS:
        raise ValueError(f"Geçersiz slot: {slot}")
    with _conn() as c:
        cur = c.execute(
            "UPDATE subscribers SET slot = ? WHERE chat_id = ?", (slot, chat_id)
        )
        return cur.rowcount > 0


def get_subscriber(chat_id: str) -> dict | None:
    """Tek abonenin bilgisini döner (active=0 dahil). Yoksa None."""
    with _conn() as c:
        row = c.execute(
            "SELECT chat_id, joined_at, active, slot, tier FROM subscribers "
            "WHERE chat_id = ?",
            (chat_id,),
        ).fetchone()
        return dict(row) if row else None


def list_active(slot: str | None = None) -> list[str]:
    """Aktif abonelerin chat_id listesi.

    slot parametresi verilirse (morning/evening), o slota uyanlar döner:
    - "morning" → slot IN ('morning', 'both')
    - "evening" → slot IN ('evening', 'both')
    - None      → tüm aktifler
    """
    with _conn() as c:
        if slot is None:
            rows = c.execute(
                "SELECT chat_id FROM subscribers WHERE active = 1 "
                "ORDER BY joined_at"
            ).fetchall()
        elif slot in ("morning", "evening"):
            rows = c.execute(
                "SELECT chat_id FROM subscribers WHERE active = 1 "
                "AND slot IN (?, 'both') ORDER BY joined_at",
                (slot,),
            ).fetchall()
        else:
            raise ValueError(f"Geçersiz slot filtresi: {slot}")
        return [r["chat_id"] for r in rows]


def count_active() -> int:
    with _conn() as c:
        return c.execute(
            "SELECT COUNT(*) AS n FROM subscribers WHERE active = 1"
        ).fetchone()["n"]
