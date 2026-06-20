from pathlib import Path
import json
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "solar_data"
OUTPUT_DIR = PROJECT_DIR / "final_outputs"

OUTPUT_DIR.mkdir(exist_ok=True)

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

model_results = load_json(DATA_DIR / "model_training_results.json")
anomaly_results = load_json(DATA_DIR / "anomaly_detection_results.json")

model_dict = {item["plant"]: item for item in model_results}
anom_dict = {item["plant"]: item for item in anomaly_results}

comparison_rows = []

for plant_no in [1, 2]:
    plant_name = f"Plant {plant_no}"

    df = pd.read_csv(DATA_DIR / f"Plant_{plant_no}_Anomaly_Data.csv")
    anom = df[df["ANOMALY"] == True].copy()

    anom["DATE_TIME"] = pd.to_datetime(anom["DATE_TIME"])
    anom["DATE"] = anom["DATE_TIME"].dt.date

    top_sources = anom.groupby("SOURCE_KEY").size().sort_values(ascending=False)
    top_days = anom.groupby("DATE").size().sort_values(ascending=False)

    top_source = top_sources.index[0]
    top_day = str(top_days.index[0])

    model_info = model_dict[plant_name]
    anom_info = anom_dict[plant_name]

    summary_path = OUTPUT_DIR / f"plant_{plant_no}_results_summary.txt"

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"{plant_name.upper()} AI ANOMALI TESPITI SONUC OZETI\n")
        f.write("=====================================\n\n")
        f.write(f"Toplam gunduz verisi: {anom_info['total_rows']}\n")
        f.write(f"Model MAE: {model_info['mae']}\n")
        f.write(f"Model R2: {model_info['r2']}\n")
        f.write(f"Toplam anomali sayisi: {anom_info['anomaly_count']}\n")
        f.write(f"Anomali orani: {anom_info['anomaly_rate_percent']}%\n\n")

        f.write("En cok anomali veren ilk 5 SOURCE_KEY:\n")
        for source, count in top_sources.head(5).items():
            f.write(f"- {source}: {count}\n")

        f.write("\nEn cok anomali gozlenen ilk 5 gun:\n")
        for day, count in top_days.head(5).items():
            f.write(f"- {day}: {count}\n")

    comparison_rows.append({
        "Plant": plant_name,
        "R2": model_info["r2"],
        "MAE": model_info["mae"],
        "Daytime_Data_Count": anom_info["total_rows"],
        "Anomaly_Count": anom_info["anomaly_count"],
        "Anomaly_Rate_Percent": anom_info["anomaly_rate_percent"],
        "Top_Anomaly_SOURCE_KEY": top_source,
        "Top_Anomaly_Day": top_day
    })

comparison_df = pd.DataFrame(comparison_rows)
comparison_path = OUTPUT_DIR / "plant_comparison_results.csv"
comparison_df.to_csv(comparison_path, index=False, encoding="utf-8-sig")

final_summary_path = OUTPUT_DIR / "final_project_summary.txt"

with open(final_summary_path, "w", encoding="utf-8") as f:
    f.write("GES AI PROJESI GENEL SONUC OZETI\n")
    f.write("================================\n\n")

    for row in comparison_rows:
        f.write(f"{row['Plant']} Sonuclari\n")
        f.write("-----------------\n")
        f.write(f"Model R2: {row['R2']}\n")
        f.write(f"Model MAE: {row['MAE']}\n")
        f.write(f"Toplam gunduz verisi: {row['Daytime_Data_Count']}\n")
        f.write(f"Toplam anomali sayisi: {row['Anomaly_Count']}\n")
        f.write(f"Anomali orani: {row['Anomaly_Rate_Percent']}%\n")
        f.write(f"En cok anomali veren SOURCE_KEY: {row['Top_Anomaly_SOURCE_KEY']}\n")
        f.write(f"En yogun anomali gunu: {row['Top_Anomaly_Day']}\n\n")

    f.write("Genel Yorum\n")
    f.write("-----------\n")
    f.write("Her iki santralde de model, beklenen AC guc uretimi ile gercek AC guc uretimi arasindaki farki kullanarak anomali tespiti yapmistir. ")
    f.write("Plant 1 model performansi Plant 2 modeline gore daha yuksektir. ")
    f.write("Plant 2 anomali orani Plant 1 oranindan daha yuksektir. ")
    f.write("Bu durum Plant 2 tarafinda uretim davranisinda daha fazla sapma oldugunu gostermektedir.\n")

print("Raporlar olusturuldu:")
print(final_summary_path)
print(comparison_path)
print(OUTPUT_DIR / "plant_1_results_summary.txt")
print(OUTPUT_DIR / "plant_2_results_summary.txt")
print("\nRapor olusturma scripti basariyla tamamlandi.")
