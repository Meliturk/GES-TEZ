from pathlib import Path
import pandas as pd
import json

PROJECT_DIR = Path(__file__).resolve().parents[1]
CONSUMPTION_DIR = PROJECT_DIR / "consumption_data"
FINAL_DIR = PROJECT_DIR / "final_outputs"

CONSUMPTION_DIR.mkdir(parents=True, exist_ok=True)
FINAL_DIR.mkdir(parents=True, exist_ok=True)

raw_file = CONSUMPTION_DIR / "household_power_consumption.txt"

if not raw_file.exists():
    raise FileNotFoundError(f"Ham UCI tuketim dosyasi bulunamadi: {raw_file}")

print("UCI ham tuketim verisi okunuyor...")
print("Dosya:", raw_file)

df = pd.read_csv(
    raw_file,
    sep=";",
    na_values=["?"],
    low_memory=False
)

raw_rows = len(df)

print("Ham satir sayisi:", raw_rows)

# Tarih ve saat bilgisini birlestir
df["DATE_TIME"] = pd.to_datetime(
    df["Date"] + " " + df["Time"],
    format="%d/%m/%Y %H:%M:%S",
    errors="coerce"
)

# Gerekli sayisal kolonlari temizle
numeric_cols = [
    "Global_active_power",
    "Global_reactive_power",
    "Voltage",
    "Global_intensity",
    "Sub_metering_1",
    "Sub_metering_2",
    "Sub_metering_3"
]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

before_clean = len(df)

df = df.dropna(subset=["DATE_TIME", "Global_active_power"])

after_clean = len(df)
missing_removed = before_clean - after_clean

# Global_active_power kW cinsinden.
# Veri 1 dakikalik oldugu icin enerji kWh = kW / 60
df["CONSUMPTION_KWH_1MIN"] = df["Global_active_power"] / 60.0

df = df.set_index("DATE_TIME").sort_index()

print("15 dakikalik enerji tuketimi hesaplanıyor...")

consumption_15min = pd.DataFrame()
consumption_15min["CONSUMPTION_KWH"] = df["CONSUMPTION_KWH_1MIN"].resample("15min").sum()
consumption_15min["AVG_ACTIVE_POWER_KW"] = df["Global_active_power"].resample("15min").mean()
consumption_15min["AVG_VOLTAGE"] = df["Voltage"].resample("15min").mean()
consumption_15min["AVG_GLOBAL_INTENSITY"] = df["Global_intensity"].resample("15min").mean()
consumption_15min["SUB_METERING_1_SUM"] = df["Sub_metering_1"].resample("15min").sum()
consumption_15min["SUB_METERING_2_SUM"] = df["Sub_metering_2"].resample("15min").sum()
consumption_15min["SUB_METERING_3_SUM"] = df["Sub_metering_3"].resample("15min").sum()

consumption_15min = consumption_15min.reset_index()

# Tamamen bos veya sifir olan araliklari temizle
consumption_15min = consumption_15min.dropna(subset=["CONSUMPTION_KWH"])
consumption_15min = consumption_15min[consumption_15min["CONSUMPTION_KWH"] > 0]

consumption_15min["DATE"] = consumption_15min["DATE_TIME"].dt.strftime("%Y-%m-%d")
consumption_15min["HOUR"] = consumption_15min["DATE_TIME"].dt.hour
consumption_15min["MINUTE"] = consumption_15min["DATE_TIME"].dt.minute
consumption_15min["DAY_OF_WEEK"] = consumption_15min["DATE_TIME"].dt.dayofweek
consumption_15min["MONTH"] = consumption_15min["DATE_TIME"].dt.month
consumption_15min["YEAR"] = consumption_15min["DATE_TIME"].dt.year

output_csv = CONSUMPTION_DIR / "cleaned_uci_15min_consumption.csv"
summary_json = CONSUMPTION_DIR / "uci_consumption_preparation_summary.json"
summary_txt = FINAL_DIR / "uci_consumption_preparation_summary.txt"

consumption_15min.to_csv(output_csv, index=False, encoding="utf-8")

summary = {
    "raw_rows": int(raw_rows),
    "rows_after_cleaning": int(after_clean),
    "missing_removed": int(missing_removed),
    "consumption_15min_rows": int(len(consumption_15min)),
    "start_datetime": str(consumption_15min["DATE_TIME"].min()),
    "end_datetime": str(consumption_15min["DATE_TIME"].max()),
    "total_consumption_kwh": float(consumption_15min["CONSUMPTION_KWH"].sum()),
    "average_15min_consumption_kwh": float(consumption_15min["CONSUMPTION_KWH"].mean()),
    "max_15min_consumption_kwh": float(consumption_15min["CONSUMPTION_KWH"].max())
}

with summary_json.open("w", encoding="utf-8") as f:
    json.dump(summary, f, indent=4, ensure_ascii=False)

summary_text = f"""UCI GERCEK ELEKTRIK TUKETIM VERISI HAZIRLAMA OZETI
=================================================

Ham veri dosyasi:
household_power_consumption.txt

Ham satir sayisi:
{summary["raw_rows"]}

Temizlik sonrasi satir sayisi:
{summary["rows_after_cleaning"]}

Eksik/hatali oldugu icin cikarilan satir sayisi:
{summary["missing_removed"]}

Olusturulan 15 dakikalik tuketim veri satiri:
{summary["consumption_15min_rows"]}

Tarih araligi:
{summary["start_datetime"]} - {summary["end_datetime"]}

Toplam tuketim:
{summary["total_consumption_kwh"]:.3f} kWh

Ortalama 15 dakikalik tuketim:
{summary["average_15min_consumption_kwh"]:.6f} kWh

Maksimum 15 dakikalik tuketim:
{summary["max_15min_consumption_kwh"]:.6f} kWh

Bu veri seti, enerji yönetimi modülünde simüle tüketim yerine gerçek tüketim profili kaynağı olarak kullanılacaktır.
"""

summary_txt.write_text(summary_text, encoding="utf-8")

print("\nUCI tuketim verisi hazirlandi.")
print("Temiz 15 dk tuketim verisi:", output_csv)
print("Ozet JSON:", summary_json)
print("Ozet TXT:", summary_txt)

print("\nOzet:")
for key, value in summary.items():
    print(f"{key}: {value}")
