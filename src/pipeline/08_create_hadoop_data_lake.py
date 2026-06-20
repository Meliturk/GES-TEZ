from pathlib import Path
import shutil

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "solar_data"
SPARK_DIR = PROJECT_DIR / "spark_outputs"
LAKE_DIR = PROJECT_DIR / "hadoop_data_lake"

folders = {
    "raw": LAKE_DIR / "raw",
    "processed": LAKE_DIR / "processed",
    "model": LAKE_DIR / "model",
    "anomaly": LAKE_DIR / "anomaly",
    "spark_results": LAKE_DIR / "spark_results"
}

for folder in folders.values():
    folder.mkdir(parents=True, exist_ok=True)

def copy_file(src, dest_folder):
    if src.exists():
        shutil.copy2(src, dest_folder / src.name)
        print("Kopyalandi:", src.name)
    else:
        print("Bulunamadi:", src)

raw_files = [
    "Plant_1_Generation_Data.csv",
    "Plant_1_Weather_Sensor_Data.csv",
    "Plant_2_Generation_Data.csv",
    "Plant_2_Weather_Sensor_Data.csv"
]

processed_files = [
    "Plant_1_Model_Data.csv",
    "Plant_2_Model_Data.csv"
]

model_files = [
    "plant_1_ac_power_model.pkl",
    "plant_2_ac_power_model_with_source.pkl"
]

anomaly_files = [
    "Plant_1_Anomaly_Data.csv",
    "Plant_2_Anomaly_Data.csv"
]

print("\nRAW katmani:")
for file in raw_files:
    copy_file(DATA_DIR / file, folders["raw"])

print("\nPROCESSED katmani:")
for file in processed_files:
    copy_file(DATA_DIR / file, folders["processed"])

print("\nMODEL katmani:")
for file in model_files:
    copy_file(DATA_DIR / file, folders["model"])

print("\nANOMALY katmani:")
for file in anomaly_files:
    copy_file(DATA_DIR / file, folders["anomaly"])

print("\nSPARK_RESULTS katmani:")
if SPARK_DIR.exists():
    for file in SPARK_DIR.iterdir():
        if file.is_file():
            copy_file(file, folders["spark_results"])

print("\nHadoop/HDFS benzeri veri golu yapisi hazirlandi.")

for name, folder in folders.items():
    file_count = len([x for x in folder.iterdir() if x.is_file()])
    print(f"{name}: {file_count} dosya")
