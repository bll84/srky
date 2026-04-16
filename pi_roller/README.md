# pi_roller

Raspberry Pi uzerinde kurulu Obsidian uygulamasi icin ayri bir kasa
(vault). Ad, "Pi uzerinde calisan roller / rutinler" fikrinden geliyor.
Repo root'undaki vault'tan bagimsiz calisir.

## Obsidian'da acma

1. Obsidian'i acin → sag alt kose → **Open folder as vault**.
2. `pi_roller/` klasorunu secin.
3. `.obsidian/` config'i otomatik okunacaktir.

## Git ile senkron

Kasa bu repo icinde versiyonlanir:

```bash
cd ~/srky
git pull
# ... Obsidian'da notlari duzenleyin ...
git add pi_roller
git commit -m "notes: gunluk not"
git push
```

## Icerik

- `Notes/` — genel notlar, `Notes/Daily/` gunluk notlar
- `Projects/` — Pi servis/proje notlari
- `Templates/` — gunluk, proje, servis sablonlari
- `Attachments/` — resim ve dosya ekleri
