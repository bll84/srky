# Hadith Content Studio v3.0 - Multi-API CLI

Kişisel kullanım için Python komut satırı aracı - Google Gemini, Claude, OpenAI desteğiyle.

---

## ⚙️ Kurulum (5 dakika)

### 1️⃣ Python Kütüphanelerini Yükle

```bash
# Temel kütüphaneler
pip install python-dotenv

# Kullanmak istediğin API'lerin kütüphanelerini yükle
pip install google-generativeai    # Google Gemini için
pip install anthropic              # Claude için
pip install openai                 # OpenAI için

# Ya da hepsini aynı anda:
pip install python-dotenv google-generativeai anthropic openai
```

### 2️⃣ API Key'leri Al

**Google Gemini:**
- Git: https://aistudio.google.com/app/apikey
- "Create API Key" tıkla
- Anahtarı kopyala: `AIzaSy...`

**Claude (Opsiyonel):**
- Git: https://console.anthropic.com/api-keys
- "Create Key" tıkla
- Anahtarı kopyala: `sk-ant-v4-...`

**OpenAI (Opsiyonel):**
- Git: https://platform.openai.com/api-keys
- "Create new secret key" tıkla
- Anahtarı kopyala: `sk-...`

### 3️⃣ .env Dosyasını Oluştur

```bash
# Şablon dosyasını kopyala
cp .env.example .env

# Metin editörü aç
nano .env
# veya
code .env
```

`.env` dosyasını düzenle ve API key'lerini yapıştır:

```
# Google Gemini (şu anda kullanıyorsun)
GOOGLE_API_KEY=AIzaSyCRaGIhYeZRNd9NL_OgzqCXVxEyMnkJgaU

# Claude (isteğe bağlı)
ANTHROPIC_API_KEY=

# OpenAI (isteğe bağlı)
OPENAI_API_KEY=
```

En az **bir API key** lazım. İstediğin diğerini daha sonra ekleyebilirsin.

---

## 🚀 Program Başlat

```bash
python hadith-studio.py
```

### Menü Görünür

```
============================================================
🔌 API SAĞLAYICISI SEÇ
============================================================

1. ✅ Google Gemini
2. ❌ Anthropic Claude
3. ❌ OpenAI GPT
4. API key'i güncelle

Seçim (1-4):
```

Yapılandırılmış API'yi seç (1) ya da yeni key ekle (4).

---

## 💬 İlk Hadis

Menü seçenekleri:

```
1. Hadis gir (yeni)
2. Özel komut gönder
3. API sağlayıcısını değiştir
4. Çık

Seçim (1-4): 1
```

Hadis gir:

```
============================================================
📝 HADİS GİRİŞİ
============================================================

Hadis metnini gir (Enter'den sonra Ctrl+D ile bitir):

Ebû Hüreyre (r.a.)'den rivayet edildiğine göre Rasûlullah
(s.a.v.) şöyle buyurdu: "Müminin haline şaşarım!..."
^D
```

---

## ✨ Iş Akışı

### AŞAMA 1: Kelime Analizi
- Sistem eski kelimeleri tespit eder
- Tablo gösterir
- Seçim bekler

### AŞAMA 2: Seçim Yap
```
✏️  Seçiminizi yazın: hepsini uygula
```

Seçenekler:
- `hepsini uygula` - Tüm değişiklikleri uygula
- `sadece yeşilleri` - Sadece 🟢 (güvenli) olanları
- `1, 3 uygula` - Belirtilen numaraları
- `değiştirme` - Orijinal metni koru

### AŞAMA 3: Format Seç
```
✏️  Seçiminizi yazın: video
```

Seçenekler:
- `video` - Tam format (1-3 dakika)
- `shorts` - Kısa format (60 saniye)
- `sadece hadis` - Minimal format

### AŞAMA 4: Senaryo Üretilir
Senaryo otomatik olarak:
- Terminal'de gösterilir
- `outputs/scripts/` klasöründe kaydedilir

---

## 📁 Dosya Yapısı

```
hadith-studio/
├── hadith-studio.py          ← Ana program (Multi-API)
├── .env                       ← Senin API key'lerin (sakın paylaşma!)
├── .env.example               ← Şablon
├── QUICK_START.md             ← Bu dosya
└── outputs/                   ← Çıktılar (otomatik oluşur)
    ├── analyses/              ← Kelime analiz dosyaları
    └── scripts/               ← Seslendirme senaryoları
```

---

## 🔄 API Değiştir

Program içinde istediğin zaman:

```
Seçim (1-4): 3
```

Başka API sağlayıcısına geç (ör. Claude'a)

---

## 🔧 Sorun Giderme

### Problem: "API key bulunamadı"

**Çözüm:**
1. `.env` dosyası var mı?
2. API key tam kopyalandı mı?
3. Dosyayı kaydettin mi?
4. Programı yeniden başlat

### Problem: "kütüphanesi yüklü değil"

```
google-generativeai kütüphanesi yüklü değil
```

**Çözüm:**
```bash
pip install google-generativeai
```

### Problem: Menüde API'ler gözükmüyor

- En az bir API key'i `.env`'de gir
- `GOOGLE_API_KEY=AIzaSy...` formatında olsun
- Boş satırlardan kaçın

### Problem: Metin girme başarısız (Windows)

Metni yaz, sonra:
```
Ctrl+Z
Enter
```

---

## 📝 Komutlar

### Ana Menü
```
1 = Hadis gir
2 = Özel komut
3 = API değiştir
4 = Çık
```

### Kelime Seçimleri
```
hepsini uygula    | sadece yeşilleri | 1,3 uygula | değiştirme
```

### Format Seçimleri
```
video | shorts | sadece hadis
```

### Özel Komutlar
```
direkt seslendirme    → Kelime analizi atla
sadece analiz         → Sadece kelime analizi yap
shorts yap            → Direkt shorts format
tekrar                → Son işlemi tekrarla
```

---

## 💡 En İyi Uygulamalar

1. **Başta Gemini dene** - Hızlı ve başarılı
2. **Claude'a geç** - Uzun hadisler için
3. **OpenAI** - Alternatif ve back-up
4. **Dosyaları kontrol et** - `outputs/` klasöründe

---

## 🔐 Güvenlik

- ❌ `.env` dosyasını GitHub'a koyma
- ❌ API key'ini kimseyle paylaşma
- ✅ `.env` dosyasında tut
- ✅ `.gitignore` tarafından korunuyor

---

## 🆘 Destek

**Kütüphane kurulum sorunları:**
- Google: `pip install google-generativeai`
- Claude: `pip install anthropic`
- OpenAI: `pip install openai`

**API key sorunları:**
- Google: https://aistudio.google.com/app/apikey
- Claude: https://console.anthropic.com/api-keys
- OpenAI: https://platform.openai.com/api-keys

---

**Version**: 3.0 Multi-API
**Python**: 3.7+
**Hazırlama Tarihi**: 2026-01-02
**Durum**: Üretim Hazır ✅
