# Srky Alarm — Mobil PWA Alarm Uygulaması

Her telefonda çalışan (Android, iOS, vb.) basit ve hızlı bir alarm uygulaması.
Progressive Web App (PWA) olarak hazırlandığı için **uygulama mağazasına gerek yoktur** —
ana ekrana eklendiğinde gerçek bir uygulama gibi açılır, çevrimdışı da çalışır.

## Özellikler

- Büyük, okunaklı saat (24 saat biçimi)
- Dilediğin kadar alarm ekleyebilme
- **Tekrar günleri**: Tek sefer / Hafta içi / Hafta sonu / özel
- **4 farklı alarm sesi** (Web Audio API ile üretilir — ekstra dosya gerekmez)
- **Erteleme (snooze)** — 5 dakika
- **Titreşim** desteği (destekleyen cihazlarda)
- **Ekranı uyanık tutma** (Wake Lock API)
- **Sistem bildirimi** (izin verildiğinde)
- Karanlık / aydınlık tema
- Alarmlar **cihazda saklanır** (localStorage) — hiçbir veri sunucuya gitmez
- Tamamen **çevrimdışı** çalışır
- Açık / aydınlık tema desteği
- `safe-area` desteği ile çentikli telefonlarda bile düzgün görünür

## Kurulum / Çalıştırma

Uygulama tamamen statik (HTML/CSS/JS) — herhangi bir build adımı gerektirmez.

### Yerel olarak test etmek için

```bash
cd alarm-app
# Python 3 ile basit bir HTTP sunucu
python3 -m http.server 8000
```

Ardından telefonundan bilgisayarla aynı Wi-Fi ağına bağlanıp tarayıcıda
`http://<bilgisayarın-ip-adresi>:8000` adresine git.

> **Not:** Service Worker ve Wake Lock API gibi bazı özellikler için
> `http://localhost` dışında **HTTPS** gerekir. Yayınlamak için GitHub Pages,
> Netlify, Cloudflare Pages veya Vercel gibi ücretsiz bir servis kullanabilirsin
> — hepsi otomatik HTTPS sağlar.

### Telefona uygulama olarak yükleme

**Android (Chrome):**
1. Siteyi Chrome ile aç
2. Menü (⋮) → **Ana ekrana ekle**
3. Artık uygulama çekmecesinden başlatılabilir

**iOS (Safari):**
1. Siteyi Safari ile aç
2. Paylaş (↑) → **Ana Ekrana Ekle**
3. İkonu dokunarak aç

## Kullanım

1. **Saat** seç, isteğe bağlı **etiket** yaz (örn. "Okul", "Spor")
2. Tekrarlamasını istediğin **günleri** seç (hiç seçmezsen bir kez çalar)
3. **Ses** seç ve **Ekle**'ye bas
4. Alarmı istediğinde anahtarla **aç/kapat** ya da **Sil**'e basıp kaldır
5. Alarm çalarken **Durdur** veya **Ertele 5 dk** butonlarını kullan

## Önemli Notlar

- **Tarayıcı arka planda alarm çalar mı?** Uygulama açıkken veya sekme aktif/arka
  planda tutulduğunda çalar. Telefon tarayıcıları enerji tasarrufu için sekmeleri
  tamamen askıya alabilir. **En güvenilir kullanım için uygulamayı ana ekrana
  ekle ve gece ekranı kilitleme ya da uygulamayı aktif tut.**
- **Ses izni:** İlk açılışta tarayıcı, kullanıcı etkileşimi olmadan ses çalmaya
  izin vermez. Alt banner'daki **Hazırla** butonuna veya ekrana bir kez
  dokunduğunda ses sistemi etkinleşir.

## Dosya Yapısı

```
alarm-app/
├─ index.html      # Ana sayfa
├─ styles.css      # Mobil öncelikli, responsive stiller
├─ app.js          # Alarm mantığı + Web Audio API ile ses üretimi
├─ sw.js           # Service Worker (çevrimdışı destek)
├─ manifest.json   # PWA manifest
├─ icon.svg        # Uygulama ikonu
└─ README.md
```

## Teknoloji

- Saf HTML + CSS + Vanilla JavaScript (framework yok)
- Web Audio API ile dinamik alarm tonları
- Service Worker ile çevrimdışı çalışma
- localStorage ile kalıcı veri
- Wake Lock API ile ekranı uyanık tutma
- Notification API ile sistem bildirimleri

Herhangi bir bağımlılık, paket yöneticisi ya da build aşaması yoktur.
