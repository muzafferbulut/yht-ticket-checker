### YHT Ticket Checker

TCDD YHT bileti kontrol etmek için geliştirilmiş bir otomasyon uygulaması. Uygulama kullanıcının bilet alımı esnasında yaptığı standart adımları takip ederek bilet kontrolü yapıp seçilen saat ve tarihte uygun bilet olup olmadığını kontrol ediyor. Uygulama geliştirime safhasında selenium kütüphanesi kullanılmıştır.

Bu noktada dikkat edilmesi gereken seçili tarihte seçili sefer saatinin gerçekten var olmasıdır ve saat ve dakika olarak doğru girilmelidir. Bu noktada program içerisinde herhangi bir kontrol mekanizması bulunmamaktadır. Veri girişi alanında bulunan butonların yukarıdan aşağıya adı ve gerçekleştirdiği fonksiyon şu şekildedir:

<figure>
    <img src="files\img\app.png"
         alt="Ticket Checker">
</figure>

#### 1. Select Chrome Driver

Uygulama kontrol işlemleri için selenium kütüphanesi kullanılmıştır. Kütüphane çalışırken chromedriver kullanmaktadır. Bu buton yardımıyla programa kullanılacak olan chromedriver dosyasının yolu gösterilmektedir. Bir defa gösterilmesi yeterlidir, program aldığı bilgisi files/dependencies.json dosyasına yazar ve daha sonraki çalışmalarda bu dosyadan okur.

#### 2. Start Control

Kontrol edilecek sefer verileri girildikten sonra Start Control butonuna tıklanır. Bu butona tıklandıktan sonra program girilen kontrol aralığı kadar sürede aynı süreci işletir ve elde ettiği mesajı log ekranına yazar. Bu mesaj olumlu bir dönüt olabileceği gibi olumsuz bir dönüt ya da bir hata mesajı olabilir.

#### 3. Stop Control

Stop control butonu mevcutta çalışmakta olan bir süreci durdurmak için kullanılır.

#### 4. Clear Logs

Program uzun süre çalıştığında ya da hata mesajları ile log ekranı dolduğunda kullanılan butondur. Log ekranını temizler ve program çalışmaya devam eder.

#### 5. dependencies.json

files dizini altında bulunan bu dosya içerisinde bilet kontrol adımlarını işletirken tıklanan web site objelerinin seçicileri yer almaktadır. Daha sonra sitede meydana gelebilecek değişmeleri dinamik olarak yansıtabilmek amacıyla ayrı bir dosyada tutulmuştur.