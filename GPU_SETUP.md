# GPU Hybrid Matching (cuDF + RapidFuzz)

Konsep yang dipakai:
- GPU (cuDF) untuk filtering kandidat cepat (buang yang jelas bukan match)
- CPU (RapidFuzz) untuk scoring fuzzy yang presisi

## 1) Prasyarat
- NVIDIA GPU + driver
- NVIDIA Container Toolkit terpasang (agar Docker bisa akses GPU)

## 2) Jalankan dengan GPU (Docker Compose override)
Gunakan override compose ini:

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build --force-recreate
```

`docker-compose.gpu.yml` akan:
- meminta akses GPU (`device_requests`)
- set `SLIS_MATCHER_BACKEND=cudf`

## 3) Install cuDF di image
Repo ini *tidak* memaksa install cuDF di `requirements.txt` karena wheel-nya spesifik CUDA/driver.

Opsi cepat:
- Tambahkan install cuDF di `Dockerfile` dengan extra index NVIDIA, misalnya (contoh untuk CUDA 12):

```bash
pip install --extra-index-url https://pypi.nvidia.com cudf-cu12
```

Catatan: paket & versi cuDF harus cocok dengan versi CUDA dan driver di host.
Jika muncul error seperti `cudaErrorInsufficientDriver`, coba pin versi cuDF yang lebih rendah (mis. `cudf-cu12==25.10.0`) atau upgrade NVIDIA driver di host.

## 4) Fallback tanpa GPU
Kalau cuDF tidak terpasang, sistem otomatis fallback ke backend `pandas` (tetap 2-stage, hanya filtering di CPU).

Untuk memaksa CPU:

```bash
export SLIS_MATCHER_BACKEND=pandas
```
