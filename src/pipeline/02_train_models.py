from pathlib import Path
import json
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

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

def train_plant_1():
    print("\nPlant 1 model egitimi basladi...")

    df = pd.read_csv(DATA_DIR / "Plant_1_Model_Data.csv")

    X = df[NUM_FEATURES]
    y = df["AC_POWER"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestRegressor(
        n_estimators=100,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)

    model_path = DATA_DIR / "plant_1_ac_power_model.pkl"
    joblib.dump(model, model_path)

    print("Plant 1 model kaydedildi:", model_path)
    print("Plant 1 MAE:", mae)
    print("Plant 1 R2:", r2)

    return {
        "plant": "Plant 1",
        "model_file": str(model_path),
        "mae": round(mae, 4),
        "r2": round(r2, 4)
    }

def train_plant_2():
    print("\nPlant 2 model egitimi basladi...")

    df = pd.read_csv(DATA_DIR / "Plant_2_Model_Data.csv")

    X = pd.get_dummies(
        df[NUM_FEATURES + ["SOURCE_KEY"]],
        columns=["SOURCE_KEY"]
    )
    y = df["AC_POWER"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestRegressor(
        n_estimators=100,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)

    model_path = DATA_DIR / "plant_2_ac_power_model_with_source.pkl"
    joblib.dump(
        {
            "model": model,
            "columns": X.columns.tolist()
        },
        model_path
    )

    print("Plant 2 model kaydedildi:", model_path)
    print("Plant 2 MAE:", mae)
    print("Plant 2 R2:", r2)

    return {
        "plant": "Plant 2",
        "model_file": str(model_path),
        "mae": round(mae, 4),
        "r2": round(r2, 4)
    }

results = []
results.append(train_plant_1())
results.append(train_plant_2())

results_path = DATA_DIR / "model_training_results.json"

with open(results_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=4)

print("\nModel egitimi tamamlandi.")
print("Sonuc dosyasi kaydedildi:", results_path)
print(json.dumps(results, ensure_ascii=False, indent=4))
