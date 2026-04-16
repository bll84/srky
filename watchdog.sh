#!/bin/bash
# Servisi kontrol et, çökmüşse yeniden başlat ve Telegram'a bildir

source /home/bllsrky/srky/.env

send_telegram() {
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        -d "chat_id=${TELEGRAM_CHAT_ID}" \
        -d "text=$1" \
        -d "parse_mode=HTML" > /dev/null
}

if ! systemctl is-active --quiet llm_news; then
    echo "[$(date)] Servis çökmüş, yeniden başlatılıyor..."
    sudo systemctl restart llm_news
    sleep 5
    if systemctl is-active --quiet llm_news; then
        send_telegram "⚠️ <b>llm_news servisi yeniden başlatıldı.</b>&#10;Otomatik kurtarma başarılı."
    else
        send_telegram "❌ <b>llm_news servisi başlatılamadı!</b>&#10;Manuel müdahale gerekiyor."
    fi
fi
