# {{title}}

## Amac


## Unit Dosyasi

`/etc/systemd/system/{{title}}.service`

```ini
[Unit]
Description=
After=network-online.target

[Service]
Type=simple
ExecStart=
Restart=on-failure
User=pi

[Install]
WantedBy=multi-user.target
```

## Kurulum Komutlari

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now {{title}}.service
```

## Log ve Teshis

```bash
systemctl status {{title}}.service
journalctl -u {{title}}.service -n 200 --no-pager
```

---
Tags: #pi #servis #systemd
