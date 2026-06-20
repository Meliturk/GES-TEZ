from pathlib import Path
import json
import warnings

import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

warnings.filterwarnings("ignore")

PROJECT_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_DIR / "solar_data"
CONSUMPTION_DIR = PROJECT_DIR / "consumption_data"
REAL_ENERGY_DIR = PROJECT_DIR / "real_energy_management"
FINAL_DIR = PROJECT_DIR / "final_outputs"

REAL_ENERGY_DIR.mkdir(parents=True, exist_ok=True)
FINAL_DIR.mkdir(parents=True, exist_ok=True)

plant_file = DATA_DIR / "Plant_1_Model_Data.csv"
consumption_file = CONSUMPTION_DIR / "cleaned_uci_15min_consumption.csv"

if not plant_file.exists():
    raise FileNotFoundError(f"Plant 1 model verisi bulunamadi: {plant_file}")

if not consumption_file.exists():
    raise FileNotFoundError(f"UCI temiz tuketim verisi bulunamadi: {consumption_file}")

print("Gercek tuketim verili enerji yonetimi AI modulu baslatildi...")
print("GES uretim verisi:", plant_file)
print("Gercek tuketim verisi:", consumption_file)

# ==========================================================
# 1) Plant 1 üretim + hava sensörü profilini 15 dk formata hazırla
# ==========================================================

plant = pd.read_csv(plant_file)
plant["DATE_TIME"] = pd.to_datetime(plant["DATE_TIME"], format="mixed", dayfirst=True, errors="coerce")
plant = plant.dropna(subset=["DATE_TIME"])

required_cols = [
    "AC_POWER",
    "IRRADIATION",
    "AMBIENT_TEMPERATURE",
    "MODULE_TEMPERATURE"
]

missing = [col for col in required_cols if col not in plant.columns]
if missing:
    raise ValueError(f"Plant verisinde eksik sutunlar: {missing}")

plant["DATE_15MIN"] = plant["DATE_TIME"].dt.floor("15min")

power_15min = (
    plant.groupby("DATE_15MIN", as_index=False)["AC_POWER"]
    .sum()
    .rename(columns={"AC_POWER": "TOTAL_AC_POWER"})
)

weather_15min = (
    plant.groupby("DATE_15MIN", as_index=False)[
        ["IRRADIATION", "AMBIENT_TEMPERATURE", "MODULE_TEMPERATURE"]
    ]
    .mean()
)

start_time = plant["DATE_TIME"].min().floor("D")
end_time = plant["DATE_TIME"].max().ceil("D")

full_index = pd.DataFrame({
    "DATE_15MIN": pd.date_range(start=start_time, end=end_time, freq="15min")
})

pv = full_index.merge(power_15min, on="DATE_15MIN", how="left")
pv = pv.merge(weather_15min, on="DATE_15MIN", how="left")

pv["TOTAL_AC_POWER"] = pv["TOTAL_AC_POWER"].fillna(0)
pv["IRRADIATION"] = pv["IRRADIATION"].fillna(0)
pv["AMBIENT_TEMPERATURE"] = pv["AMBIENT_TEMPERATURE"].ffill().bfill()
pv["MODULE_TEMPERATURE"] = pv["MODULE_TEMPERATURE"].ffill().bfill()

pv["DATE_ONLY"] = pv["DATE_15MIN"].dt.floor("D")
unique_days = sorted(pv["DATE_ONLY"].unique())
day_map = {day: i for i, day in enumerate(unique_days)}

pv["PATTERN_DAY_INDEX"] = pv["DATE_ONLY"].map(day_map)
pv["SLOT"] = pv["DATE_15MIN"].dt.hour * 4 + (pv["DATE_15MIN"].dt.minute // 15)

# Mikro-şebeke ölçeği için PV üretimini 15 dk kWh değerine indir
max_power = pv["TOTAL_AC_POWER"].max()
if max_power <= 0:
    raise ValueError("Pozitif AC guc bulunamadi.")

MAX_15MIN_PRODUCTION_KWH = 1.8

pv["EXPECTED_PRODUCTION_KWH"] = (
    pv["TOTAL_AC_POWER"] / max_power * MAX_15MIN_PRODUCTION_KWH
)

pv_pattern = pv[
    [
        "PATTERN_DAY_INDEX",
        "SLOT",
        "EXPECTED_PRODUCTION_KWH",
        "IRRADIATION",
        "AMBIENT_TEMPERATURE",
        "MODULE_TEMPERATURE"
    ]
].copy()

pattern_day_count = pv_pattern["PATTERN_DAY_INDEX"].nunique()

# ==========================================================
# 2) UCI gerçek tüketim verisini oku
# ==========================================================

cons = pd.read_csv(consumption_file)
cons["DATE_TIME"] = pd.to_datetime(cons["DATE_TIME"], errors="coerce")
cons = cons.dropna(subset=["DATE_TIME", "CONSUMPTION_KWH"])
cons = cons[cons["CONSUMPTION_KWH"] > 0].copy()

cons = cons.sort_values("DATE_TIME").reset_index(drop=True)

cons["DATE_ONLY"] = cons["DATE_TIME"].dt.floor("D")
first_day = cons["DATE_ONLY"].min()

cons["CONSUMPTION_DAY_INDEX"] = (cons["DATE_ONLY"] - first_day).dt.days
cons["PATTERN_DAY_INDEX"] = cons["CONSUMPTION_DAY_INDEX"] % pattern_day_count
cons["SLOT"] = cons["DATE_TIME"].dt.hour * 4 + (cons["DATE_TIME"].dt.minute // 15)

# GES üretim profilini, gerçek tüketim zaman serisinin zaman dilimlerine hizala
data = cons.merge(
    pv_pattern,
    on=["PATTERN_DAY_INDEX", "SLOT"],
    how="left"
)

data["EXPECTED_PRODUCTION_KWH"] = data["EXPECTED_PRODUCTION_KWH"].fillna(0)
data["IRRADIATION"] = data["IRRADIATION"].fillna(0)
data["AMBIENT_TEMPERATURE"] = data["AMBIENT_TEMPERATURE"].ffill().bfill()
data["MODULE_TEMPERATURE"] = data["MODULE_TEMPERATURE"].ffill().bfill()

data["HOUR"] = data["DATE_TIME"].dt.hour
data["MINUTE"] = data["DATE_TIME"].dt.minute
data["DAY_OF_WEEK"] = data["DATE_TIME"].dt.dayofweek
data["MONTH"] = data["DATE_TIME"].dt.month

# Simüle zaman bazlı şebeke fiyatı
def grid_price(hour):
    if 17 <= hour <= 22:
        return 2.20
    elif 8 <= hour <= 16:
        return 1.65
    else:
        return 1.10

data["GRID_PRICE_TL_KWH"] = data["HOUR"].apply(grid_price)

# ==========================================================
# 3) Akü ve şebekeye satış karar simülasyonu
# ==========================================================

BATTERY_CAPACITY_KWH = 20.0
MIN_SOC_PERCENT = 15.0
LOW_SOC_PERCENT = 30.0
SELL_SOC_PERCENT = 85.0
HIGH_PRICE_THRESHOLD = 1.60

soc = 55.0

soc_before_values = []
soc_after_values = []
surplus_values = []
grid_sell_values = []
decision_values = []

for _, row in data.iterrows():
    production = float(row["EXPECTED_PRODUCTION_KWH"])
    consumption = float(row["CONSUMPTION_KWH"])
    price = float(row["GRID_PRICE_TL_KWH"])

    surplus = production - consumption
    soc_before = soc
    grid_sell_kwh = 0.0

    if surplus >= 0:
        if surplus <= 0.02:
            decision = "TUKETIME_VER"

        elif soc < SELL_SOC_PERCENT:
            decision = "AKUYU_SARJ_ET"

            available_capacity_kwh = BATTERY_CAPACITY_KWH * (100.0 - soc) / 100.0
            charged_kwh = min(surplus, available_capacity_kwh)
            soc += charged_kwh / BATTERY_CAPACITY_KWH * 100.0

        else:
            if price >= HIGH_PRICE_THRESHOLD or soc >= 95.0:
                decision = "SEBEKEYE_SATISA_UYGUN"
                grid_sell_kwh = surplus
            else:
                decision = "AKUYU_SARJ_ET"
                available_capacity_kwh = BATTERY_CAPACITY_KWH * (100.0 - soc) / 100.0
                charged_kwh = min(surplus, available_capacity_kwh)
                soc += charged_kwh / BATTERY_CAPACITY_KWH * 100.0

    else:
        deficit = abs(surplus)

        if soc > LOW_SOC_PERCENT:
            decision = "AKUDEN_KULLAN"

            usable_battery_kwh = BATTERY_CAPACITY_KWH * (soc - MIN_SOC_PERCENT) / 100.0
            discharged_kwh = min(deficit, usable_battery_kwh)
            soc -= discharged_kwh / BATTERY_CAPACITY_KWH * 100.0

        else:
            decision = "SEBEKEDEN_DESTEK_AL"

    soc = max(MIN_SOC_PERCENT, min(100.0, soc))

    soc_before_values.append(round(soc_before, 3))
    soc_after_values.append(round(soc, 3))
    surplus_values.append(round(surplus, 6))
    grid_sell_values.append(round(grid_sell_kwh, 6))
    decision_values.append(decision)

data["BATTERY_CAPACITY_KWH"] = BATTERY_CAPACITY_KWH
data["BATTERY_SOC_BEFORE_PERCENT"] = soc_before_values
data["BATTERY_SOC_AFTER_PERCENT"] = soc_after_values
data["SURPLUS_ENERGY_KWH"] = surplus_values
data["GRID_SELL_ENERGY_KWH"] = grid_sell_values
data["AI_DECISION"] = decision_values

# ==========================================================
# 4) AI karar modeli eğitimi
# ==========================================================

feature_cols = [
    "EXPECTED_PRODUCTION_KWH",
    "CONSUMPTION_KWH",
    "SURPLUS_ENERGY_KWH",
    "BATTERY_CAPACITY_KWH",
    "BATTERY_SOC_BEFORE_PERCENT",
    "IRRADIATION",
    "AMBIENT_TEMPERATURE",
    "MODULE_TEMPERATURE",
    "GRID_PRICE_TL_KWH",
    "HOUR",
    "MINUTE",
    "DAY_OF_WEEK",
    "MONTH"
]

model_data = data.dropna(subset=feature_cols + ["AI_DECISION"]).copy()

X = model_data[feature_cols]
y = model_data["AI_DECISION"]

label_counts = y.value_counts()

if label_counts.shape[0] < 2:
    raise ValueError("AI karar modeli icin en az iki karar sinifi gerekli.")

can_stratify = label_counts.min() >= 2

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.25,
    random_state=42,
    stratify=y if can_stratify else None
)

clf = RandomForestClassifier(
    n_estimators=120,
    max_depth=18,
    random_state=42,
    class_weight="balanced",
    n_jobs=-1
)

clf.fit(X_train, y_train)

pred = clf.predict(X_test)
accuracy = accuracy_score(y_test, pred)
report = classification_report(y_test, pred, zero_division=0)

# ==========================================================
# 5) Çıktıları kaydet
# ==========================================================

training_csv = REAL_ENERGY_DIR / "real_consumption_energy_management_training_data.csv"
model_file = REAL_ENERGY_DIR / "real_consumption_energy_management_ai_model.pkl"
results_json = REAL_ENERGY_DIR / "real_consumption_energy_management_results.json"
classification_txt = REAL_ENERGY_DIR / "real_consumption_classification_report.txt"
summary_txt = FINAL_DIR / "real_consumption_energy_management_aciklama_metni.txt"

output_cols = [
    "DATE_TIME",
    "EXPECTED_PRODUCTION_KWH",
    "CONSUMPTION_KWH",
    "SURPLUS_ENERGY_KWH",
    "BATTERY_CAPACITY_KWH",
    "BATTERY_SOC_BEFORE_PERCENT",
    "BATTERY_SOC_AFTER_PERCENT",
    "GRID_SELL_ENERGY_KWH",
    "GRID_PRICE_TL_KWH",
    "IRRADIATION",
    "AMBIENT_TEMPERATURE",
    "MODULE_TEMPERATURE",
    "HOUR",
    "MINUTE",
    "DAY_OF_WEEK",
    "MONTH",
    "AI_DECISION"
]

model_data[output_cols].to_csv(training_csv, index=False, encoding="utf-8")
joblib.dump({"model": clf, "features": feature_cols}, model_file)
classification_txt.write_text(report, encoding="utf-8")

results = {
    "source_consumption_dataset": "UCI Individual Household Electric Power Consumption",
    "solar_source_dataset": "Kaggle Solar Power Generation Data - Plant 1",
    "record_count": int(len(model_data)),
    "accuracy": float(accuracy),
    "battery_capacity_kwh": BATTERY_CAPACITY_KWH,
    "decision_counts": {str(k): int(v) for k, v in label_counts.items()},
    "total_real_consumption_kwh": float(model_data["CONSUMPTION_KWH"].sum()),
    "total_expected_production_kwh": float(model_data["EXPECTED_PRODUCTION_KWH"].sum()),
    "total_grid_sell_energy_kwh": float(model_data["GRID_SELL_ENERGY_KWH"].sum()),
    "average_battery_soc_before_percent": float(model_data["BATTERY_SOC_BEFORE_PERCENT"].mean()),
    "average_battery_soc_after_percent": float(model_data["BATTERY_SOC_AFTER_PERCENT"].mean()),
    "note": "Bu modul UCI gercek tuketim verisi ile Plant 1 GES uretim profilini hibrit enerji yonetimi simülasyonunda birlikte kullanir."
}

with results_json.open("w", encoding="utf-8") as f:
    json.dump(results, f, indent=4, ensure_ascii=False)

summary_text = f"""GERCEK TUKETIM VERISIYLE AI TABANLI ENERJI YONETIMI MODULU
=========================================================

Bu modül, UCI gerçek elektrik tüketim veri seti ile Plant 1 güneş enerjisi üretim profilini birlikte kullanarak akıllı enerji yönetimi kararları üretmek amacıyla geliştirilmiştir.

Kullanılan veri kaynakları:
- Kaggle Solar Power Generation Data - Plant 1 üretim ve hava sensörü verileri
- UCI Individual Household Electric Power Consumption gerçek tüketim verisi

Önemli metodolojik not:
UCI tüketim verisi, Kaggle GES santralinin kendi tüketim verisi değildir. Bu nedenle bu çalışma, aynı tesise ait birebir üretim-tüketim eşleştirmesi olarak değil; gerçek tüketim profiliyle desteklenen hibrit enerji yönetimi simülasyonu olarak değerlendirilmelidir.

Oluşturulan karar veri seti kayıt sayısı:
{len(model_data)}

AI karar modeli doğruluk oranı:
{accuracy:.4f}

Akü kapasitesi:
{BATTERY_CAPACITY_KWH} kWh

Toplam gerçek tüketim:
{model_data["CONSUMPTION_KWH"].sum():.3f} kWh

Toplam beklenen GES üretimi:
{model_data["EXPECTED_PRODUCTION_KWH"].sum():.3f} kWh

Toplam şebekeye satışa uygun enerji:
{model_data["GRID_SELL_ENERGY_KWH"].sum():.3f} kWh

Ortalama akü doluluk oranı:
{model_data["BATTERY_SOC_AFTER_PERCENT"].mean():.3f} %

Karar dağılımı:
{label_counts.to_string()}

Bu modül sayesinde enerji yönetimi tarafı yalnızca simüle tüketimden oluşan küçük bir yapı olmaktan çıkarılmış, gerçek tüketim davranışı içeren büyük bir veri setiyle desteklenmiştir.
"""

summary_txt.write_text(summary_text, encoding="utf-8")

# ==========================================================
# 6) Grafikler
# ==========================================================

decision_chart = FINAL_DIR / "real_consumption_decision_distribution.png"
soc_chart = FINAL_DIR / "real_consumption_battery_soc_simulation.png"
sell_chart = FINAL_DIR / "real_consumption_grid_sell_energy_simulation.png"
prod_cons_chart = FINAL_DIR / "real_consumption_production_vs_consumption_sample.png"

plt.figure(figsize=(10, 5))
label_counts.sort_values().plot(kind="barh")
plt.title("Gerçek Tüketim Verili AI Karar Dağılımı")
plt.xlabel("Kayıt Sayısı")
plt.ylabel("Karar")
plt.tight_layout()
plt.savefig(decision_chart, dpi=200)
plt.close()

sample = model_data.head(96 * 14).copy()

plt.figure(figsize=(12, 5))
plt.plot(sample["DATE_TIME"], sample["BATTERY_SOC_AFTER_PERCENT"])
plt.title("Akü Doluluk Oranı Simülasyonu")
plt.xlabel("Tarih")
plt.ylabel("Akü Doluluk Oranı (%)")
plt.tight_layout()
plt.savefig(soc_chart, dpi=200)
plt.close()

plt.figure(figsize=(12, 5))
plt.plot(sample["DATE_TIME"], sample["GRID_SELL_ENERGY_KWH"])
plt.title("Şebekeye Satışa Uygun Enerji Simülasyonu")
plt.xlabel("Tarih")
plt.ylabel("Enerji (kWh)")
plt.tight_layout()
plt.savefig(sell_chart, dpi=200)
plt.close()

plt.figure(figsize=(12, 5))
plt.plot(sample["DATE_TIME"], sample["EXPECTED_PRODUCTION_KWH"], label="GES Üretimi")
plt.plot(sample["DATE_TIME"], sample["CONSUMPTION_KWH"], label="Gerçek Tüketim")
plt.title("GES Üretimi ve Gerçek Tüketim Karşılaştırması")
plt.xlabel("Tarih")
plt.ylabel("Enerji (kWh / 15 dk)")
plt.legend()
plt.tight_layout()
plt.savefig(prod_cons_chart, dpi=200)
plt.close()

print("\nGercek tuketim verili enerji yonetimi AI modulu tamamlandi.")
print("Egitim verisi:", training_csv)
print("Model dosyasi:", model_file)
print("Sonuc JSON:", results_json)
print("Classification report:", classification_txt)
print("Aciklama metni:", summary_txt)
print("\nModel dogruluk orani:", round(accuracy, 4))
print("\nKayit sayisi:", len(model_data))
print("\nKarar dagilimi:")
print(label_counts)
