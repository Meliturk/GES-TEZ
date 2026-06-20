from pathlib import Path
from urllib.request import Request, urlopen
import zipfile
import shutil

PROJECT_DIR = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_DIR / "consumption_data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

zip_path = OUT_DIR / "household_power_consumption.zip"
txt_path = OUT_DIR / "household_power_consumption.txt"

urls = [
    "https://archive.ics.uci.edu/static/public/235/individual+household+electric+power+consumption.zip",
    "https://archive.ics.uci.edu/ml/machine-learning-databases/00235/household_power_consumption.zip"
]

if not txt_path.exists():
    downloaded = False

    for url in urls:
        try:
            print("Indirme deneniyor:", url)
            request = Request(url, headers={"User-Agent": "GES-AI-Project/1.0"})

            with urlopen(request, timeout=180) as response:
                with zip_path.open("wb") as f:
                    shutil.copyfileobj(response, f)

            print("ZIP indirildi:", zip_path)
            downloaded = True
            break

        except Exception as e:
            print("Bu URL ile indirilemedi:", e)

    if not downloaded:
        raise RuntimeError("UCI veri seti indirilemedi. Internet baglantisini veya UCI erisimini kontrol et.")

    print("ZIP aciliyor...")

    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(OUT_DIR)

else:
    print("Veri dosyasi zaten var:", txt_path)

if not txt_path.exists():
    raise FileNotFoundError("household_power_consumption.txt bulunamadi.")

print("Satir sayisi hesaplaniyor...")
with txt_path.open("r", encoding="latin1") as f:
    line_count = sum(1 for _ in f)

data_rows = line_count - 1

info_path = OUT_DIR / "uci_consumption_dataset_info.txt"

info_text = f"""UCI INDIVIDUAL HOUSEHOLD ELECTRIC POWER CONSUMPTION DATASET
=========================================================

Kaynak:
UCI Machine Learning Repository

Dosya:
household_power_consumption.txt

Ham veri satir sayisi:
{data_rows}

Aciklama:
Bu veri seti bir hanenin elektrik tuketimini 1 dakikalik olcumlerle kaydetmektedir.
Projede bu veri seti, akilli enerji yonetimi modulu icin gercek tuketim profili kaynagi olarak kullanilacaktir.

Not:
Bu tuketim verisi Kaggle GES santralinin kendi tuketim verisi degildir.
Bu nedenle veri, hibrit enerji yonetimi simülasyonunda gercek tuketim profili olarak kullanilacaktir.
"""

info_path.write_text(info_text, encoding="utf-8")

print("\nUCI tuketim veri seti hazir.")
print("TXT:", txt_path)
print("Bilgi dosyasi:", info_path)
print("Ham veri satiri:", data_rows)
