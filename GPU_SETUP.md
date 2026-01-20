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

Alternatif yang lebih rapi: pakai file [requirements.gpu.txt](requirements.gpu.txt):

```bash
pip install -r requirements.txt
pip install -r requirements.gpu.txt
```

Catatan: paket & versi cuDF harus cocok dengan versi CUDA dan driver di host.
Jika muncul error seperti `cudaErrorInsufficientDriver`, coba pin versi cuDF yang lebih rendah (mis. `cudf-cu12==25.10.0`) atau upgrade NVIDIA driver di host.

## 4) Fallback tanpa GPU
Kalau cuDF tidak terpasang, sistem otomatis fallback ke backend `pandas` (tetap 2-stage, hanya filtering di CPU).

Untuk memaksa CPU:

```bash
export SLIS_MATCHER_BACKEND=pandas
```

## 5) Local dev pakai Conda (disarankan untuk GPU)
Kalau kamu memang targetnya GPU cuDF, paling aman pakai **conda env** (mis. `slis-suptech-py310`) dan **jangan** barengin dengan venv `env`.

Gejala salah setup yang sering terjadi: prompt jadi dua env sekaligus, mis. `(slis-suptech-py310) (env)`.
Itu artinya kamu mengaktifkan conda di atas venv (atau sebaliknya) dan Python/pip jadi campur.

Langkah yang aman:

1) Buka terminal baru (paling gampang), atau matikan venv dulu:

```bash
deactivate  # kalau sedang aktif venv
```

2) Aktifkan conda env:

```bash
conda activate slis-suptech-py310
python -V
```

3) Install dependency app:

```bash
pip install -r requirements.txt
```

4) Install cuDF (pilih salah satu):

- Opsi A (pip wheel, CUDA 12):

```bash
pip install -r requirements.gpu.txt
```

- Opsi B (conda, biasanya lebih stabil untuk cuDF):

```bash
# contoh umum (sesuaikan versi cudf/cuda dengan environment kamu)
conda install -c rapidsai -c conda-forge -c nvidia cudf
```

5) Paksa pakai GPU:

```bash
export SLIS_MATCHER_BACKEND=cudf
```
