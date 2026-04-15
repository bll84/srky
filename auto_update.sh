#!/bin/bash
# Değişiklik varsa kodu çek ve servisi yeniden başlat

cd /home/bllsrky/srky || exit 1

LOCAL=$(git rev-parse HEAD)
git fetch origin claude/setup-llm-news-routine-2wkrV --quiet
REMOTE=$(git rev-parse origin/claude/setup-llm-news-routine-2wkrV)

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "[$(date)] Yeni güncelleme bulundu, çekiliyor..."
    git pull --quiet
    sudo systemctl restart llm_news
    echo "[$(date)] Servis yeniden başlatıldı."
else
    echo "[$(date)] Güncelleme yok."
fi
