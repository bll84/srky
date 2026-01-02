#!/usr/bin/env python3
"""
Hadith Content Studio v3.0 - Kişisel Kullanım CLI Aracı
Multi-API Support: Google Gemini, Claude, OpenAI
İyilerin Yolu YouTube Kanalı için Hadis Modernleştirme & Seslendirme Sistemi
"""

import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from abc import ABC, abstractmethod

# .env dosyasını yükle
load_dotenv()

# Klasör yapısını oluştur
OUTPUTS_DIR = Path("outputs")
ANALYSES_DIR = OUTPUTS_DIR / "analyses"
SCRIPTS_DIR = OUTPUTS_DIR / "scripts"

ANALYSES_DIR.mkdir(parents=True, exist_ok=True)
SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

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


# ═══════════════════════════════════════════════════════════════
# API ADAPTER SYSTEM
# ═══════════════════════════════════════════════════════════════

class APIAdapter(ABC):
    """Base class for API providers"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.conversation_history = []

    @abstractmethod
    def check_key(self) -> bool:
        """Check if API key is valid"""
        pass

    @abstractmethod
    def chat(self, message: str, system_prompt: str) -> str:
        """Send message and get response"""
        pass

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []


class GeminiAdapter(APIAdapter):
    """Google Gemini API Adapter"""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        try:
            import google.generativeai as genai
            self.genai = genai
            self.genai.configure(api_key=api_key)
            self.model = self.genai.GenerativeModel("gemini-1.5-pro")
        except ImportError:
            raise ImportError("google-generativeai kütüphanesi yüklü değil. Yüklemek için: pip install google-generativeai")

    def check_key(self) -> bool:
        """Check if API key works"""
        try:
            self.genai.configure(api_key=self.api_key)
            return True
        except Exception:
            return False

    def chat(self, message: str, system_prompt: str) -> str:
        """Send message to Gemini"""
        try:
            full_prompt = f"{system_prompt}\n\nKullanıcı: {message}"
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            raise Exception(f"Gemini API hatası: {str(e)}")


class ClaudeAdapter(APIAdapter):
    """Anthropic Claude API Adapter"""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=api_key)
        except ImportError:
            raise ImportError("anthropic kütüphanesi yüklü değil. Yüklemek için: pip install anthropic")

    def check_key(self) -> bool:
        """Check if API key works"""
        try:
            self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except Exception:
            return False

    def chat(self, message: str, system_prompt: str) -> str:
        """Send message to Claude"""
        try:
            self.conversation_history.append({
                "role": "user",
                "content": message
            })

            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                system=system_prompt,
                messages=self.conversation_history
            )

            assistant_message = response.content[0].text
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })

            return assistant_message
        except Exception as e:
            raise Exception(f"Claude API hatası: {str(e)}")


class OpenAIAdapter(APIAdapter):
    """OpenAI API Adapter"""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("openai kütüphanesi yüklü değil. Yüklemek için: pip install openai")

    def check_key(self) -> bool:
        """Check if API key works"""
        try:
            self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10
            )
            return True
        except Exception:
            return False

    def chat(self, message: str, system_prompt: str) -> str:
        """Send message to OpenAI"""
        try:
            self.conversation_history.append({
                "role": "user",
                "content": message
            })

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=2048,
                system=system_prompt,
                messages=self.conversation_history
            )

            assistant_message = response.choices[0].message.content
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })

            return assistant_message
        except Exception as e:
            raise Exception(f"OpenAI API hatası: {str(e)}")


# ═══════════════════════════════════════════════════════════════
# HADITH STUDIO MAIN CLASS
# ═══════════════════════════════════════════════════════════════

class HadithStudio:
    """Hadith Content Studio v3.0 - Ana Sınıf"""

    PROVIDERS = {
        "gemini": {
            "name": "Google Gemini",
            "adapter": GeminiAdapter,
            "key_env": "GOOGLE_API_KEY"
        },
        "claude": {
            "name": "Anthropic Claude",
            "adapter": ClaudeAdapter,
            "key_env": "ANTHROPIC_API_KEY"
        },
        "openai": {
            "name": "OpenAI GPT",
            "adapter": OpenAIAdapter,
            "key_env": "OPENAI_API_KEY"
        }
    }

    def __init__(self):
        self.api = None
        self.current_provider = None
        self.original_hadith = ""

    def select_api(self):
        """API sağlayıcısını seç"""
        print("\n" + "="*60)
        print("🔌 API SAĞLAYICISI SEÇ")
        print("="*60 + "\n")

        for i, (key, info) in enumerate(self.PROVIDERS.items(), 1):
            has_key = bool(os.getenv(info["key_env"]))
            status = "✅" if has_key else "❌"
            print(f"{i}. {status} {info['name']}")

        print(f"{len(self.PROVIDERS) + 1}. API key'i güncelle\n")

        choice = input("Seçim (1-4): ").strip()

        if choice == str(len(self.PROVIDERS) + 1):
            self.update_api_keys()
            return self.select_api()

        try:
            provider_list = list(self.PROVIDERS.keys())
            provider = provider_list[int(choice) - 1]
        except (IndexError, ValueError):
            print("❌ Hatalı seçim.")
            return self.select_api()

        api_key = os.getenv(self.PROVIDERS[provider]["key_env"])

        if not api_key:
            print(f"\n❌ {self.PROVIDERS[provider]['name']} key'i bulunamadı!")
            print(f"   .env dosyasını kontrol et.\n")
            return self.select_api()

        try:
            self.api = self.PROVIDERS[provider]["adapter"](api_key)
            self.current_provider = provider
            print(f"\n✅ {self.PROVIDERS[provider]['name']} seçildi!\n")
            return True
        except ImportError as e:
            print(f"\n❌ Hata: {str(e)}\n")
            return self.select_api()

    def update_api_keys(self):
        """API key'lerini güncelle"""
        print("\n" + "="*60)
        print("🔑 API KEY'LERİ GÜNCELLE")
        print("="*60 + "\n")

        env_file = Path(".env")
        content = ""

        if env_file.exists():
            with open(env_file, "r", encoding="utf-8") as f:
                content = f.read()

        for provider, info in self.PROVIDERS.items():
            key_var = info["key_env"]
            print(f"\n{info['name']} API key'i gir")
            print(f"(Boş bırak ve Enter'a bas =  değiştirme)")
            key = input(f"{key_var}: ").strip()

            if key:
                # Env dosyasında var mı kontrol et
                if f"{key_var}=" in content:
                    # Güncelle
                    lines = content.split("\n")
                    content = "\n".join(
                        [f"{key_var}={key}" if line.startswith(key_var) else line for line in lines]
                    )
                else:
                    # Ekle
                    content += f"\n{key_var}={key}"

        # Dosyaya kaydet
        env_file.write_text(content, encoding="utf-8")
        print("\n✅ .env dosyası güncellendi!\n")

    def save_analysis(self, hadith_text: str, analysis_text: str) -> Path:
        """Kelime analizini dosyaya kaydet"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = ANALYSES_DIR / f"analysis_{timestamp}.txt"

        with open(filename, "w", encoding="utf-8") as f:
            f.write("="*60 + "\n")
            f.write("HADITH CONTENT STUDIO v3.0\n")
            f.write(f"KELİME ANALİZİ ({self.PROVIDERS[self.current_provider]['name']})\n")
            f.write("="*60 + "\n\n")
            f.write("ORIJINAL HADİS:\n")
            f.write("-"*60 + "\n")
            f.write(hadith_text + "\n\n")
            f.write("ANALİZ SONUCU:\n")
            f.write("-"*60 + "\n")
            f.write(analysis_text + "\n")

        return filename

    def save_script(self, script_text: str, format_type: str) -> Path:
        """Seslendirme senaryosunu dosyaya kaydet"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = SCRIPTS_DIR / f"script_{format_type}_{timestamp}.txt"

        with open(filename, "w", encoding="utf-8") as f:
            f.write("="*60 + "\n")
            f.write("HADITH CONTENT STUDIO v3.0\n")
            f.write(f"SESLENDİRME SENARYOSU ({format_type.upper()})\n")
            f.write(f"API: {self.PROVIDERS[self.current_provider]['name']}\n")
            f.write("="*60 + "\n\n")
            f.write(script_text + "\n")

        return filename

    def start_session(self):
        """Kullanıcı oturumu başlat"""
        print("\n" + "="*60)
        print("🕌 HADITH CONTENT STUDIO v3.0")
        print("Multi-API Support")
        print("="*60)
        print("\n👋 Hoşgeldin! Hadis gir, sistemi çalıştıralım.\n")

        while True:
            print("\n" + "-"*60)
            print("💡 Ne yapmak istiyorsun?")
            print("-"*60)
            print("\n1. Hadis gir (yeni)")
            print("2. Özel komut gönder")
            print("3. API sağlayıcısını değiştir")
            print("4. Çık\n")

            choice = input("Seçim (1-4): ").strip()

            if choice == "1":
                self.process_hadith()
            elif choice == "2":
                self.send_command()
            elif choice == "3":
                self.select_api()
            elif choice == "4":
                print("\n👋 Hoşça kalın!\n")
                break
            else:
                print("❌ Hatalı seçim.")

    def process_hadith(self):
        """Hadis işle"""
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
            print("\n❌ Hadis metni boş.\n")
            return

        self.original_hadith = hadith_text
        self.api.clear_history()

        print("\n⏳ Kelime analizi yapılıyor...\n")
        analysis = self.api.chat(hadith_text, SYSTEM_PROMPT)

        print(analysis)

        analysis_file = self.save_analysis(hadith_text, analysis)
        print(f"\n💾 Analiz kaydedildi: {analysis_file}\n")

        self.handle_user_choice()

    def handle_user_choice(self):
        """Kullanıcı seçimini işle"""
        while True:
            choice = input("\n✏️  Seçiminizi yazın: ").strip().lower()

            if not choice:
                print("❌ Boş girdi.")
                continue

            print(f"\n⏳ İşleniyor...\n")
            response = self.api.chat(choice, SYSTEM_PROMPT)

            print(response)

            if "[sakin açılış]" in response:
                if "video" in choice:
                    script_file = self.save_script(response, "video")
                elif "shorts" in choice:
                    script_file = self.save_script(response, "shorts")
                else:
                    script_file = self.save_script(response, "hadis")

                print(f"\n💾 Senaryo kaydedildi: {script_file}\n")
                break

            if "korundu" in response.lower():
                break

    def send_command(self):
        """Özel komut gönder"""
        print("\n" + "="*60)
        print("⚡ ÖZEL KOMUTLAR")
        print("="*60 + "\n")

        command = input("Komut gir: ").strip()

        if not command or not self.original_hadith:
            print("❌ Hata: Önce bir hadis gir!\n")
            return

        print(f"\n⏳ İşleniyor...\n")
        response = self.api.chat(command, SYSTEM_PROMPT)

        print(response)

        if "[sakin açılış]" in response:
            if "shorts" in command.lower():
                script_file = self.save_script(response, "shorts")
            else:
                script_file = self.save_script(response, "video")

            print(f"\n💾 Senaryo kaydedildi: {script_file}\n")


def main():
    """Ana giriş"""
    studio = HadithStudio()

    if not studio.select_api():
        return

    try:
        studio.start_session()
    except KeyboardInterrupt:
        print("\n\n👋 Çıkılıyor...\n")


if __name__ == "__main__":
    main()
