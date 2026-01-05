# SLIS Suptech (Flask + Celery + Redis + Postgres)

Project ini adalah aplikasi **Sanction List Intelligence Screening** dengan:
- **Web UI (Flask + Jinja templates)** untuk upload data, mulai screening, lihat hasil.
- **API** untuk upload batch transaksi, import sanctions, dan submit screening job.
- **Async worker (Celery)** untuk menjalankan screening di background.
- **Redis** sebagai broker/result backend Celery.
- **Postgres** sebagai database (contoh: Neon).

## Komponen yang harus jalan
1. **Postgres** (wajib) → lewat `DATABASE_URL`
2. **Redis** (wajib) → untuk Celery
3. **Web** (Flask) → service UI/API
4. **Worker** (Celery) → eksekusi job screening

> Catatan penting: repo ini **tidak** punya migrasi/Alembic. Untuk first run di DB baru, jalankan inisialisasi tabel via `scripts/init_db.py`.

## Konfigurasi Environment (.env)
Buat file `.env` (jangan di-commit) berdasarkan `.env.example`.
Minimal yang wajib:
- `DATABASE_URL` (Postgres connection string)
- `CELERY_BROKER_URL` dan `CELERY_RESULT_BACKEND` (Redis)

## First Run (inisialisasi schema DB)
Pastikan `DATABASE_URL` sudah benar, lalu:

```bash
python scripts/init_db.py
```

Ini akan membuat tabel-tabel SQLAlchemy di database.

## Menjalankan dengan Docker (CPU)
Ini mode paling gampang untuk publish ke server lain.

```bash
docker compose up -d --build
```

Akses UI:
- `http://localhost:5001/` (compose memetakan host 5001 → container 5000)

Cek kesehatan:
- `GET http://localhost:5001/` (UI)

Log:
```bash
docker compose logs -f web
docker compose logs -f worker
```

### Menjalankan dengan GPU (opsional)
Butuh NVIDIA GPU + NVIDIA Container Toolkit.

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build --force-recreate
```

`docker-compose.gpu.yml` akan set:
- `SLIS_MATCHER_BACKEND=cudf`
- `gpus: all`

Lihat juga [GPU_SETUP.md](GPU_SETUP.md).

## Menjalankan Lokal (tanpa Docker)
### 1) Install dependency
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Jalankan Redis
Paling gampang via Docker:
```bash
docker run --rm -p 6379:6379 redis:7-alpine
```

### 3) Set environment
```bash
set -a
source .env
set +a
```

### 4) Jalankan Web (Flask)
Opsi 1:
```bash
python run.py
```

Opsi 2 (lebih eksplisit):
```bash
flask --app run.py run --host 0.0.0.0 --port 5001
```

### 5) Jalankan Worker (Celery)
Di terminal lain:
```bash
celery -A slis.celery_app worker --loglevel=info
```

## Endpoint penting
- UI: `/`
- Upload transaksi (API): `POST /api/batches/transactions/upload-txt`
- Import sanctions (API): `POST /api/sanctions/import`
- Buat screening job (API): `POST /api/screening/jobs`
- Progress screening (API): `GET /api/screening/jobs/<job_id>/progress`
- Cancel screening (API): `POST /api/screening/jobs/<job_id>/cancel`
- Quick search bulk (API): `POST /api/screening/quick-search-bulk`

## Catatan seeding data sanctions
Untuk import sanctions, database harus punya minimal 1 baris di tabel `sanction_source` dengan:
- `code` (mis: `OFAC`, `UN`, dll)
- `column_mapping` (JSON) minimal berisi key `full_name` sesuai nama kolom di file.

Kalau belum ada, import akan error: `sanction_source with code '...' not found`.

## Catatan keamanan saat publish
- Jangan commit `.env` ke GitHub. Kalau pernah terlanjur ter-push, **rotate credential** (password/token DB) dan pertimbangkan membersihkan history git.
- Untuk produksi, sebaiknya tidak pakai `FLASK_DEBUG=1` dan jalankan web dengan `gunicorn` (dependency sudah ada di `requirements.txt`).
