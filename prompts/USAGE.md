# Hadith Content Studio v3.0 - Kullanım Kılavuzu

## 📋 Hakkında

Hadith Content Studio v3.0, "İyilerin Yolu" YouTube kanalı için iki aşamalı bir hadis içerik üretim sistemidir:
1. **Kelime Modernleştirme**: Eski kelimeleri tespit edip, modern Türkçe karşılık sunma
2. **Seslendirme Senaryosu**: ElevenLabs TTS için profesyonel senaryo oluşturma

## 🚀 AI Studio'da Nasıl Kullanılır

### Adım 1: System Prompt'u Ayarla
1. AI Studio arayüzünde **System Instructions** bölümünü aç
2. `hadith-content-studio-v3.0.md` dosyasının içeriğini kopyala
3. Yapıştır ve kaydet

### Adım 2: Hadis Gönder
Herhangi bir hadis metni gönder:
```
Ebû Hüreyre (r.a.)'den rivayet edildiğine göre Rasûlullah (s.a.v.)
şöyle buyurdu: "Müminin haline şaşarım!..."
```

### Adım 3: Sistem Otomatik İşler
- **AŞAMA 1**: Eski kelimeleri tespit eder ve tablo ile gösterir
- **Seçim**: Hangi değişiklikleri uygulamak istediğini belirlersin
- **AŞAMA 2**: Seçimin uygulanır ve format seçeneği sunulur
- **AŞAMA 3**: Seçilen formatta (video/shorts/hadis) seslendirme senaryosu üretilir

## 📝 Kullanıcı Komutları

```
hepsini uygula      → Tüm önerilen değişiklikleri uygula
sadece yeşilleri    → Sadece 🟢 (güvenli) değişiklikleri uygula
1, 3 uygula         → Belirtilen numaralar için önerileri uygula
değiştirme          → Orijinal metni koru, seslendirmeye geç

video               → Tam video format senaryosu (1-3 dk)
shorts              → Kısa video senaryosu (max 60 sn)
sadece hadis        → Minimal senaryodaki hadis metni

direkt seslendirme  → Kelime analizi atla, direkt senaryo
sadece analiz       → Sadece kelime analizi yap, seslendirme yapma
shorts yap          → Kısa format senaryo oluştur
tekrar              → Son işlemi tekrarla
```

## ⚙️ Sistem Konfigürasyonu

### Önerilen AI Modeli Ayarları
- **Model**: Gemini 1.5 Pro (veya Claude 3 Opus)
- **Temperature**: 0.4 (tutarlı ve kontrollü çıktı)
- **Top P**: 0.8
- **Top K**: 40
- **Max Tokens**: 4096

### Önemli Notlar
- Sistem her zaman **iki aşamalı iş akışı** izler
- Kullanıcı onayı olmadan hiçbir değişiklik otomatik uygulanmaz
- Seslendirme senaryosunda ASLA açıklama, başlık veya meta veri yazmaz
- Tüm seslendirme senaryoları **doğrudan direktifle başlar** `[sakin açılış]` gibi

## 📚 Korunan Terimler

Sistem aşağıdaki terimleri **ASLA değiştirmez**:

**Dini İsimler & Kavramlar:**
- Allah, Rab, Rahman, Rahim
- takva, iman, ihsan, islam, hidayet
- cennet, cehennem, ahiret

**İbadetler:**
- namaz, oruç, zekat, hac

**Hukuki Terimler:**
- sünnet, farz, haram, helal

**Salavat Formülü:**
- sallallahu aleyhi ve sellem (s.a.v. YAZILMAZ)
- radıyallahu anh/anha (r.a. YAZILMAZ)

## 🎯 En İyi Uygulamalar

1. **Kontrollü Değişiklikler**: Başta "sadece yeşilleri" seçerek güvenli değişiklikleri test et
2. **Dini Duyarlılık**: 🟠 (orta risk) değişiklikleri dikkatli değerlendir
3. **Senaryo Kalitesi**: Seslendirme senaryosunu ElevenLabs'a göndermeden önce kontrol et
4. **Batch İşleme**: Birden fazla hadis varsa, hepsini sırayla işle

## 🔧 Sorun Giderme

### Problem: Sistem "Markdown formatı" yazıyor
**Çözüm**: System Prompt'u kontrol et. "ASLA YAZMA" bölümü düzgün kopyalanmış mı?

### Problem: Senaryo önerileri uygulanmıyor
**Çözüm**: Komutunu tam yazın. Örnek: `hepsini uygula` (virgül yok)

### Problem: Kısa kelimeleri tespit etmiyor
**Çözüm**: Normal davranış. Sistem yalnızca gerçek arkaik kelimeleri hedefler.

## 📞 Destek

Herhangi bir sorun için:
1. System Prompt'un güncel olup olmadığını kontrol et
2. Komutu tam yazıp yazıp yazmadığını kontrol et
3. Model ayarlarını önerilen konfigürasyonla karşılaştır

---

**Version**: 3.0
**Last Updated**: 2026-01-02
**Channel**: İyilerin Yolu (YouTube)
