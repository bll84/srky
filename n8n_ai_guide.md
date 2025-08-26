# Yapay Zeka Desteği ile n8n'de Uzmanlaşma Rehberi

Bu rehber, sizi hiç tecrübesi olmayan bir kullanıcı seviyesinden, yapay zeka (AI) asistanlarını bir yardımcı olarak kullanarak n8n'de karmaşık otomasyonlar kurabilen bir uzman seviyesine taşımak için tasarlanmıştır.

---

## Aşama 1: Temel Kavramlar (Başlangıç Seviyesi)

Bu aşamada, hem yapay zeka ile nasıl etkili iletişim kuracağınızı hem de n8n'in temel mantığını kavrayacaksınız.

### Adım 1.1: Çekirdek Konseptleri Anlama

#### Yapay Zeka İçin Etkili Komut (Prompt) Yazma Sanatı

Bir yapay zeka asistanından alacağınız sonucun kalitesi, ona verdiğiniz komutun kalitesine doğrudan bağlıdır. İşte 4 temel kural:

1.  **Rol ve Hedef Belirleyin (Persona):** Asistanın kim olmasını istediğinizi söyleyin.
    *   *Örnek:* "Sen deneyimli bir otomasyon uzmanısın. Amacım, yeni müşterilerim için bir karşılama sürecini otomatikleştirmek."

2.  **Bağlam Sunun (Context):** Görevle ilgili tüm arka plan bilgisini verin.
    *   *Örnek:* "n8n'deki bir 'Function' nodu için JavaScript kodu yazıyorum. Giriş olarak bir müşterinin adını ve e-postasını içeren bir JSON nesnesi alıyorum."

3.  **Adım Adım Talimat Verin (Step-by-step):** Karmaşık bir istek için, asistanın izlemesi gereken adımları listeleyin.
    *   *Örnek:* "n8n iş akışımda bir hatayı ayıklamaya çalışıyorum. 1. Hata mesajını analiz et. 2. Nodun yapılandırmasını incele. 3. Olası nedeni ve çözümü açıkla."

4.  **Çıktı Formatını Belirleyin (Output Format):** Cevabı nasıl bir formatta istediğinizi belirtin.
    *   *Örnek:* "Bana 5 otomasyon fikrini bir tablo formatında, 'Fikir Adı', 'Kullanılacak Nodlar' ve 'Zorluk' sütunlarıyla listele."

#### n8n'in Temelleri: 4 Ana Kavram

1.  **Workflow (İş Akışı):** Tüm otomasyonunuzun kendisidir. Birbirine bağlı adımlar (nodlar) dizisidir.
2.  **Node (Düğüm):** İş akışınızdaki her bir adımdır. Belirli bir işlevi yerine getirir (örn: e-posta gönder, veriyi filtrele).
3.  **Connection (Bağlantı):** Nodları birbirine bağlayan çizgilerdir. Verinin bir noddan diğerine akışını belirler.
4.  **Credential (Kimlik Bilgisi):** n8n'in harici servislere (Google, Twitter vb.) sizin adınıza bağlanması için gereken API anahtarları gibi güvenli bilgilerdir.

### Adım 1.2: Yapay Zeka Yardımıyla İlk İş Akışınız

**Hedef:** Her sabah belirli bir saatte, İstanbul'un hava durumu bilgisini alıp, Discord'daki bir kanalımıza mesaj olarak göndermek.

**Yapay Zekaya Sorulacak Komut:**
> "Sen deneyimli bir n8n otomasyon uzmanısın. Amacım, her sabah İstanbul için hava durumu bilgisini alıp Discord'daki 'raporlar' kanalıma göndermek. Bu iş akışı için hangi n8n nodlarını kullanmam gerektiğini ve adımların ne olduğunu açıkla."

**Uygulama Adımları:**
1.  **Schedule Nodu:** İş akışını her gün belirli bir saatte (örn: 08:00) tetiklemek için kullanılır.
2.  **Open-Meteo Nodu:** `Location` olarak 'Istanbul' girilerek anlık hava durumu verisini çeker. API anahtarı gerektirmediği için başlangıç için idealdir.
3.  **Discord Nodu:** `Content` alanına `Bugün İstanbul'da hava sıcaklığı {{$json["temperature"]}} derece.` gibi bir ifade yazılarak önceki noddan gelen veriyi mesaja ekler. Bu nod için Discord'dan bir Webhook URL alıp `Credential` olarak eklemeniz gerekir.

Bu üç nodu birbirine bağlayıp iş akışını `Activate` ettiğinizde, ilk otomasyonunuz hazır!

---

## Aşama 2: Karmaşıklığı Artırma (Orta Seviye)

Bu aşamada iş akışlarımızı daha dinamik ve akıllı hale getireceğiz.

### Adım 2.1: Veri Manipülasyonu (JSON ve `Set` Nodu)

n8n'de veri, nodlar arasında JSON formatında akar. Farklı sistemler farklı JSON yapıları beklediği için veriyi dönüştürmek kritik bir yetenektir.

**Senaryo:** Bir e-ticaret sitesinden gelen sipariş verisini Google Sheets'e kaydetmek.

Gelen Veri (Karmaşık):
```json
{ "customer_details": { "firstName": "Ahmet", "lastName": "Yılmaz" }, "total_price": 170 }
```
İstenen Format (Basit): `customerName` ve `orderTotal` sütunları.

**Çözüm:** Araya bir `Set` nodu eklenir. `Set` nodu, yeni veri alanları oluşturmanızı sağlar.

**Yapay Zekaya Sorulacak Komut:**
> "Sen bir n8n uzmanısın. Yukarıdaki JSON verisini alıyorum. Müşterinin adını ve soyadını birleştiren 'customerName' ve 'total_price'ı alan 'orderTotal' için n8n ifadelerini (expressions) yazar mısın?"

**Yapay Zeka Cevabı:**
*   `customerName` için: `{{$json.customer_details.firstName}} {{$json.customer_details.lastName}}`
*   `orderTotal` için: `{{$json.total_price}}`

Bu ifadeler `Set` noduna girildiğinde, veri istediğiniz formata dönüşür.

### Adım 2.2: Mantık ve Koşulların Eklenmesi (`IF` Nodu)

İş akışlarınıza karar verme yeteneği eklemek için `IF` nodu kullanılır. Akış, belirlenen koşula göre farklı yollara ayrılır.

**Senaryo:** Gelen sipariş tutarı 1000 TL'den büyükse yöneticiye e-posta gönder, değilse sadece Google Sheets'e kaydet.

**Yapay Zekaya Sorulacak Komut:**
> "n8n'de bir `IF` nodu kullanıyorum. Bir önceki adımdan gelen veride `orderTotal` adında bir sayı var. Bu sayının 1000'den büyük olup olmadığını kontrol etmek için `IF` noduna girmem gereken koşul nedir?"

**Yapay Zeka Cevabı:**
*   `Value 1`: `{{$json.orderTotal}}`
*   `Operation`: `Larger Than`
*   `Value 2`: `1000`

Bu ayar yapıldığında, `IF` nodunun iki çıkışı olur: `true` (koşul doğruysa) ve `false` (yanlışsa). `true` çıkışına `Send Email` nodunu, `false` çıkışına `Google Sheets` nodunu bağlayarak senaryoyu tamamlayabilirsiniz.

### Adım 2.3: Yapay Zeka ile Özel Kod Yazma (`Function` Nodu)

Standart nodların yetmediği durumlarda, JavaScript kodu yazmanızı sağlayan `Function` nodu devreye girer.

**Senaryo:** Gelen veride müşterinin tam adı "Ahmet Yılmaz" olarak tek bir alanda geliyor. Ama size sadece ilk adı ("Ahmet") lazım.

**Yapay Zekaya Sorulacak Komut:**
> "Sen bir JavaScript uzmanısın. n8n'deki bir `Function` nodu için kod yazıyorum. Girdi olarak `{\"fullName\": \"Ahmet Yılmaz\"}` şeklinde bir JSON geliyor. Bu `fullName` alanındaki ilk kelimeyi (boşluğa kadar olan kısmı) alıp, çıktı olarak `{\"firstName\": \"Ahmet\"}` şeklinde döndüren bir JavaScript kodu yazar mısın?"

**Yapay Zeka Cevabı:**
```javascript
const fullName = $json.fullName;
const firstName = fullName.split(' ')[0];
return { firstName: firstName };
```
Bu kodu `Function` noduna yapıştırdığınızda, istediğiniz özel veri işleme görevini yerine getirir.

---

## Aşama 3: İleri Teknikler ve Ustalık

### Adım 3.1: Yapay Zeka Destekli Hata Ayıklama (Debugging)

Her uzman hata yapar. Önemli olan, hatayı hızla bulup çözmektir.

**Hata Ayıklama Süreci:**
1.  **Hatanın Yerini Bul:** n8n arayüzünde kırmızı ile işaretlenmiş, hata veren nodu bulun.
2.  **Bilgileri Topla:**
    *   Hata veren nodun **Girdi (Input)** verisini kopyalayın.
    *   Nodun **Ayarlarını (Parameters)** ekran görüntüsü alın veya not edin.
    *   **Hata Mesajının (Error Message)** tamamını kopyalayın.
3.  **Yapay Zekaya Sor:**

**Yapay Zekaya Sorulacak Komut:**
> "Sen bir n8n hata ayıklama uzmanısın. Bir iş akışımda hata alıyorum.
> *   **Hata Veren Nod:** `Google Sheets`
> *   **Hata Mesajı:** `[Buraya hata mesajını yapıştırın]`
> *   **Nodun Girdi Verisi:** `[Buraya input JSON'ını yapıştırın]`
> *   **Nodun Ayarları:** `[Buraya ayarları açıklayın, örn: 'Spreadsheet ID' doğru, 'Sheet Name' doğru, 'Name' sütununa {{ $json.customerName }} yazmaya çalışıyorum]`
>
> Bu bilgilere göre hatanın sebebi ne olabilir ve nasıl çözebilirim?"

Bu yapısal yaklaşım, yapay zekanın size en doğru ve hızlı çözümü sunmasını sağlar.

### Adım 3.2: İş Akışı Fikri Geliştirme ve Tasarımı

Yapay zeka, sadece sorun çözmek için değil, aynı zamanda yaratıcı bir ortak olarak da kullanılabilir.

**Fikir Üretme Komutu:**
> "Ben bir dijital pazarlama uzmanıyım. Günlük görevlerimi otomatikleştirmek için bana 5 farklı n8n iş akışı fikri ver. Fikirleri bir tablo olarak sun."

**Tasarım Yaptırma Komutu:**
> "Yukarıdaki '[Fikir Adı]' fikrini hayata geçirmek istiyorum. Bu iş akışı için üst düzey bir plan oluştur. Hangi n8n nodlarını kullanmam gerektiğini ve aralarındaki mantıksal akışın nasıl olması gerektiğini adım adım listele."

### Adım 3.3: Özel HTTP API Çağrıları Oluşturma (`HTTP Request` Nodu)

Her servisin kendine özel bir n8n nodu yoktur. `HTTP Request` nodu, herhangi bir API'ye bağlanmanızı sağlayan evrensel bir araçtır.

**Senaryo:** Özel bir CRM sistemine yeni bir müşteri eklemek istiyorsunuz ve bu CRM'in bir API dokümantasyonu var.

**Yapay Zekaya Sorulacak Komut:**
> "Sen bir API entegrasyon uzmanısın. Bir servisin API dokümanından bir bölümü aşağıya yapıştırıyorum:
> `[Buraya API dokümanının ilgili bölümünü (örn: 'Create a new contact') yapıştırın]`
>
> Bu işlemi n8n'deki `HTTP Request` nodu ile yapmak için bilmem gerekenler:
> *   **HTTP Metodu** (GET, POST, vb.) nedir?
> *   **URL** ne olmalı?
> *   **Request Body** (gönderilecek JSON) nasıl görünmeli?"

Yapay zeka, teknik dokümanı sizin için "tercüme ederek" `HTTP Request` nodunu nasıl dolduracağınızı söyler.

---

## Aşama 4: Bilgiyi Pekiştirme ve Sonuç

### Adım 4.1: Öğrenilenlerin Özeti

Bu rehber boyunca sıfırdan başlayarak bir yolculuk yaptınız:
*   **Temelleri** öğrendiniz ve yapay zeka ile nasıl konuşacağınızı keşfettiniz.
*   **Veriyi işlemeyi**, gelen bilgiyi istediğiniz formata dönüştürmeyi öğrendiniz.
*   İş akışlarınıza **mantık ve karar verme** yeteneği eklediniz.
*   Standartların dışına çıkarak **özel kodlarla** kendi çözümlerinizi ürettiniz.
*   Bir uzman gibi **hata ayıklamayı**, yeni **fikirler üretmeyi** ve evrensel **API'lere bağlanmayı** öğrendiniz.

### Sonuç

Artık n8n ve yapay zeka asistanlarını birer araç olarak değil, iş akışlarınızı otomatikleştirmek ve üretkenliğinizi artırmak için birer **ortak** olarak nasıl kullanacağınızı biliyorsunuz. Ustalık, bu teknikleri kendi görevlerinize yaratıcı bir şekilde uygulamaktan geçer. Başarılar!
