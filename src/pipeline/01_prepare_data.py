from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "solar_data"

def prepare_plant(plant_no):
    print(f"\nPlant {plant_no} veri hazirlama basladi...")

    gen_path = DATA_DIR / f"Plant_{plant_no}_Generation_Data.csv"
    weather_path = DATA_DIR / f"Plant_{plant_no}_Weather_Sensor_Data.csv"

    gen = pd.read_csv(gen_path)
    weather = pd.read_csv(weather_path)

    gen["DATE_TIME"] = pd.to_datetime(gen["DATE_TIME"], format="mixed", dayfirst=True)
    weather["DATE_TIME"] = pd.to_datetime(weather["DATE_TIME"], format="mixed", dayfirst=True)

    merged = pd.merge(
        gen,
        weather[["DATE_TIME", "AMBIENT_TEMPERATURE", "MODULE_TEMPERATURE", "IRRADIATION"]],
        on="DATE_TIME",
        how="left"
    )

    merged_path = DATA_DIR / f"Plant_{plant_no}_Merged_Data.csv"
    merged.to_csv(merged_path, index=False)

    clean = merged.dropna().copy()
    clean_path = DATA_DIR / f"Plant_{plant_no}_Clean_Data.csv"
    clean.to_csv(clean_path, index=False)

    daytime = clean[clean["IRRADIATION"] > 0].copy()
    daytime_path = DATA_DIR / f"Plant_{plant_no}_Daytime_Data.csv"
    daytime.to_csv(daytime_path, index=False)

    daytime["HOUR"] = daytime["DATE_TIME"].dt.hour
    daytime["MINUTE"] = daytime["DATE_TIME"].dt.minute
    daytime["DAY"] = daytime["DATE_TIME"].dt.day
    daytime["MONTH"] = daytime["DATE_TIME"].dt.month

    model_path = DATA_DIR / f"Plant_{plant_no}_Model_Data.csv"
    daytime.to_csv(model_path, index=False)

    print(f"Plant {plant_no} tamamlandi.")
    print(f"Merged: {merged.shape}")
    print(f"Clean: {clean.shape}")
    print(f"Daytime/Model: {daytime.shape}")

prepare_plant(1)
prepare_plant(2)

print("\nVeri hazirlama scripti basariyla tamamlandi.")
