# Pi Vault

Raspberry Pi uzerinde kurulu Obsidian uygulamasi icin ayri bir vault.
Repo root'undaki vault'tan bagimsiz calisir.

## Obsidian'da acma

1. Obsidian'i acin → sag alt kose → **Open folder as vault**.
2. `pi-vault/` klasorunu secin.
3. `.obsidian/` config'i otomatik okunacaktir.

## Git ile senkron

Vault bu repo icinde versiyonlanir:

```bash
cd ~/srky
git pull
# ... Obsidian'da notlari duzenleyin ...
git add pi-vault
git commit -m "notes: gunluk not"
git push
```

## Icerik

- `Notes/` — genel notlar, `Notes/Daily/` gunluk notlar
- `Projects/` — Pi servis/proje notlari
- `Templates/` — gunluk, proje, servis sablonlari
- `Attachments/` — resim ve dosya ekleri
