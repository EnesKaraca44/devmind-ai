# DevMind AI

Geliştiricinin kendi dokümanlarını (PDF, TXT, Markdown) indeksleyip kaynak göstererek soru-cevap yapabildiği, **local-first** bir RAG / Agent / MCP öğrenme projesi.
Yol haritası ve çalışma kuralları: [`DevMind_AI_Codex_Master_Prompt.md`](DevMind_AI_Codex_Master_Prompt.md).

## Durum

Sprint 1 (Foundation) tamam, Sprint 2 (Doküman yükleme) tamamlanmak üzere. Çalışan kısımlar:

- PostgreSQL 18 + pgvector (Docker), Alembic migration'ları
- FastAPI backend: koleksiyonlar ve doküman yükleme/listeleme/silme (PDF, TXT, Markdown)
- Next.js arayüzü: koleksiyon oluşturma, dosya yükleme, doküman listesi, silme

**Henüz yok:** chunking, embedding, arama, RAG, agent, MCP, kimlik doğrulama (Sprint 3 ve sonrası).

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

# 3) Veritabanı tablolarını oluştur (İLK KURULUMDA ve her yeni migration'dan sonra şart;
#    yapılmazsa tablo yokken API 500 döner)
docker compose exec api alembic upgrade head

# 4) Durumu gör
docker compose ps
```

| Servis | Adres | Not |
|---|---|---|
| Web | http://localhost:3001 | "Backend bağlı" yazmalı |
| API | http://localhost:8000/api/v1/health | `{"status":"ok","service":"devmind-backend"}` |
| API dokümanı | http://localhost:8000/docs | FastAPI'nin otomatik ürettiği sayfa |
| PostgreSQL | `localhost:5433` | Host'taki PostgreSQL'le çakışmasın diye 5433 |

Durdurmak için: `docker compose down` (veritabanı `devmind_pgdata`, yüklenen dosyalar `devmind_storage` volume'ünde kalır).
Her şeyi silmek için: `docker compose down -v` (**veritabanı ve yüklenen dosyalar geri alınamaz şekilde silinir**).

> Not: Web 3001'de çünkü bazı makinelerde 3000'i başka uygulamalar tutuyor.

## API (doküman yükleme)

| Metot | Adres | Açıklama |
|---|---|---|
| POST | `/api/v1/collections` | Koleksiyon oluştur (`{"name": "..."}`) |
| GET | `/api/v1/collections`, `/{id}` | Listele / getir |
| POST | `/api/v1/documents/upload` | Dosya yükle (form: `collection_id`, `file`). PDF, TXT, MD; en fazla 20 MB |
| GET | `/api/v1/documents?collection_id=` | Listele |
| GET / DELETE | `/api/v1/documents/{id}` | Getir / sil (kayıt ve dosya) |

Yükleme sonuçları: `201` başarılı, `400` geçersiz dosya, `404` koleksiyon yok, `409` aynı dosya zaten var, `413` çok büyük.
Okunamayan ama geçerli görünen dosya (ör. taranmış PDF) `201` ile kaydedilir ve `status: failed` + `error_message` taşır.

Ayarlar (ortam değişkeni): `MAX_UPLOAD_BYTES` (varsayılan 20 MB), `STORAGE_DIR` (varsayılan `storage`), `DATABASE_URL`, `CORS_ORIGINS`.

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
