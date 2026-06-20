from pathlib import Path
import json
import joblib
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "solar_data"

NUM_FEATURES = [
    "IRRADIATION",
    "AMBIENT_TEMPERATURE",
    "MODULE_TEMPERATURE",
    "HOUR",
    "MINUTE",
    "DAY",
    "MONTH"
]

def detect_plant_1():
    print("\nPlant 1 anomali tespiti basladi...")

    df = pd.read_csv(DATA_DIR / "Plant_1_Model_Data.csv")
    model = joblib.load(DATA_DIR / "plant_1_ac_power_model.pkl")

    X = df[NUM_FEATURES]

    df["EXPECTED_AC_POWER"] = model.predict(X)
    df["POWER_GAP"] = df["EXPECTED_AC_POWER"] - df["AC_POWER"]
    df["ABS_ERROR"] = df["POWER_GAP"].abs()

    positive_gap = df[df["POWER_GAP"] > 0]["POWER_GAP"]
    threshold = positive_gap.mean() + 3 * positive_gap.std()

    df["ANOMALY"] = df["POWER_GAP"] > threshold

    out_path = DATA_DIR / "Plant_1_Anomaly_Data.csv"
    df.to_csv(out_path, index=False)

    anomaly_count = int(df["ANOMALY"].sum())
    anomaly_rate = round((anomaly_count / len(df)) * 100, 2)

    print("Plant 1 anomali dosyasi kaydedildi:", out_path)
    print("Plant 1 anomali esigi:", threshold)
    print("Plant 1 anomali sayisi:", anomaly_count)
    print("Plant 1 anomali orani:", anomaly_rate, "%")

    return {
        "plant": "Plant 1",
        "threshold": round(float(threshold), 4),
        "total_rows": int(len(df)),
        "anomaly_count": anomaly_count,
        "anomaly_rate_percent": anomaly_rate
    }

def detect_plant_2():
    print("\nPlant 2 anomali tespiti basladi...")

    df = pd.read_csv(DATA_DIR / "Plant_2_Model_Data.csv")
    saved = joblib.load(DATA_DIR / "plant_2_ac_power_model_with_source.pkl")

    model = saved["model"]
    columns = saved["columns"]

    X = pd.get_dummies(
        df[NUM_FEATURES + ["SOURCE_KEY"]],
        columns=["SOURCE_KEY"]
    )
    X = X.reindex(columns=columns, fill_value=0)

    df["EXPECTED_AC_POWER"] = model.predict(X)
    df["POWER_GAP"] = df["EXPECTED_AC_POWER"] - df["AC_POWER"]
    df["ABS_ERROR"] = df["POWER_GAP"].abs()

    positive_gap = df[df["POWER_GAP"] > 0]["POWER_GAP"]
    threshold = positive_gap.mean() + 3 * positive_gap.std()

    df["ANOMALY"] = df["POWER_GAP"] > threshold

    out_path = DATA_DIR / "Plant_2_Anomaly_Data.csv"
    df.to_csv(out_path, index=False)

    anomaly_count = int(df["ANOMALY"].sum())
    anomaly_rate = round((anomaly_count / len(df)) * 100, 2)

    print("Plant 2 anomali dosyasi kaydedildi:", out_path)
    print("Plant 2 anomali esigi:", threshold)
    print("Plant 2 anomali sayisi:", anomaly_count)
    print("Plant 2 anomali orani:", anomaly_rate, "%")

    return {
        "plant": "Plant 2",
        "threshold": round(float(threshold), 4),
        "total_rows": int(len(df)),
        "anomaly_count": anomaly_count,
        "anomaly_rate_percent": anomaly_rate
    }

results = []
results.append(detect_plant_1())
results.append(detect_plant_2())

results_path = DATA_DIR / "anomaly_detection_results.json"

with open(results_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=4)

print("\nAnomali tespiti tamamlandi.")
print("Sonuc dosyasi kaydedildi:", results_path)
print(json.dumps(results, ensure_ascii=False, indent=4))
