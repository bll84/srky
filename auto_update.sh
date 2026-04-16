#!/bin/bash
# Değişiklik varsa kodu çek ve servisi yeniden başlat.
# Güvenlik:
#   - Sadece fast-forward pull (force-push ile history yeniden yazılamaz)
#   - Beklenen origin URL doğrulaması (origin kaçırılmasına karşı)
#   - Beklenen branch doğrulaması
#   - flock ile eşzamanlı çalıştırma engeli

set -euo pipefail

REPO_DIR="/home/bllsrky/srky"
BRANCH="claude/setup-llm-news-routine-2wkrV"
EXPECTED_REMOTE_REGEX='^(https://github\.com/|git@github\.com:)bll84/srky(\.git)?$'
LOCK_FILE="/tmp/srky_autoupdate.lock"

cd "$REPO_DIR"

# Eşzamanlı çalışmayı engelle — cron üst üste binerse ikinci çalışma sessizce çıkar
exec 200>"$LOCK_FILE"
if ! flock -n 200; then
    echo "[$(date)] Başka bir güncelleme sürüyor, çıkılıyor."
    exit 0
fi

# Remote URL'i doğrula — origin değiştirilip başka repoya yönlendirilmişse dur
ACTUAL_REMOTE=$(git remote get-url origin)
if ! [[ "$ACTUAL_REMOTE" =~ $EXPECTED_REMOTE_REGEX ]]; then
    echo "[$(date)] HATA: beklenmeyen origin URL: $ACTUAL_REMOTE"
    exit 1
fi

# Branch kilidi — yanlış branch'te çalışma
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
    echo "[$(date)] HATA: $BRANCH bekleniyordu, $CURRENT_BRANCH üzerindeyiz."
    exit 1
fi

LOCAL=$(git rev-parse HEAD)
git fetch origin "$BRANCH" --quiet
REMOTE=$(git rev-parse "origin/$BRANCH")

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "[$(date)] Güncelleme yok."
    exit 0
fi

# --ff-only: history yeniden yazılmışsa (force-push) pull reddeder, sessiz
# şekilde malicious kod deploy edilmez
if ! git pull --ff-only --quiet origin "$BRANCH"; then
    echo "[$(date)] HATA: fast-forward değil, pull reddedildi. Manuel inceleme gerekli."
    exit 1
fi

NEW=$(git rev-parse HEAD)
echo "[$(date)] Güncellendi: ${LOCAL:0:7} → ${NEW:0:7}"
sudo systemctl restart llm_news
echo "[$(date)] Servis yeniden başlatıldı."
