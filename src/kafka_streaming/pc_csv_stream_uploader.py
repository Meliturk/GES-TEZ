import os
import json
import time
import pandas as pd
import requests
from datetime import datetime

# =========================================================
# JUPYTERHUB AYARLARI
# =========================================================

JUPYTER_BASE_URL = os.getenv("JUPYTER_BASE_URL", "http://YOUR_JUPYTERHUB_URL")
JUPYTER_USER = os.getenv("JUPYTER_USER", "YOUR_JUPYTER_USER")

# Buraya JupyterHub notebook içinde aldığın güncel tokenı yaz
JUPYTER_TOKEN = os.getenv("JUPYTER_TOKEN", "YOUR_JUPYTER_TOKEN")

TARGET_DIR = "incoming"

# =========================================================
# CSV / STREAM AYARLARI
# =========================================================

FILES = {
    "env": {
        "csv": "wifi_ortam_verileri.csv",
        "prefix": "env_stream",
        "device_type": "env"
    },
    "panel": {
        "csv": "wifi_panel_verileri.csv",
        "prefix": "panel_stream",
        "device_type": "panel"
    },
    "combined": {
        "csv": "wifi_ges_birlesik_veri.csv",
        "prefix": "combined_stream",
        "device_type": "combined"
    }
}

CHECKPOINT_FILE = "pc_stream_checkpoint_all.json"

# Her seferde en fazla kaç yeni satır paketlenecek
BATCH_SIZE = 200

# Kaç saniyede bir CSV kontrol edilecek
SLEEP_SECONDS = 5

# Upload deneme sayısı
MAX_UPLOAD_RETRY = 3

# HTTP timeout
HTTP_TIMEOUT = 30


# =========================================================
# Yardımcı Fonksiyonlar
# =========================================================

def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_checkpoint():
    if not os.path.exists(CHECKPOINT_FILE):
        checkpoint = {
            "files": {},
            "batch_no": 0
        }

        for stream_type, cfg in FILES.items():
            checkpoint["files"][cfg["csv"]] = 0

        save_checkpoint(checkpoint)
        return checkpoint

    try:
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            checkpoint = json.load(f)

        if "files" not in checkpoint:
            checkpoint["files"] = {}

        if "batch_no" not in checkpoint:
            checkpoint["batch_no"] = 0

        for stream_type, cfg in FILES.items():
            if cfg["csv"] not in checkpoint["files"]:
                checkpoint["files"][cfg["csv"]] = 0

        save_checkpoint(checkpoint)
        return checkpoint

    except Exception as e:
        print("[CHECKPOINT HATA]")
        print("Checkpoint okunamadı:", e)
        print("Bozuk checkpoint dosyasını yedekleyip yenisini oluşturuyorum.")

        backup_name = f"{CHECKPOINT_FILE}.broken_{int(time.time())}"
        try:
            os.rename(CHECKPOINT_FILE, backup_name)
            print("Bozuk checkpoint yedeklendi:", backup_name)
        except Exception:
            pass

        checkpoint = {
            "files": {},
            "batch_no": 0
        }

        for stream_type, cfg in FILES.items():
            checkpoint["files"][cfg["csv"]] = 0

        save_checkpoint(checkpoint)
        return checkpoint


def save_checkpoint(checkpoint):
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, ensure_ascii=False, indent=2)


def make_session():
    session = requests.Session()

    session.headers.update({
        "Authorization": f"token {JUPYTER_TOKEN}",
        "Content-Type": "application/json"
    })

    return session


def api_url(path):
    clean_path = path.strip("/")
    return f"{JUPYTER_BASE_URL}/user/{JUPYTER_USER}/api/contents/{clean_path}"


def status_url():
    return f"{JUPYTER_BASE_URL}/user/{JUPYTER_USER}/api/status"


def check_jupyter_connection(session):
    try:
        r = session.get(status_url(), timeout=HTTP_TIMEOUT)

        if r.status_code == 200:
            return True

        print("[JUPYTER BAGLANTI UYARISI]")
        print("Status:", r.status_code)
        print("Cevap:", r.text[:300])
        return False

    except Exception as e:
        print("[JUPYTER BAGLANTI HATASI]")
        print(e)
        return False


def refresh_xsrf(session):
    """
    JupyterHub bazen PUT işlemleri için _xsrf ister.
    Bu fonksiyon önce /api/status çağırıp cookie içinden _xsrf alır.
    """
    try:
        session.get(status_url(), timeout=HTTP_TIMEOUT)

        xsrf_token = session.cookies.get("_xsrf")

        if xsrf_token:
            session.headers.update({
                "X-XSRFToken": xsrf_token
            })

        return xsrf_token

    except Exception as e:
        print("[XSRF ALMA HATASI]")
        print(e)
        return None


def ensure_remote_dir(session, dir_name):
    """
    Jupyter tarafında incoming klasörü yoksa oluşturur.
    Varsa dokunmaz.
    """
    url = api_url(dir_name)

    try:
        r = session.get(url, timeout=HTTP_TIMEOUT)

        if r.status_code == 200:
            return True

        payload = {
            "type": "directory"
        }

        xsrf_token = refresh_xsrf(session)
        put_url = url

        if xsrf_token:
            put_url = f"{url}?_xsrf={xsrf_token}"

        r = session.put(
            put_url,
            data=json.dumps(payload),
            timeout=HTTP_TIMEOUT
        )

        if r.status_code in [200, 201]:
            print(f"[OK] Jupyter klasörü hazır: {dir_name}")
            return True

        print("[KLASOR OLUSTURMA HATA]")
        print("Status:", r.status_code)
        print("Cevap:", r.text[:500])
        return False

    except Exception as e:
        print("[KLASOR KONTROL HATA]")
        print(e)
        return False


def upload_text_file(session, jupyter_path, content):
    """
    Jupyter Contents API ile text dosyası yükler.
    Hata olursa False döner.
    Checkpoint sadece True durumunda ilerletilecek.
    """
    url = api_url(jupyter_path)

    payload = {
        "type": "file",
        "format": "text",
        "content": content
    }

    for attempt in range(1, MAX_UPLOAD_RETRY + 1):
        try:
            xsrf_token = refresh_xsrf(session)

            put_url = url
            if xsrf_token:
                put_url = f"{url}?_xsrf={xsrf_token}"

            r = session.put(
                put_url,
                data=json.dumps(payload),
                timeout=HTTP_TIMEOUT
            )

            if r.status_code in [200, 201]:
                return True

            print("[UPLOAD HATA]")
            print("Deneme:", attempt, "/", MAX_UPLOAD_RETRY)
            print("Status:", r.status_code)
            print("Cevap:", r.text[:500])

            # 403 geldiyse XSRF/token tekrar denensin
            time.sleep(2)

        except requests.exceptions.ConnectTimeout as e:
            print("[UPLOAD BAGLANTI TIMEOUT]")
            print("Deneme:", attempt, "/", MAX_UPLOAD_RETRY)
            print(e)
            time.sleep(5)

        except requests.exceptions.ReadTimeout as e:
            print("[UPLOAD OKUMA TIMEOUT]")
            print("Deneme:", attempt, "/", MAX_UPLOAD_RETRY)
            print(e)
            time.sleep(5)

        except requests.exceptions.ConnectionError as e:
            print("[UPLOAD BAGLANTI HATASI]")
            print("Deneme:", attempt, "/", MAX_UPLOAD_RETRY)
            print(e)
            time.sleep(5)

        except Exception as e:
            print("[UPLOAD GENEL HATA]")
            print("Deneme:", attempt, "/", MAX_UPLOAD_RETRY)
            print(e)
            time.sleep(5)

    return False


def dataframe_rows_to_jsonl(df, stream_type, cfg, start_index, end_index):
    """
    CSV satırlarını JSONL string'e çevirir.
    start_index dahil, end_index hariç.
    """
    lines = []

    part = df.iloc[start_index:end_index].copy()

    for row_index, row in part.iterrows():
        msg = {
            "source": "pc_csv_stream",
            "stream_type": stream_type,
            "device_type": cfg["device_type"],
            "row_index": int(row_index),
            "stream_sent_at": now_text()
        }

        for col in part.columns:
            value = row[col]

            if pd.isna(value):
                msg[col] = None
            else:
                # Pandas/numpy tiplerini JSON uyumlu hale getir
                if hasattr(value, "item"):
                    value = value.item()
                msg[col] = value

        lines.append(json.dumps(msg, ensure_ascii=False))

    return "\n".join(lines) + "\n"


def process_one_file(session, stream_type, cfg, checkpoint):
    csv_file = cfg["csv"]

    if not os.path.exists(csv_file):
        print(f"[{now_text()}] [{stream_type}] CSV bulunamadı: {csv_file}")
        return

    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        print(f"[{now_text()}] [{stream_type}] CSV okunamadı:", e)
        return

    total_rows = len(df)
    last_sent = int(checkpoint["files"].get(csv_file, 0))

    if total_rows <= last_sent:
        print(f"[{now_text()}] [{stream_type}] Yeni satır yok. Toplam: {total_rows}, son gönderilen: {last_sent}")
        return

    end_index = min(last_sent + BATCH_SIZE, total_rows)

    checkpoint["batch_no"] = int(checkpoint.get("batch_no", 0)) + 1
    batch_no = checkpoint["batch_no"]

    file_name = f"{cfg['prefix']}_{batch_no:08d}_{last_sent}_{end_index}.jsonl"
    jupyter_path = f"{TARGET_DIR}/{file_name}"

    content = dataframe_rows_to_jsonl(
        df=df,
        stream_type=stream_type,
        cfg=cfg,
        start_index=last_sent,
        end_index=end_index
    )

    ok = upload_text_file(session, jupyter_path, content)

    if ok:
        checkpoint["files"][csv_file] = end_index
        save_checkpoint(checkpoint)

        print(f"[{now_text()}] [OK] {jupyter_path} yuklendi. Satir: {last_sent} -> {end_index}")

    else:
        # Batch no artmış olabilir, bunu da kaydedelim ama row checkpoint ilerlemesin.
        save_checkpoint(checkpoint)
        print(f"[{now_text()}] [{stream_type}] Upload basarisiz. Checkpoint ilerletilmedi.")


# =========================================================
# Ana Döngü
# =========================================================

def main():
    print("PC CSV Stream Uploader basladi.")
    print("3 CSV izleniyor:")

    for stream_type, cfg in FILES.items():
        print(f"- {cfg['csv']} -> {stream_type}")

    print("JupyterHub:", JUPYTER_BASE_URL)
    print("Kullanıcı:", JUPYTER_USER)
    print("Hedef klasor:", TARGET_DIR + "/")
    print("--------------------------------")

    session = make_session()

    if not check_jupyter_connection(session):
        print("JupyterHub'a şu an erişilemiyor.")
        print("Kontrol et:")
        print("1. VPN açık mı?")
        print("2. Tarayıcıdan JupyterHub açılıyor mu?")
        print("3. URL doğru mu? ->", JUPYTER_BASE_URL)
        print("Uploader kapanmıyor, 10 saniyede bir tekrar deneyecek.")

    while True:
        try:
            # Bağlantı yoksa bekle, checkpoint oynatma
            if not check_jupyter_connection(session):
                print(f"[{now_text()}] JupyterHub erişilemiyor. 10 saniye sonra tekrar denenecek.")
                time.sleep(10)
                continue

            if not ensure_remote_dir(session, TARGET_DIR):
                print(f"[{now_text()}] incoming klasörü hazırlanamadı. 10 saniye sonra tekrar denenecek.")
                time.sleep(10)
                continue

            checkpoint = load_checkpoint()

            for stream_type, cfg in FILES.items():
                process_one_file(session, stream_type, cfg, checkpoint)

            time.sleep(SLEEP_SECONDS)

        except KeyboardInterrupt:
            print("Uploader durduruldu.")
            break

        except Exception as e:
            print(f"[{now_text()}] HATA:", e)
            time.sleep(10)


if __name__ == "__main__":
    main()