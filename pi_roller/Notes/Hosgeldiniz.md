# Hosgeldiniz — pi_roller

Bu kasanin adi **pi_roller**: Pi'de donen "roller / rutinler" fikrinden
geliyor (haber ozeti, YouTube takibi, LED kontrol vb.). Raspberry Pi
uzerinde kurulu Obsidian icin acildi; amac Pi ile alakali notlari,
servis kayitlarini ve proje dokumantasyonunu repo'daki diger vault'tan
ayri tutmak.

## Klasor Yapisi

- **Notes/** — Genel notlar, arastirmalar, cheatsheet'ler
- **Notes/Daily/** — Gunluk notlar (YYYY-MM-DD.md)
- **Projects/** — Pi uzerinde calisan/calisacak projeler
- **Templates/** — Not sablonlari
- **Attachments/** — Ekran goruntuleri ve dosyalar

## Pi'de Kullanim Ipuclari

1. Obsidian'i `snap install obsidian --classic` veya AppImage ile kurdugunuzda,
   bu klasoru `Open folder as vault` ile acabilirsiniz.
2. Repo klonlu oldugu surece `git pull` ile notlar senkron kalir; degisiklikleri
   Pi'den commit etmek icin `git commit && git push` yeterli.
3. Dosya ekleri `Attachments/` klasorune dusecegi icin vault git'i hafif kalir.

## Hizli Komutlar

- Yeni not: `Ctrl+N`
- Hizli gec: `Ctrl+O`
- Komut paleti: `Ctrl+P`
- Graph: sol paneldeki dugum ikonu

## Bag Kurma

Notlar arasinda baglanti: `[[Not Adi]]` seklinde yazin.

---
Tags: #pi #pi_roller #giris
