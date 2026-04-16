# Pi Servisleri

Raspberry Pi uzerinde calisan ya da calismasi planlanan servisleri
takip eden ust dosya.

## Aktif

- [ ] `llm_news.service` — LLM haber ozeti + Telegram botu (bkz. PR #6)

## Planlanan

- [ ] YouTube kanal takibi
- [ ] LED kontrol demo scripti (`led_control.py`)

## Komut Notlari

```bash
# Servis durumu
systemctl status llm_news.service

# Loglar
journalctl -u llm_news.service -f

# Yeniden baslat
sudo systemctl restart llm_news.service
```

---
Tags: #pi #servis #systemd
