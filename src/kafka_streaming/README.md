# IoT Terminal Kodları

Bu klasörde ESP32 cihazlarından gelen verilerin bilgisayar tarafında izlenmesi, CSV dosyalarından JupyterHub'a yüklenmesi ve stream biçiminde gönderilmesi için kullanılan Python kodları yer alır.

Dosyalar:
- `upload_csv_to_jupyter.py`: CSV dosyalarını JupyterHub Contents API ile yükler.
- `pc_csv_stream_uploader.py`: CSV dosyalarını sürekli izler, yeni satırları JSONL paketleri halinde JupyterHub `incoming/` klasörüne gönderir.

Gizli bilgiler `.env` dosyasında tutulmalıdır. GitHub'a gerçek token, kullanıcı bilgisi veya okul bağlantı bilgisi yüklenmemelidir.
