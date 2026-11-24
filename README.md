# DevMind AI

Geliştiricinin kendi dokümanlarını (PDF, TXT, Markdown) indeksleyip kaynak göstererek soru-cevap yapabildiği, **local-first** bir RAG / Agent / MCP öğrenme projesi.
Yol haritası ve çalışma kuralları: [`DevMind_AI_Codex_Master_Prompt.md`](DevMind_AI_Codex_Master_Prompt.md).

## Durum

Sprint 1 (Foundation) büyük ölçüde tamam. Çalışan kısımlar:

- PostgreSQL 18 + pgvector (Docker)
- FastAPI backend, tek endpoint: `GET /api/v1/health`
- Next.js frontend, backend'e istek atıp durumu gösteren tek sayfa

**Henüz yok:** doküman yükleme, chunking, embedding, arama, RAG, agent, MCP (Sprint 2 ve sonrası).

## Gereksinimler

- Docker Desktop (Compose dahil)
- Windows PowerShell için komutlar yazıldı

Geliştirme sırasında konteyner dışında çalıştırmak istersen ayrıca: Python 3.11, Node.js 22.

## Hızlı başlangıç (Docker)

```powershell
# 1) Ortam dosyasını oluştur ve POSTGRES_PASSWORD değerini kendin belirle
Copy-Item .env.example .env

# 2) Tüm servisleri derle ve başlat
docker compose up -d --build

# 3) Durumu gör
docker compose ps
```

| Servis | Adres | Not |
|---|---|---|
| Web | http://localhost:3001 | "Backend bağlı" yazmalı |
| API | http://localhost:8000/api/v1/health | `{"status":"ok","service":"devmind-backend"}` |
| API dokümanı | http://localhost:8000/docs | FastAPI'nin otomatik ürettiği sayfa |
| PostgreSQL | `localhost:5433` | Host'taki PostgreSQL'le çakışmasın diye 5433 |

Durdurmak için: `docker compose down` (veri `devmind_pgdata` volume'ünde kalır).
Veriyi de silmek için: `docker compose down -v` (**geri alınamaz**).

> Not: Web 3001'de çünkü bazı makinelerde 3000'i başka uygulamalar tutuyor.

## Testler

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
```

### Veritabanı şeması (migration)

Veritabanı çalışırken (`docker compose up -d`), `backend` klasöründe:

```powershell
. ..\scripts\dev-env.ps1                      # DATABASE_URL'i .env'den üretir (parola gösterilmez)
.\.venv\Scripts\alembic.exe upgrade head      # şemayı en son sürüme getirir
.\.venv\Scripts\alembic.exe current           # şu anki sürüm
.\.venv\Scripts\alembic.exe downgrade base    # her şeyi geri alır (tablolar silinir!)
.\.venv\Scripts\alembic.exe check             # modeller ile veritabanı arasında fark var mı?
```

`DATABASE_URL` tanımlıysa veritabanı entegrasyon testleri de çalışır (her test sonunda geri alınır, veri bırakmaz); tanımlı değilse atlanır.

> Bağlantıda `localhost` yerine `127.0.0.1` kullanılır: `localhost` önce IPv6'ya (`::1`) çözülür, Docker portu yalnızca IPv4'e açtığı için her bağlantı saniyelerce takılırdı.

### Frontend

```powershell
cd apps/web
npm ci
npm run lint
npm run build
```

## Klasör yapısı

```text
apps/web/        Next.js arayüzü
backend/         FastAPI uygulaması (app/) ve testleri (tests/)
docs/decisions/  Mimari karar kayıtları (ADR)
docker-compose.yml, .env.example
```

## Gizlilik ve güvenlik

- `.env` dosyaları Git'e girmez, yalnızca `.env.example` şablondur.
- Servisler yalnızca `127.0.0.1`'e açılır (yerel ağdan erişilemez).
- Kullanıcı dosyaları harici servislere gönderilmez (local-first).
