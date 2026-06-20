from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "solar_data"
OUTPUT_DIR = PROJECT_DIR / "final_outputs"

OUTPUT_DIR.mkdir(exist_ok=True)

def save_source_chart(plant_no):
    df = pd.read_csv(DATA_DIR / f"Plant_{plant_no}_Anomaly_Data.csv")
    anom = df[df["ANOMALY"] == True]

    summary = anom.groupby("SOURCE_KEY").size().sort_values(ascending=False).head(10)

    plt.figure(figsize=(12, 6))
    summary.plot(kind="bar")
    plt.title(f"Plant {plant_no} - En Cok Anomali Veren Ilk 10 SOURCE_KEY")
    plt.xlabel("SOURCE_KEY")
    plt.ylabel("Anomali Sayisi")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    out = OUTPUT_DIR / f"plant_{plant_no}_anomaly_by_source.png"
    plt.savefig(out, dpi=200)
    plt.close()

    print("Kaydedildi:", out)

def save_day_chart(plant_no):
    df = pd.read_csv(DATA_DIR / f"Plant_{plant_no}_Anomaly_Data.csv")
    anom = df[df["ANOMALY"] == True].copy()

    anom["DATE_TIME"] = pd.to_datetime(anom["DATE_TIME"])
    anom["DATE"] = anom["DATE_TIME"].dt.date

    daily = anom.groupby("DATE").size().sort_index()

    plt.figure(figsize=(12, 6))
    daily.plot(kind="bar")
    plt.title(f"Plant {plant_no} - Gun Bazinda Anomali Sayisi")
    plt.xlabel("Tarih")
    plt.ylabel("Anomali Sayisi")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    out = OUTPUT_DIR / f"plant_{plant_no}_anomaly_by_day.png"
    plt.savefig(out, dpi=200)
    plt.close()

    print("Kaydedildi:", out)

def save_actual_expected_chart(plant_no):
    df = pd.read_csv(DATA_DIR / f"Plant_{plant_no}_Anomaly_Data.csv")
    df["DATE_TIME"] = pd.to_datetime(df["DATE_TIME"])

    anom = df[df["ANOMALY"] == True].copy()
    anom["DATE"] = anom["DATE_TIME"].dt.date

    top_day = anom.groupby("DATE").size().sort_values(ascending=False).index[0]
    day_anom = anom[anom["DATE"] == top_day]
    top_source = day_anom.groupby("SOURCE_KEY").size().sort_values(ascending=False).index[0]

    sub = df[
        (df["SOURCE_KEY"] == top_source) &
        (df["DATE_TIME"].dt.date == top_day)
    ].copy()

    plt.figure(figsize=(12, 6))
    plt.plot(sub["DATE_TIME"], sub["AC_POWER"], marker="o", label="Gercek AC_POWER")
    plt.plot(sub["DATE_TIME"], sub["EXPECTED_AC_POWER"], marker="o", label="Modelin Bekledigi AC_POWER")

    anom_points = sub[sub["ANOMALY"] == True]
    plt.scatter(anom_points["DATE_TIME"], anom_points["AC_POWER"], s=80, label="Anomali Noktalari")

    plt.title(f"Plant {plant_no} - Gercek ve Beklenen AC Guc Karsilastirmasi")
    plt.xlabel("Zaman")
    plt.ylabel("AC_POWER")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    out = OUTPUT_DIR / f"plant_{plant_no}_actual_vs_expected.png"
    plt.savefig(out, dpi=200)
    plt.close()

    print("Kaydedildi:", out)
    print(f"Plant {plant_no} secilen gun:", top_day)
    print(f"Plant {plant_no} secilen SOURCE_KEY:", top_source)

def save_comparison_charts():
    with open(DATA_DIR / "model_training_results.json", "r", encoding="utf-8") as f:
        model_results = json.load(f)

    with open(DATA_DIR / "anomaly_detection_results.json", "r", encoding="utf-8") as f:
        anomaly_results = json.load(f)

    plants = [item["plant"] for item in anomaly_results]
    anomaly_rates = [item["anomaly_rate_percent"] for item in anomaly_results]
    r2_scores = [item["r2"] for item in model_results]

    plt.figure(figsize=(8, 5))
    plt.bar(plants, anomaly_rates)
    plt.title("Plant 1 ve Plant 2 Anomali Orani Karsilastirmasi")
    plt.xlabel("Santral")
    plt.ylabel("Anomali Orani (%)")
    plt.ylim(0, max(anomaly_rates) + 0.3)
    plt.tight_layout()

    out1 = OUTPUT_DIR / "plant_anomaly_rate_comparison.png"
    plt.savefig(out1, dpi=200)
    plt.close()

    print("Kaydedildi:", out1)

    plt.figure(figsize=(8, 5))
    plt.bar(plants, r2_scores)
    plt.title("Plant 1 ve Plant 2 Model R2 Basari Karsilastirmasi")
    plt.xlabel("Santral")
    plt.ylabel("R2 Skoru")
    plt.ylim(0, 1.1)
    plt.tight_layout()

    out2 = OUTPUT_DIR / "plant_model_r2_comparison.png"
    plt.savefig(out2, dpi=200)
    plt.close()

    print("Kaydedildi:", out2)

save_source_chart(1)
save_day_chart(1)
save_actual_expected_chart(1)

save_source_chart(2)
save_day_chart(2)
save_actual_expected_chart(2)

save_comparison_charts()

print("\nGrafik olusturma scripti basariyla tamamlandi.")
