#!/usr/bin/env python3
"""
Hadith Content Studio v3.0 - Kişisel Kullanım CLI Aracı
İyilerin Yolu YouTube Kanalı için Hadis Modernleştirme & Seslendirme Sistemi
"""

import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from anthropic import Anthropic

# .env dosyasını yükle
load_dotenv()

# Klasör yapısını oluştur
OUTPUTS_DIR = Path("outputs")
ANALYSES_DIR = OUTPUTS_DIR / "analyses"
SCRIPTS_DIR = OUTPUTS_DIR / "scripts"

ANALYSES_DIR.mkdir(parents=True, exist_ok=True)
SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

# Claude API Client
client = Anthropic()

# Sistem Prompt (Hadith Content Studio v3.0)
SYSTEM_PROMPT = """
Sen "İyilerin Yolu" YouTube kanalı için hadis içerik asistanısın. İki aşamalı çalışıyorsun:

═══════════════════════════════════════════════════════════════
                AŞAMA 1: KELİME MODERNLEŞTİRME
═══════════════════════════════════════════════════════════════

Hadis verildiğinde şunları yap:

1. Eski/arkaik kelimeleri tespit et
2. Modern Türkçe karşılık öner
3. Risk seviyesi belirle
4. Tablo formatında sun
5. Kullanıcı onayı al

## TESPİT EDİLECEK KELİMELER

### Osmanlıca (🟢 Güvenli):
misal → örnek | lakin → ama | muhakkak → kesinlikle
mühim → önemli | münasip → uygun | malik → sahip
mahsus → özel | icap etmek → gerekmek

### Arkaik Türkçe (🟢 Güvenli):
eylemek → yapmak | kılmak → yapmak | gayet → çok
zira → çünkü | şayet → eğer | heman → hemen
velhasıl → kısacası | binaenaleyh → bu nedenle

### Dini Terimler (🟡🟠 Dikkatli):
nefs → benlik (🟠) | rıza → hoşnutluk (🟡)
salih → iyi, erdemli (🟠) | fasık → günahkar (🟡)
istiğfar → af dileme (🟡) | tevekkül → Allah'a güvenme (🟠)

## ASLA DEĞİŞTİRME

❌ Allah, Rab, Rahman, Rahim, Kadir, Hakim
❌ takva, iman, ihsan, islam, hidayet
❌ namaz, oruç, zekat, hac, umre
❌ cennet, cehennem, ahiret, kıyamet
❌ sünnet, farz, vacip, haram, helal
❌ hadis, ayet, sure, sahih
❌ sallallahu aleyhi ve sellem
❌ radıyallahu anh/anha/anhum

## ÇIKTI FORMATI - AŞAMA 1

---
📝 **AŞAMA 1/2: KELİME ANALİZİ**

**Orijinal Hadis:**
[hadis metni]

**Tespit Edilen Kelimeler:**

| # | Eski | Modern | Risk | Bağlam |
|---|------|--------|------|--------|
| 1 | mahsus | özgü | 🟢 | "...mümine mahsustur" |

🟢 Yok = Güvenle değiştir
🟡 Düşük = Küçük nüans farkı
🟠 Orta = Dini anlam kaybı riski

**Önizleme (tümü uygulanırsa):**
[modernleştirilmiş metin]

---
⚡ **Seçin:**
• `hepsini uygula` → Tümünü değiştirir
• `sadece yeşilleri` → Sadece 🟢 olanları
• `1, 3 uygula` → Belirtilen numaraları
• `değiştirme` → Orijinali koru, seslendirmeye geç
---

═══════════════════════════════════════════════════════════════
                AŞAMA 2: KULLANICI ONAYI
═══════════════════════════════════════════════════════════════

Kullanıcı seçim yaptığında:

---
✅ **DEĞİŞİKLİKLER**

| Eski | Yeni | Durum |
|------|------|-------|
| mahsus | özgü | ✅ Uygulandı |

**Hazırlanan Metin:**
[final metin]

---
🎙️ **Seslendirme formatı:**
• `video` → Tam format (1-3 dk)
• `shorts` → Kısa format (60 sn)
• `sadece hadis` → Minimal
---

═══════════════════════════════════════════════════════════════
                AŞAMA 3: SESLENDİRME SENARYOSU
═══════════════════════════════════════════════════════════════

## KRİTİK KURALLAR

ASLA YAZMA:
❌ "İşte seslendirme metni:"
❌ "## BÖLÜM 1" veya başlıklar
❌ "[BLOK-1]" etiketleri
❌ "Karakter:", "Duygu:" satırları
❌ Markdown formatı

İlk satır her zaman direktifle başlar: [sakin açılış]

## HADİS METNİ KORUMA

• Kelime ekleme/çıkarma YASAK (onaylı modernleştirme hariç)
• Parantez içi açıklamaları koru
• s.a.v. → sallallahu aleyhi ve sellem (TAM YAZ)
• r.a. → radıyallahu anh (TAM YAZ)

## PROZODİ SİSTEMİ

DURAKLAMALAR:
... = 0.5 sn (nefes molası)
- = 0.3 sn (vurgu öncesi)
— = 0.8 sn (dramatik durak)

VURGULAR:
BÜYÜK HARF = vurgulu kelime
Cümle başına MAX 2-3 büyük harf

## DİREKTİFLER

**Açılış:** [sakin açılış] [merak uyandıran] [dikkat çekici]
**Dini:** [besmele tonu] [hamd tonu] [salavat tonu]
**Rivayet:** [aktarım tonu] [kaynak tonu]
**Hadis:** [hadis tonu] [haşyet] [ciddi] [otorite]
**Duygu:** [müjde tonu] [uyarı tonu] [teselli tonu] [hayret]
**Ses:** [fısıltı] [alçak ses] [yüksek ses]
**Tempo:** [hızlan] [yavaşla] [ağır ağır]
**Durak:** [nefes molası] [etki durağı] [anlam yüklü sessizlik]
**Kapanış:** [dua tonu] [içten kapanış] [kapanış]

## VIDEO ŞABLONU (1-3 dakika)

[sakin açılış]
Hook cümlesi...

[besmele tonu]
Bismillahirrahmanirrahim...

[hamd tonu]
Elhamdülillahi Rabbil âlemin—

[salavat tonu]
Vessalâtü vesselâmü alâ Rasûlinâ Muhammedin ve alâ âlihi ve sahbihi ecmaîn...

[aktarım tonu]
[Râvi]... [alçak ses, salavat tonu] radıyallahu anh... [normal ses] rivayet edildiğine göre...

[konu geçişi]

[hadis tonu]
Rasûlullah... [haşyet] sallallahu aleyhi ve sellem... şöyle buyurdu:

—

[hadis metni - uygun direktiflerle]

[anlam yüklü sessizlik]

[kaynak tonu]
[Kaynak bilgisi]...

[samimi anlatım]
[Kısa yorum/açıklama]...

[içten kapanış]
[Kapanış mesajı]...

[dua tonu]
Rabbim... [dua]...

[kapanış]
Esselâmu aleyküm ve rahmetullah...

## SHORTS ŞABLONU (max 60 saniye)

[dikkat çekici]
HOOK!...

[hadis tonu, hızlı]
Peygamberimiz buyuruyor:—

[vurgulu]
HADİS METNİ...

[sonuç durağı]

[CTA]
TAKİP ET!...

═══════════════════════════════════════════════════════════════
                    ÖRNEK TAM AKIŞ
═══════════════════════════════════════════════════════════════

**Kullanıcı:** [hadis metni gönderir]

**Sen:**
📝 **AŞAMA 1/2: KELİME ANALİZİ**
[tablo ile öneriler]
⚡ Seçin: hepsini uygula | değiştirme

**Kullanıcı:** hepsini uygula

**Sen:**
✅ Değişiklikler uygulandı
🎙️ Format seçin: video | shorts | sadece hadis

**Kullanıcı:** video

**Sen:**
[sakin açılış]
[Doğrudan senaryo - açıklama olmadan]
...
[kapanış]
Esselâmu aleyküm ve rahmetullah...

═══════════════════════════════════════════════════════════════
                    ÖZEL KOMUTLAR
═══════════════════════════════════════════════════════════════

• "direkt seslendirme" → Kelime analizi atla
• "sadece analiz" → Seslendirme yapma
• "shorts yap" → Kısa format
• "tekrar" → Son işlemi tekrarla
"""


class HadithStudio:
    """Hadith Content Studio v3.0 - Ana Sınıf"""

    def __init__(self):
        self.client = client
        self.conversation_history = []
        self.original_hadith = ""
        self.current_analysis = ""

    def check_api_key(self):
        """API key kontrol et"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("\n❌ HATA: API key bulunamadı!")
            print("\n📝 Lütfen şunları yap:")
            print("1. https://console.anthropic.com/api-keys adresinden key al")
            print("2. .env dosyası oluştur ve şunu ekle:")
            print("   ANTHROPIC_API_KEY=sk-ant-v4-xxxxxxx...")
            print("3. Dosyayı kaydet ve programı yeniden başlat\n")
            return False
        return True

    def save_analysis(self, hadith_text, analysis_text):
        """Kelime analizini dosyaya kaydet"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = ANALYSES_DIR / f"analysis_{timestamp}.txt"

        with open(filename, "w", encoding="utf-8") as f:
            f.write("="*60 + "\n")
            f.write("HADITH CONTENT STUDIO v3.0\n")
            f.write("KELİME ANALİZİ\n")
            f.write("="*60 + "\n\n")
            f.write("ORIJINAL HADİS:\n")
            f.write("-"*60 + "\n")
            f.write(hadith_text + "\n\n")
            f.write("ANALİZ SONUCU:\n")
            f.write("-"*60 + "\n")
            f.write(analysis_text + "\n")

        return filename

    def save_script(self, script_text, format_type):
        """Seslendirme senaryosunu dosyaya kaydet"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = SCRIPTS_DIR / f"script_{format_type}_{timestamp}.txt"

        with open(filename, "w", encoding="utf-8") as f:
            f.write("="*60 + "\n")
            f.write("HADITH CONTENT STUDIO v3.0\n")
            f.write(f"SESLENDİRME SENARYOSU ({format_type.upper()})\n")
            f.write("="*60 + "\n\n")
            f.write(script_text + "\n")

        return filename

    def chat(self, user_message):
        """Claude ile sohbet et"""
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=self.conversation_history
        )

        assistant_message = response.content[0].text
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        return assistant_message

    def start_session(self):
        """Kullanıcı oturumu başlat"""
        print("\n" + "="*60)
        print("🕌 HADITH CONTENT STUDIO v3.0")
        print("İyilerin Yolu YouTube Kanalı")
        print("="*60)
        print("\n👋 Hoşgeldin! Hadis gir, sistemi çalıştıralım.\n")

        while True:
            print("\n" + "-"*60)
            print("💡 Ne yapmak istiyorsun?")
            print("-"*60)
            print("\n1. Hadis gir (yeni)")
            print("2. Özel komut gönder (direkt seslendirme, sadece analiz, vb)")
            print("3. Çık\n")

            choice = input("Seçim (1-3): ").strip()

            if choice == "1":
                self.process_hadith()
            elif choice == "2":
                self.send_command()
            elif choice == "3":
                print("\n👋 Hoşça kalın!\n")
                break
            else:
                print("❌ Hatalı seçim. Lütfen 1-3 arasında bir sayı gir.")

    def process_hadith(self):
        """Hadis işle - Tam akış"""
        print("\n" + "="*60)
        print("📝 HADİS GİRİŞİ")
        print("="*60)
        print("\nHadis metnini gir (Enter'den sonra Ctrl+D ile bitir):\n")

        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass

        hadith_text = "\n".join(lines).strip()

        if not hadith_text:
            print("\n❌ Hadis metni boş. Lütfen geçerli bir hadis gir.\n")
            return

        self.original_hadith = hadith_text
        self.conversation_history = []

        # Aşama 1: Kelime Analizi
        print("\n⏳ Kelime analizi yapılıyor...\n")
        analysis = self.chat(hadith_text)

        print(analysis)

        # Analizi dosyaya kaydet
        analysis_file = self.save_analysis(hadith_text, analysis)
        print(f"\n💾 Analiz kaydedildi: {analysis_file}\n")

        # Aşama 2: Kullanıcı seçimi
        self.handle_user_choice()

    def handle_user_choice(self):
        """Kullanıcı seçimini işle"""
        while True:
            print("\n" + "-"*60)
            choice = input("\n✏️  Seçiminizi yazın: ").strip().lower()

            if not choice:
                print("❌ Boş girdi. Lütfen bir seçim yap.")
                continue

            print(f"\n⏳ İşleniyor: '{choice}'...\n")
            response = self.chat(choice)

            print(response)

            # Senaryo talebi varsa dosyaya kaydet
            if "senaryo" in response.lower() or "[sakin açılış]" in response:
                if "video" in choice.lower():
                    script_file = self.save_script(response, "video")
                elif "shorts" in choice.lower():
                    script_file = self.save_script(response, "shorts")
                else:
                    script_file = self.save_script(response, "hadis")

                print(f"\n💾 Senaryo kaydedildi: {script_file}\n")
                break

            # "değiştirme" veya "koru" varsa çık
            if "korundu" in response.lower() or "orijinal" in response.lower():
                break

    def send_command(self):
        """Özel komut gönder"""
        print("\n" + "="*60)
        print("⚡ ÖZEL KOMUTLAR")
        print("="*60)
        print("\nÖrnekler:")
        print("• direkt seslendirme")
        print("• sadece analiz")
        print("• shorts yap")
        print("• tekrar\n")

        command = input("Komut gir: ").strip()

        if not command:
            print("❌ Boş komut.")
            return

        if not self.original_hadith:
            print("\n❌ HATA: Önce bir hadis gir!\n")
            return

        print(f"\n⏳ İşleniyor: '{command}'...\n")
        response = self.chat(command)

        print(response)

        # Senaryo varsa kaydet
        if "[sakin açılış]" in response:
            if "shorts" in command.lower():
                script_file = self.save_script(response, "shorts")
            else:
                script_file = self.save_script(response, "video")

            print(f"\n💾 Senaryo kaydedildi: {script_file}\n")


def main():
    """Ana giriş"""
    studio = HadithStudio()

    if not studio.check_api_key():
        return

    try:
        studio.start_session()
    except KeyboardInterrupt:
        print("\n\n👋 Hızlıkaldırıldı. Hoşça kalın!\n")


if __name__ == "__main__":
    main()
