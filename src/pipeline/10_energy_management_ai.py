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
ENERGY_DIR = PROJECT_DIR / "energy_management"
FINAL_DIR = PROJECT_DIR / "final_outputs"

ENERGY_DIR.mkdir(parents=True, exist_ok=True)
FINAL_DIR.mkdir(parents=True, exist_ok=True)

plant_file = DATA_DIR / "Plant_1_Model_Data.csv"

if not plant_file.exists():
    raise FileNotFoundError(f"Plant 1 model verisi bulunamadi: {plant_file}")

print("Akilli enerji yonetimi AI modulu baslatildi...")
print("Kullanilan veri:", plant_file)

# ==========================================================
# 1) Plant 1 üretim + hava sensörü profilini hazırla
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
    raise ValueError(f"Eksik sutunlar: {missing}")

plant["DATE_HOUR"] = plant["DATE_TIME"].dt.floor("h")

# Aynı saat içindeki tüm inverterlerin toplam AC gücü
hourly_power = (
    plant.groupby("DATE_HOUR", as_index=False)["AC_POWER"]
    .sum()
    .rename(columns={"AC_POWER": "TOTAL_AC_POWER"})
)

# Saatlik hava sensörü ortalamaları
hourly_weather = (
    plant.groupby("DATE_HOUR", as_index=False)[
        ["IRRADIATION", "AMBIENT_TEMPERATURE", "MODULE_TEMPERATURE"]
    ]
    .mean()
)

# Tam saatlik aralık oluştur: gündüz + gece simülasyonu için
start_hour = plant["DATE_TIME"].min().floor("D")
end_hour = plant["DATE_TIME"].max().ceil("D")

hourly_index = pd.DataFrame({
    "DATE_HOUR": pd.date_range(start=start_hour, end=end_hour, freq="h")
})

data = hourly_index.merge(hourly_power, on="DATE_HOUR", how="left")
data = data.merge(hourly_weather, on="DATE_HOUR", how="left")

data["TOTAL_AC_POWER"] = data["TOTAL_AC_POWER"].fillna(0)

# Gece saatlerinde ışınım üretim verisinde olmadığı için 0 kabul edilir.
data["IRRADIATION"] = data["IRRADIATION"].fillna(0)

# Sıcaklıklar için ileri/geri doldurma yapılır.
data["AMBIENT_TEMPERATURE"] = data["AMBIENT_TEMPERATURE"].ffill().bfill()
data["MODULE_TEMPERATURE"] = data["MODULE_TEMPERATURE"].ffill().bfill()

data["DATE"] = data["DATE_HOUR"].dt.strftime("%Y-%m-%d")
data["HOUR"] = data["DATE_HOUR"].dt.hour

# ==========================================================
# 2) Üretimi mikro-şebeke / akü simülasyonu için kWh ölçeğine indir
# ==========================================================

max_power = data["TOTAL_AC_POWER"].max()

if max_power <= 0:
    raise ValueError("Pozitif AC guc verisi bulunamadi.")

# Demo sistem ölçeği: maksimum saatlik üretim 35 kWh kabul edilir.
MAX_HOURLY_PRODUCTION_KWH = 35.0

data["EXPECTED_PRODUCTION_KWH"] = (
    data["TOTAL_AC_POWER"] / max_power * MAX_HOURLY_PRODUCTION_KWH
)

# ==========================================================
# 3) Tüketim simülasyonu oluştur
# ==========================================================

rng = np.random.default_rng(42)

def simulate_consumption(row):
    hour = int(row["HOUR"])
    ambient_temp = float(row["AMBIENT_TEMPERATURE"])

    base = 6.0

    if 8 <= hour <= 17:
        usage = 10.0
    elif 18 <= hour <= 23:
        usage = 14.0
    else:
        usage = 5.0

    cooling_load = max(0, ambient_temp - 25) * 0.35
    random_noise = rng.normal(0, 1.1)

    consumption = base + usage + cooling_load + random_noise
    return round(max(3.0, consumption), 3)

data["CONSUMPTION_KWH"] = data.apply(simulate_consumption, axis=1)
data["SURPLUS_ENERGY_KWH"] = data["EXPECTED_PRODUCTION_KWH"] - data["CONSUMPTION_KWH"]

# ==========================================================
# 4) Akü ve şebekeye satış karar simülasyonu
# ==========================================================

BATTERY_CAPACITY_KWH = 120.0
MIN_SOC_PERCENT = 20.0
LOW_SOC_PERCENT = 35.0
SELL_SOC_PERCENT = 80.0

soc = 55.0

battery_soc_values = []
grid_sell_values = []
decision_values = []

for _, row in data.iterrows():
    production = float(row["EXPECTED_PRODUCTION_KWH"])
    consumption = float(row["CONSUMPTION_KWH"])
    surplus = production - consumption

    grid_sell_kwh = 0.0

    if surplus >= 0:
        if surplus <= 0.5:
            decision = "TUKETIME_VER"

        elif soc < SELL_SOC_PERCENT:
            decision = "AKUYU_SARJ_ET"

            available_capacity_kwh = BATTERY_CAPACITY_KWH * (100.0 - soc) / 100.0
            charged_kwh = min(surplus, available_capacity_kwh)
            soc += charged_kwh / BATTERY_CAPACITY_KWH * 100.0

        else:
            decision = "SEBEKEYE_SATISA_UYGUN"
            grid_sell_kwh = surplus

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

    battery_soc_values.append(round(soc, 3))
    grid_sell_values.append(round(grid_sell_kwh, 3))
    decision_values.append(decision)

data["BATTERY_CAPACITY_KWH"] = BATTERY_CAPACITY_KWH
data["BATTERY_SOC_PERCENT"] = battery_soc_values
data["GRID_SELL_ENERGY_KWH"] = grid_sell_values
data["AI_DECISION"] = decision_values

# ==========================================================
# 5) AI karar modeli eğitimi
# ==========================================================

feature_cols = [
    "EXPECTED_PRODUCTION_KWH",
    "CONSUMPTION_KWH",
    "SURPLUS_ENERGY_KWH",
    "BATTERY_CAPACITY_KWH",
    "BATTERY_SOC_PERCENT",
    "IRRADIATION",
    "AMBIENT_TEMPERATURE",
    "MODULE_TEMPERATURE",
    "HOUR"
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
    n_estimators=250,
    random_state=42,
    class_weight="balanced"
)

clf.fit(X_train, y_train)

pred = clf.predict(X_test)
accuracy = accuracy_score(y_test, pred)
report = classification_report(y_test, pred, zero_division=0)

# ==========================================================
# 6) Çıktıları kaydet
# ==========================================================

training_csv = ENERGY_DIR / "energy_management_training_data.csv"
model_file = ENERGY_DIR / "energy_management_ai_model.pkl"
results_json = ENERGY_DIR / "energy_management_results.json"
summary_txt = FINAL_DIR / "energy_management_ai_aciklama_metni.txt"

output_cols = [
    "DATE_HOUR",
    "DATE",
    "HOUR",
    "EXPECTED_PRODUCTION_KWH",
    "CONSUMPTION_KWH",
    "SURPLUS_ENERGY_KWH",
    "BATTERY_CAPACITY_KWH",
    "BATTERY_SOC_PERCENT",
    "GRID_SELL_ENERGY_KWH",
    "IRRADIATION",
    "AMBIENT_TEMPERATURE",
    "MODULE_TEMPERATURE",
    "AI_DECISION"
]

data[output_cols].to_csv(training_csv, index=False, encoding="utf-8")
joblib.dump({"model": clf, "features": feature_cols}, model_file)

results = {
    "record_count": int(len(model_data)),
    "accuracy": float(accuracy),
    "battery_capacity_kwh": BATTERY_CAPACITY_KWH,
    "decision_counts": {str(k): int(v) for k, v in label_counts.items()},
    "total_grid_sell_energy_kwh": float(model_data["GRID_SELL_ENERGY_KWH"].sum()),
    "average_battery_soc_percent": float(model_data["BATTERY_SOC_PERCENT"].mean()),
    "note": "Bu modul Plant 1 uretim ve hava sensoru verilerine dayali simule edilmis AI enerji yonetimi karar destek moduludur."
}

with results_json.open("w", encoding="utf-8") as f:
    json.dump(results, f, indent=4, ensure_ascii=False)

summary_text = f"""AI TABANLI AKILLI ENERJI YONETIMI VE SEBEKEYE SATIS KARAR MODULU
=================================================================

Bu modül, güneş enerjisi üretimi, tüketim ihtiyacı, akü kapasitesi, akü doluluk oranı ve santrale ait hava sensörü verilerini kullanarak enerji yönetimi kararı üretmek amacıyla geliştirilmiştir.

Kullanılan veri kaynağı:
- Plant 1 üretim verisi
- Plant 1 hava sensörü verisi
- Simüle edilmiş tüketim verisi
- Simüle edilmiş akü doluluk davranışı

Bu modül gerçek ticari elektrik satışı yapmaz. Şebekeye satışa uygunluk kararını simülasyon ve yapay zekâ modeli üzerinden verir.

Karar sınıfları:
- TUKETIME_VER
- AKUYU_SARJ_ET
- AKUDEN_KULLAN
- SEBEKEYE_SATISA_UYGUN
- SEBEKEDEN_DESTEK_AL

Model:
RandomForestClassifier

Kayıt sayısı:
{len(model_data)}

Model doğruluk oranı:
{accuracy:.4f}

Akü kapasitesi:
{BATTERY_CAPACITY_KWH} kWh

Toplam şebekeye satışa uygun enerji:
{model_data["GRID_SELL_ENERGY_KWH"].sum():.3f} kWh

Ortalama akü doluluk oranı:
{model_data["BATTERY_SOC_PERCENT"].mean():.3f} %

Karar dağılımı:
{label_counts.to_string()}

Bu modül sayesinde proje, yalnızca üretim tahmini ve anomali tespiti yapan bir yapı olmaktan çıkarılarak; üretim, tüketim, akü depolama ve şebekeye satışa uygunluk kararını birlikte değerlendiren akıllı enerji yönetim sistemine genişletilmiştir.

Not:
Bu çalışma gerçek şebeke satış işlemi gerçekleştirmez. Satış kararı, akademik proje kapsamında simülasyon ve karar destek modeli olarak ele alınmıştır.
"""

summary_txt.write_text(summary_text, encoding="utf-8")

# ==========================================================
# 7) Grafikler
# ==========================================================

decision_chart = FINAL_DIR / "energy_management_decision_distribution.png"
soc_chart = FINAL_DIR / "battery_soc_simulation.png"
sell_chart = FINAL_DIR / "grid_sell_energy_simulation.png"

plt.figure(figsize=(10, 5))
label_counts.sort_values().plot(kind="barh")
plt.title("AI Enerji Yönetimi Karar Dağılımı")
plt.xlabel("Kayıt Sayısı")
plt.ylabel("Karar")
plt.tight_layout()
plt.savefig(decision_chart, dpi=200)
plt.close()

plt.figure(figsize=(12, 5))
plt.plot(data["DATE_HOUR"], data["BATTERY_SOC_PERCENT"])
plt.title("Simüle Edilmiş Akü Doluluk Oranı")
plt.xlabel("Tarih")
plt.ylabel("Akü Doluluk Oranı (%)")
plt.tight_layout()
plt.savefig(soc_chart, dpi=200)
plt.close()

plt.figure(figsize=(12, 5))
plt.plot(data["DATE_HOUR"], data["GRID_SELL_ENERGY_KWH"])
plt.title("Şebekeye Satışa Uygun Fazla Enerji Simülasyonu")
plt.xlabel("Tarih")
plt.ylabel("Enerji (kWh)")
plt.tight_layout()
plt.savefig(sell_chart, dpi=200)
plt.close()

print("\nEnerji yonetimi AI modulu tamamlandi.")
print("Egitim verisi:", training_csv)
print("Model dosyasi:", model_file)
print("Sonuc JSON:", results_json)
print("Aciklama metni:", summary_txt)
print("Karar grafigi:", decision_chart)
print("Aku grafigi:", soc_chart)
print("Sebekeye satis grafigi:", sell_chart)
print("\nModel dogruluk orani:", round(accuracy, 4))
print("\nKarar dagilimi:")
print(label_counts)
