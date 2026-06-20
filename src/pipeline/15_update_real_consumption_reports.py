from pathlib import Path
import json
import shutil

PROJECT_DIR = Path(__file__).resolve().parents[1]

FINAL_DIR = PROJECT_DIR / "final_outputs"
CONSUMPTION_DIR = PROJECT_DIR / "consumption_data"
REAL_ENERGY_DIR = PROJECT_DIR / "real_energy_management"
LAKE_DIR = PROJECT_DIR / "hadoop_data_lake"

FINAL_DIR.mkdir(parents=True, exist_ok=True)

real_results_file = REAL_ENERGY_DIR / "real_consumption_energy_management_results.json"
consumption_summary_file = CONSUMPTION_DIR / "uci_consumption_preparation_summary.json"

if not real_results_file.exists():
    raise FileNotFoundError(f"Gercek tuketim enerji yonetimi sonuc dosyasi bulunamadi: {real_results_file}")

if not consumption_summary_file.exists():
    raise FileNotFoundError(f"UCI tuketim hazirlama ozet dosyasi bulunamadi: {consumption_summary_file}")

with real_results_file.open("r", encoding="utf-8") as f:
    real_results = json.load(f)

with consumption_summary_file.open("r", encoding="utf-8") as f:
    consumption_summary = json.load(f)

# Hadoop veri gölüne gerçek tüketim ve gerçek enerji yönetimi katmanlarını ekle
lake_consumption = LAKE_DIR / "consumption_data"
lake_real_energy = LAKE_DIR / "real_energy_management"

lake_consumption.mkdir(parents=True, exist_ok=True)
lake_real_energy.mkdir(parents=True, exist_ok=True)

# Çok büyük ham txt dosyasını ikinci kez kopyalamıyoruz.
# Veri gölüne temizlenmiş 15 dakikalık veri ve özetleri ekliyoruz.
consumption_files_to_copy = [
    "cleaned_uci_15min_consumption.csv",
    "uci_consumption_dataset_info.txt",
    "uci_consumption_preparation_summary.json"
]

for file_name in consumption_files_to_copy:
    src = CONSUMPTION_DIR / file_name
    if src.exists():
        shutil.copy2(src, lake_consumption / src.name)

for file in REAL_ENERGY_DIR.iterdir():
    if file.is_file():
        shutil.copy2(file, lake_real_energy / file.name)

summary_txt = FINAL_DIR / "real_consumption_extended_project_summary.txt"

text = f"""GERCEK TUKETIM VERISIYLE GENISLETILMIS ENERJI YONETIMI OZETI
================================================================

Bu aşamada proje, UCI gerçek elektrik tüketim veri seti ile güçlendirilmiştir. Böylece enerji yönetimi modülü yalnızca simüle tüketimden oluşan küçük bir yapı olmaktan çıkarılmış, gerçek tüketim profili içeren büyük bir veri kaynağıyla desteklenmiştir.

1. Kullanılan Veri Kaynakları
-----------------------------
GES üretim verisi:
Kaggle Solar Power Generation Data - Plant 1

Gerçek tüketim verisi:
UCI Individual Household Electric Power Consumption Dataset

2. UCI Tüketim Verisi Hazırlama
-------------------------------
Ham tüketim satır sayısı:
{consumption_summary["raw_rows"]}

Temizlik sonrası satır sayısı:
{consumption_summary["rows_after_cleaning"]}

15 dakikalık tüketim veri satırı:
{consumption_summary["consumption_15min_rows"]}

Toplam tüketim:
{consumption_summary["total_consumption_kwh"]:.3f} kWh

3. Gerçek Tüketim Verili Enerji Yönetimi Modülü
-----------------------------------------------
Oluşturulan karar veri seti kayıt sayısı:
{real_results["record_count"]}

AI karar modeli doğruluk oranı:
{real_results["accuracy"]:.4f}

Akü kapasitesi:
{real_results["battery_capacity_kwh"]} kWh

Toplam gerçek tüketim:
{real_results["total_real_consumption_kwh"]:.3f} kWh

Toplam beklenen GES üretimi:
{real_results["total_expected_production_kwh"]:.3f} kWh

Toplam şebekeye satışa uygun enerji:
{real_results["total_grid_sell_energy_kwh"]:.3f} kWh

Ortalama akü doluluk oranı:
{real_results["average_battery_soc_after_percent"]:.3f} %

Karar dağılımı:
{json.dumps(real_results["decision_counts"], indent=4, ensure_ascii=False)}

4. Metodolojik Not
------------------
UCI tüketim verisi, Kaggle GES santralinin kendi tüketim verisi değildir. Bu nedenle çalışma birebir aynı tesise ait üretim-tüketim eşleştirmesi olarak değil, gerçek tüketim profiliyle desteklenen hibrit enerji yönetimi simülasyonu olarak değerlendirilmelidir.

AI modelinin yüksek doğruluk oranı, gerçek dünyada ticari satış kararlarının doğruluğu olarak değil; oluşturulan enerji yönetimi karar mantığının model tarafından öğrenilme başarısı olarak yorumlanmalıdır.

5. Sonuç
--------
Bu ekleme ile proje; üretim tahmini, anomali tespiti, Spark/Spark SQL analizi, Hadoop veri gölü yapısı ve gerçek tüketim profiline dayalı akıllı enerji yönetimi karar destek modülünü içeren daha güçlü bir büyük veri ve yapay zekâ sistemi haline gelmiştir.
"""

summary_txt.write_text(text, encoding="utf-8")

print("Gercek tuketim genisletilmis ozet dosyasi olusturuldu:")
print(summary_txt)

print("\nHadoop veri golu katmanlari guncellendi:")
print(lake_consumption)
print(lake_real_energy)

print("\nConsumption data lake dosya sayisi:", len([x for x in lake_consumption.iterdir() if x.is_file()]))
print("Real energy management data lake dosya sayisi:", len([x for x in lake_real_energy.iterdir() if x.is_file()]))
