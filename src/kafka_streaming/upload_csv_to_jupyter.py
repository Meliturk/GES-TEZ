import requests
import base64
import os
from datetime import datetime

# =====================
# JupyterHub Bilgileri
# =====================

JUPYTER_BASE_URL = os.getenv("JUPYTER_BASE_URL", "http://YOUR_JUPYTERHUB_URL")
JUPYTER_USER = os.getenv("JUPYTER_USER", "YOUR_JUPYTER_USER")

# Buraya JupyterHub içinden aldığın token'ı yaz
JUPYTER_TOKEN = os.getenv("JUPYTER_TOKEN", "YOUR_JUPYTER_TOKEN")

# =====================
# Yüklenecek CSV dosyaları
# =====================

CSV_FILES = [
    "wifi_ortam_verileri.csv",
    "wifi_panel_verileri.csv",
    "wifi_ges_birlesik_veri.csv"
]


def upload_file_to_jupyter(local_file_path):
    if not os.path.exists(local_file_path):
        print(f"[YOK] Dosya bulunamadı: {local_file_path}")
        return False

    file_name = os.path.basename(local_file_path)

    api_url = f"{JUPYTER_BASE_URL}/user/{JUPYTER_USER}/api/contents/{file_name}"

    headers = {
        "Authorization": f"token {JUPYTER_TOKEN}"
    }

    with open(local_file_path, "rb") as f:
        file_content = f.read()

    encoded_content = base64.b64encode(file_content).decode("utf-8")

    payload = {
        "content": encoded_content,
        "format": "base64",
        "type": "file"
    }

    response = requests.put(api_url, headers=headers, json=payload, timeout=30)

    if response.status_code in [200, 201]:
        print(f"[OK] {file_name} JupyterHub'a yüklendi/güncellendi.")
        return True
    else:
        print(f"[HATA] {file_name} yüklenemedi.")
        print("Status:", response.status_code)
        print("Cevap:", response.text[:500])
        return False


def main():
    print("CSV -> JupyterHub otomatik upload basladi.")
    print("Zaman:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("--------------------------------")

    success_count = 0

    for csv_file in CSV_FILES:
        ok = upload_file_to_jupyter(csv_file)

        if ok:
            success_count += 1

    print("--------------------------------")
    print("Islem tamamlandi.")
    print(f"Basarili yuklenen dosya sayisi: {success_count}/{len(CSV_FILES)}")


if __name__ == "__main__":
    main()