from pathlib import Path
import subprocess
import sys

PROJECT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_DIR / "scripts"

scripts = [
    "01_prepare_data.py",
    "02_train_models.py",
    "03_detect_anomalies.py",
    "04_generate_charts.py",
    "05_generate_reports.py",
    "06_spark_analysis.py",
    "07_spark_sql_hive_like.py",
    "08_create_hadoop_data_lake.py",
    "10_energy_management_ai.py",
    "11_update_extended_reports.py"
]

print("GES AI genisletilmis proje akisi baslatildi...\n")

for script in scripts:
    script_path = SCRIPTS_DIR / script

    print("=" * 60)
    print(f"Calistiriliyor: {script}")
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(PROJECT_DIR)
    )

    if result.returncode != 0:
        print(f"\nHATA: {script} calisirken sorun olustu.")
        sys.exit(result.returncode)

    print(f"\nTamamlandi: {script}\n")

print("=" * 60)
print("Tum GES AI genisletilmis proje akisi basariyla tamamlandi.")
print("=" * 60)
