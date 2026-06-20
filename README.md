Güneş Enerji Sistemlerinde Büyük Veri ve Yapay Zekâ Tabanlı Üretim Tahmini, Anomali Tespiti ve Akıllı Enerji Yönetimi

Bu repository, “Güneş Enerji Sistemlerinde Büyük Veri ve Yapay Zekâ Tabanlı Üretim Tahmini, Anomali Tespiti ve Akıllı Enerji Yönetimi” başlıklı tez/proje çalışmasına ait kodları, görsel çıktıları ve proje dokümanlarını içermektedir.

Çalışma; güneş enerji santrallerinde üretim tahmini, anomali tespiti, büyük veri analizi, IoT tabanlı veri toplama, Kafka tabanlı veri akışı, dashboard izleme ve enerji yönetimi karar desteği süreçlerini bir araya getiren bütünleşik bir sistem yaklaşımı sunmaktadır.

Tez Dosyası

Tezin Word dosyasına aşağıdaki bağlantıdan ulaşabilirsiniz:

GES TEZ MELİH TÜRK.docx dosyasını indir

Projenin Amacı

Bu projenin temel amacı, güneş enerji santrallerinde yalnızca gerçekleşen üretim değerlerini izlemek yerine, mevcut çevresel koşullara göre beklenen üretim değerini tahmin etmek ve beklenen üretim ile gerçekleşen üretim arasındaki sapmaları belirlemektir.

Bu yaklaşım sayesinde:

Güneş enerji santrallerinde üretim performansı analiz edilebilir.
Beklenen üretimden sapmalar erken fark edilebilir.
Anomali görülen zamanlar ve kaynaklar belirlenebilir.
Bakım ve saha incelemesi süreçleri veriye dayalı şekilde desteklenebilir.
Üretim, tüketim, akü ve şebeke kararları birlikte değerlendirilebilir.
Kullanılan Teknolojiler

Projede kullanılan başlıca teknolojiler şunlardır:

Python
Pandas
NumPy
Matplotlib
Scikit-learn
Random Forest Regressor
Apache Spark
Spark SQL
Kafka
ESP32
Arduino IDE
JupyterLab
HTML Dashboard
Kullanılan Veri Setleri

Bu projede kullanılan büyük veri setleri GitHub repository içine eklenmemiştir. Bunun nedeni, veri setlerinin ve model çıktı dosyalarının GitHub dosya boyutu sınırlarını aşabilmesidir.

Projede kullanılan veri kaynakları:

Kaggle Solar Power Generation Data
Güneş enerji santrallerine ait üretim ve hava/sensör verileri kullanılmıştır.
UCI Individual Household Electric Power Consumption
Enerji yönetimi modülünde gerçek tüketim profili olarak kullanılmıştır.
Proje Klasör Yapısı

Repository yapısı genel olarak aşağıdaki gibidir:

GES-TEZ/
│
├── README.md
├── requirements.txt
├── .gitignore
├── .gitattributes
│
├── src/
│   ├── pipeline/
│   ├── iot_esp32/
│   ├── kafka_streaming/
│   ├── dashboard/
│   ├── modeling/
│   ├── spark_analysis/
│   └── energy_management/
│
├── figures/
│   ├── plant_model_r2_comparison.png
│   ├── plant_anomaly_rate_comparison.png
│   ├── plant_1_anomaly_by_source.png
│   ├── plant_2_anomaly_by_source.png
│   ├── plant_1_actual_vs_expected.png
│   ├── plant_2_actual_vs_expected.png
│   ├── real_consumption_decision_distribution.png
│   └── real_consumption_battery_soc_simulation.png
│
├── docs/
│   ├── GES TEZ MELİH TÜRK.docx
│   └── github_hazirlik/
│
└── sample_data/
Ana Kod Dosyaları

Ana Python pipeline kodları src/pipeline/ klasörü altında yer almaktadır.

Dosya	Açıklama
01_prepare_data.py	Güneş enerji veri setlerinin hazırlanması ve birleştirilmesi
02_train_models.py	Plant 1 ve Plant 2 için üretim tahmini modellerinin eğitilmesi
03_detect_anomalies.py	Beklenen ve gerçekleşen üretim farkına göre anomali tespiti
04_generate_charts.py	Model, anomali ve karşılaştırma grafiklerinin oluşturulması
05_generate_reports.py	Temel çıktı raporlarının hazırlanması
06_spark_analysis.py	Spark ile anomali ve üretim çıktılarının analiz edilmesi
07_spark_sql_hive_like.py	Spark SQL ile Hive benzeri sorgulama yapılması
08_create_hadoop_data_lake.py	Yerel veri gölü klasör yapısının oluşturulması
10_energy_management_ai.py	Enerji yönetimi karar destek modelinin oluşturulması
11_update_extended_reports.py	Genişletilmiş rapor çıktılarının güncellenmesi
12_download_uci_consumption.py	UCI tüketim veri setinin indirilmesi
13_prepare_consumption_data.py	Tüketim verisinin hazırlanması
14_energy_management_real_consumption.py	Gerçek tüketim profiliyle enerji yönetimi simülasyonu
15_update_real_consumption_reports.py	Gerçek tüketim destekli raporların güncellenmesi
run_all.py	Temel pipeline dosyalarını sırayla çalıştırmak
run_all_extended.py	Genişletilmiş süreci çalıştırmak
run_all_real_consumption_extended.py	Gerçek tüketim destekli genişletilmiş süreci çalıştırmak
IoT ve ESP32 Kodları

ESP32 tarafındaki kodlar src/iot_esp32/ klasöründe yer almaktadır.

Klasör / Dosya	Açıklama
esp_ortam_dht22_bh1750/	DHT22 ve BH1750 sensörleriyle sıcaklık, nem ve ışık şiddeti verilerini toplar
esp_panel_acs712/	ACS712 sensörüyle panel akım verisini okumak için kullanılır
README_hardware.md	Donanım tarafına ait kısa açıklamaları içerir

Bu katman, sahadan veri toplanabileceğini göstermek için hazırlanmış IoT prototipini temsil etmektedir.

Kafka ve Veri Aktarım Kodları

Kafka ve veri aktarım kodları src/kafka_streaming/ klasöründe yer almaktadır.

Dosya	Açıklama
pc_csv_stream_uploader.py	ESP32/PC tarafında oluşan verileri dosya ve aktarım sürecine hazırlar
upload_csv_to_jupyter.py	CSV/JSONL verilerinin JupyterHub ortamına gönderilmesini sağlar
README_iot_terminal.md	IoT terminal veri aktarım sürecine ait kısa açıklamaları içerir

Projede kullanılan Kafka topicleri:

team.ges.v2.raw.env
team.ges.v2.raw.panel
team.ges.v2.raw.combined
Model Performans Sonuçları

Çalışmada Plant 1 ve Plant 2 için ayrı Random Forest regresyon modelleri oluşturulmuştur.

Santral	Model	R²	MAE
Plant 1	Random Forest Regressor	0,9681	30,5077
Plant 2	Random Forest Regressor	0,8273	72,73

Model başarı karşılaştırması:




Anomali Tespiti Sonuçları

Anomali tespiti, model tarafından tahmin edilen beklenen AC güç değeri ile gerçekleşen AC güç değeri arasındaki fark üzerinden yapılmıştır.

Santral	Modelleme kayıt sayısı	Anomali sayısı	Anomali oranı
Plant 1	38.376	141	%0,37
Plant 2	38.722	383	%0,99
Toplam	77.098	524	-

Anomali oranı karşılaştırması:




Kaynak Bazlı Anomali Analizi

Plant 1 ve Plant 2 için en çok anomali görülen kaynaklar ayrı ayrı incelenmiştir. Bu analiz, üretim sapmalarının belirli inverter/kaynak gruplarında yoğunlaşıp yoğunlaşmadığını anlamaya yardımcı olur.

Plant 1 Kaynak Bazlı Anomali Dağılımı




Plant 2 Kaynak Bazlı Anomali Dağılımı




Beklenen ve Gerçekleşen AC Güç Karşılaştırması

Modelin beklediği AC güç değeri ile gerçek AC güç değeri karşılaştırılarak üretim sapmaları görsel olarak incelenmiştir.

Plant 1 Beklenen ve Gerçekleşen AC Güç




Plant 2 Beklenen ve Gerçekleşen AC Güç




Enerji Yönetimi Simülasyonu

Enerji yönetimi aşamasında gerçek tüketim profiliyle desteklenen hibrit bir karar destek simülasyonu geliştirilmiştir. Bu bölümde üretim, tüketim, akü ve şebeke kararları birlikte değerlendirilmiştir.

Karar sınıfları:

Karar sınıfı	Kayıt sayısı
AKUDEN_KULLAN	56.597
SEBEKEYE_SATISA_UYGUN	28.735
SEBEKEDEN_DESTEK_AL	26.821
AKUYU_SARJ_ET	23.473
TUKETIME_VER	1.013

Enerji yönetimi karar dağılımı:




Akü doluluk oranı simülasyonu:




Çalışmanın Genel İş Akışı

Projenin genel iş akışı şu şekildedir:

Güneş enerji üretim ve hava/sensör verilerinin hazırlanması
Plant 1 ve Plant 2 verilerinin ayrı ayrı modellenmesi
Random Forest ile beklenen AC güç tahmini yapılması
Beklenen ve gerçekleşen üretim farkı üzerinden anomali tespiti
Anomali sonuçlarının kaynak ve zaman bazında analiz edilmesi
Spark ve Spark SQL ile büyük veri mantığında sorgulama yapılması
ESP32 prototipiyle sensör verisi toplama altyapısının hazırlanması
Kafka topicleri ve dashboard ile canlıya yakın izleme yapısının test edilmesi
Gerçek tüketim profiliyle enerji yönetimi karar destek simülasyonunun oluşturulması
Kurulum

Projeyi çalıştırmak için gerekli Python kütüphaneleri requirements.txt dosyasında verilmiştir.

pip install -r requirements.txt
Çalıştırma

Ana pipeline dosyaları src/pipeline/ klasörü altında yer almaktadır.

Temel süreci çalıştırmak için:

python src/pipeline/run_all.py

Gerçek tüketim destekli genişletilmiş enerji yönetimi süreci için:

python src/pipeline/run_all_real_consumption_extended.py

Not: Büyük veri setleri repository içine eklenmediği için kodların çalıştırılabilmesi için veri setlerinin ayrıca indirilmesi ve proje klasör yapısına uygun şekilde yerleştirilmesi gerekir.

Repository İçine Eklenmeyen Dosyalar

Aşağıdaki dosyalar bilinçli olarak repository içine eklenmemiştir:

solar_data/
consumption_data/
final_outputs/
hadoop_data_lake/
spark_outputs/
*.csv
*.jsonl
*.pkl
*.joblib
*.zip

Bu dosyalar büyük veri, model çıktısı veya ara çıktı dosyaları olduğu için GitHub dosya boyutu sınırlarını aşabilir.

Çalışmanın Sınırlılıkları

Bu çalışma bir prototip ve karar destek yaklaşımıdır. Ana modelleme süreci açık veri setleri üzerinden yürütülmüştür. ESP32’den alınan sensör verileri ana modelin eğitim verisi olarak kullanılmamış, gerçek zamanlıya yakın veri toplama ve izleme altyapısının uygulanabilirliğini göstermek amacıyla kullanılmıştır.

Enerji yönetimi bölümü ise gerçek bir GES tesisine ait tüketim verisiyle değil, UCI veri setinden alınan gerçek tüketim profiliyle desteklenen hibrit bir simülasyon olarak değerlendirilmelidir.

Geliştirme Önerileri

Gelecekte bu çalışma şu yönlerden geliştirilebilir:

Gerçek bir güneş enerji santralinden uzun dönemli veri toplanabilir.
ESP32 yerine endüstriyel sensör ve inverter logları kullanılabilir.
Kafka ve Spark Streaming ile gerçek zamanlı anomali tespiti yapılabilir.
Bakım kayıtları modele dahil edilerek anomali nedenleri sınıflandırılabilir.
Akü kapasitesi, elektrik fiyatları ve şebeke kısıtlarıyla daha gelişmiş enerji optimizasyonu yapılabilir.
Dashboard yapısı web tabanlı ve kullanıcı girişli bir sisteme dönüştürülebilir.
Yazar

Melih Türk
Bursa Uludağ Üniversitesi
İnegöl İşletme Fakültesi
Yönetim Bilişim Sistemleri Bölümü

Danışman

Prof. Dr. Melih Engin

Not

Bu repository, tez çalışmasının kod, görsel ve açıklama dosyalarını paylaşmak amacıyla hazırlanmıştır. Büyük veri setleri ve model dosyaları repository içine eklenmemiştir. Tez dosyası docs/ klasörü altında sunulmuştur.
