from pathlib import Path
import json
import shutil
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]

FINAL_DIR = PROJECT_DIR / "final_outputs"
ENERGY_DIR = PROJECT_DIR / "energy_management"
LAKE_DIR = PROJECT_DIR / "hadoop_data_lake"

FINAL_DIR.mkdir(parents=True, exist_ok=True)

energy_results_file = ENERGY_DIR / "energy_management_results.json"
energy_training_file = ENERGY_DIR / "energy_management_training_data.csv"

if not energy_results_file.exists():
    raise FileNotFoundError(f"Enerji yonetimi sonuc dosyasi bulunamadi: {energy_results_file}")

if not energy_training_file.exists():
    raise FileNotFoundError(f"Enerji yonetimi egitim verisi bulunamadi: {energy_training_file}")

energy_data = pd.read_csv(energy_training_file)

with energy_results_file.open("r", encoding="utf-8") as f:
    energy_results = json.load(f)

# Hadoop veri gölüne enerji yönetimi katmanını ekle/güncelle
lake_energy = LAKE_DIR / "energy_management"
lake_energy.mkdir(parents=True, exist_ok=True)

for file in ENERGY_DIR.iterdir():
    if file.is_file():
        shutil.copy2(file, lake_energy / file.name)

extended_summary = FINAL_DIR / "extended_project_summary.txt"

text = f"""GENISLETILMIS GES AI PROJE OZETI
================================

Bu proje, güneş enerji santrali üretim tahmini, anomali tespiti ve akıllı enerji yönetimi üzerine geliştirilmiştir. İlk aşamada Plant 1 ve Plant 2 üretim/hava sensörü verileri kullanılarak AC güç tahmini ve anomali tespiti yapılmıştır. Daha sonra proje, akü depolama ve şebekeye satışa uygunluk kararı veren AI tabanlı karar destek modülü ile genişletilmiştir.

1. Ana Veri Seti
----------------
Ana modelleme aşamasında açık kaynaklı GES üretim veri seti kullanılmıştır. Bu veri setinde Plant 1 ve Plant 2 santrallerine ait üretim verileri ve santral seviyesinde hava sensörü verileri bulunmaktadır.

Modelleme ve enerji yönetimi aşamalarında veri setinin kendi hava sensörü ölçümleri kullanılmıştır:
- IRRADIATION
- AMBIENT_TEMPERATURE
- MODULE_TEMPERATURE

Dış konumdan alınan meteoroloji verileri aktif modele dahil edilmemiştir. Çünkü santral koordinatları net bilinmeden dış meteoroloji verisini üretim verisiyle birleştirmek metodolojik olarak doğru değildir.

2. Üretim Tahmini ve Anomali Tespiti
------------------------------------
Plant 1 ve Plant 2 verileri kullanılarak AC_POWER tahmini yapan yapay zekâ modelleri geliştirilmiştir. Modelin beklediği üretim ile gerçek üretim arasındaki fark hesaplanmış ve belirli eşik değerlerin üzerindeki düşük üretim durumları anomali olarak işaretlenmiştir.

3. Spark, Spark SQL ve Hadoop Veri Gölü
---------------------------------------
Anomali sonuçları Apache Spark ile analiz edilmiş, Spark SQL ile Hive benzeri geçici tablolar üzerinden sorgulanmış ve sonuçlar Hadoop/HDFS mantığını temsil eden hadoop_data_lake klasör yapısında saklanmıştır.

4. Akıllı Enerji Yönetimi Modülü
--------------------------------
Plant 1 üretim ve hava sensörü verileri kullanılarak akü depolama, tüketim ve şebekeye satışa uygunluk kararlarını değerlendiren simülasyon tabanlı AI karar destek modülü geliştirilmiştir.

Bu modül şu verilere dayanır:
- Plant 1 üretim profili
- Plant 1 IRRADIATION değeri
- Plant 1 AMBIENT_TEMPERATURE değeri
- Plant 1 MODULE_TEMPERATURE değeri
- Simüle edilmiş tüketim verisi
- Simüle edilmiş akü doluluk oranı

Enerji yönetimi kayıt sayısı:
{energy_results["record_count"]}

AI karar modeli doğruluk oranı:
{energy_results["accuracy"]:.4f}

Akü kapasitesi:
{energy_results["battery_capacity_kwh"]} kWh

Toplam şebekeye satışa uygun enerji:
{energy_results["total_grid_sell_energy_kwh"]:.3f} kWh

Ortalama akü doluluk oranı:
{energy_results["average_battery_soc_percent"]:.3f} %

Karar dağılımı:
{json.dumps(energy_results["decision_counts"], indent=4, ensure_ascii=False)}

5. Önemli Not
-------------
Enerji yönetimi modülü gerçek ticari elektrik satışı gerçekleştirmez. Bu modül, akademik proje kapsamında üretim, tüketim, akü doluluk oranı ve santral hava sensörü verilerine göre şebekeye satışa uygunluk kararını simülasyon ve AI modeliyle değerlendiren karar destek sistemidir.

6. Sonuç
--------
Proje bu haliyle üretim tahmini, anomali tespiti, büyük veri analizi, SQL tabanlı sorgulama, veri gölü mimarisi ve akıllı enerji yönetimi karar destek modülünü içeren bütünleşik bir GES büyük veri ve yapay zekâ sistemi haline getirilmiştir.
"""

extended_summary.write_text(text, encoding="utf-8")

print("Genişletilmiş proje özeti NASA meteoroloji verisi olmadan güncellendi:")
print(extended_summary)

print("\nHadoop veri gölü enerji yönetimi katmanı güncellendi:")
print(lake_energy)

print("\nEnergy management dosya sayısı:", len([x for x in lake_energy.iterdir() if x.is_file()]))
