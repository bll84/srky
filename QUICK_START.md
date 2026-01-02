# Hadith Content Studio v3.0 - Python CLI

Kişisel kullanım için Python komut satırı aracı.

---

## ⚙️ Kurulum (5 dakika)

### 1️⃣ Kütüphaneleri Yükle

```bash
pip install anthropic python-dotenv
```

### 2️⃣ API Key Al

1. Git: https://console.anthropic.com/api-keys
2. "Create Key" tıkla
3. Anahtarı kopyala: `sk-ant-v4-xxxx...`

### 3️⃣ .env Dosyasını Oluştur

```bash
# .env.example dosyasını kopyala
cp .env.example .env

# Metin editörü aç
nano .env
# veya
code .env
```

`.env` içine bu satırı gir ve API key'ini yapıştır:

```
ANTHROPIC_API_KEY=sk-ant-v4-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Kaydet ve kapat.

---

## 🚀 Kullanım

### Program Başlat

```bash
python hadith-studio.py
```

### Menü Görünür

```
============================================================
🕌 HADITH CONTENT STUDIO v3.0
İyilerin Yolu YouTube Kanalı
============================================================

👋 Hoşgeldin! Hadis gir, sistemi çalıştıralım.

------------------------------------------------------------
💡 Ne yapmak istiyorsun?
------------------------------------------------------------

1. Hadis gir (yeni)
2. Özel komut gönder (direkt seslendirme, sadece analiz, vb)
3. Çık

Seçim (1-3):
```

### 1️⃣ Hadis Gir

```
Seçim (1-3): 1

============================================================
📝 HADİS GİRİŞİ
============================================================

Hadis metnini gir (Enter'den sonra Ctrl+D ile bitir):

Ebû Hüreyre (r.a.)'den rivayet edildiğine göre Rasûlullah
(s.a.v.) şöyle buyurdu: "Müminin haline şaşarım! Onun her hali
hayırdır..."
^D
```

### 2️⃣ Sistem Otomatik Çalışır

**AŞAMA 1: Kelime Analizi**
- Eski kelimeleri tespit eder
- Tablo gösterir
- Bekler

**Cevap Ver:**
```
hepsini uygula
```

**AŞAMA 2: Senaryo Formatı**
- Format seçenekleri sunulur
- Seçim yap

**Cevap Ver:**
```
video
```

**AŞAMA 3: Senaryo Üretilir**
- `outputs/scripts/` klasörüne kaydedilir
- Terminal'de gösterilir

---

## 📁 Dosya Yapısı

```
hadith-studio/
├── hadith-studio.py          ← Ana program
├── .env                       ← API key (sen gireceksin)
├── .env.example               ← Template
├── outputs/
│   ├── analyses/              ← Kelime analizi çıktıları
│   └── scripts/               ← Seslendirme senaryoları
└── QUICK_START.md             ← Bu dosya
```

---

## 📝 Komutlar

### Kelime Seçimleri

```
hepsini uygula        → Tüm değişiklikleri uygula
sadece yeşilleri      → Sadece 🟢 (güvenli) olanları
1, 3 uygula           → Belirtilen numaraları uygula
değiştirme            → Orijinal metni koru
```

### Format Seçimleri

```
video                 → Tam format (1-3 dakika)
shorts                → Kısa format (60 saniye)
sadece hadis          → Minimal format
```

### Özel Komutlar

```
direkt seslendirme    → Kelime analizi atla
sadece analiz         → Sadece kelime analizi yap
shorts yap            → Direkt shorts format
tekrar                → Son işlemi tekrarla
```

---

## 🔧 Sorun Giderme

### Problem: "API key bulunamadı"

```
❌ HATA: API key bulunamadı!
```

**Çözüm:**
1. `.env` dosyası var mı kontrol et
2. `ANTHROPIC_API_KEY=` satırı var mı?
3. Key tam mı kopyalanmış?
4. Programı yeniden başlat

### Problem: "module not found"

```
ModuleNotFoundError: No module named 'anthropic'
```

**Çözüm:**
```bash
pip install anthropic python-dotenv
```

### Problem: Ctrl+D çalışmıyor (Windows)

Windows'ta metni bitirmek için:
```
İçeriği yaz
Ctrl+Z
Enter
```

---

## 💡 İpuçları

1. **Çokça test et**: Farklı hadislerle dene
2. **Dosyalar kaydediliyor**: `outputs/` klasöründe saklanıyor
3. **Konuşma devam ediyor**: Aynı hadisle devam edebilirsin
4. **Yeni hadis**: Program menüsüne dön (3 → 1)

---

## ❓ Sorular?

- API key sorunları: https://console.anthropic.com/docs
- Python kurulum: https://www.python.org/downloads/
- Hadis talebi: Programda yazarak ilet

---

**Version**: 3.0
**Python**: 3.7+
**Hazırlanma Tarihi**: 2026-01-02
