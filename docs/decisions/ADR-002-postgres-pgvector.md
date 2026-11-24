# ADR-002: Veri ve vektörler için PostgreSQL + pgvector

**Durum:** Kabul edildi
**Tarih:** 2026-11-24

## Bağlam

Uygulama iki tür veri tutacak:

1. Klasik veri: kullanıcılar, koleksiyonlar, dokümanlar, sohbetler (ilişkisel).
2. Vektörler: her metin parçasının (chunk) embedding'i; "anlamca en yakın parçaları bul" sorgusu için.

## Karar

İkisini de **tek bir PostgreSQL** içinde tutarız; vektörler için **pgvector** eklentisi kullanılır.
Geliştirmede `pgvector/pgvector:pg18` Docker imajı çalıştırılır (doğrulanan sürümler: PostgreSQL 18.7, pgvector 0.8.7).

## Alternatifler

| Seçenek | Artı | Eksi |
|---|---|---|
| **PostgreSQL + pgvector (seçildi)** | Tek veritabanı, tek yedek, tek bağlantı; vektör ve ilişkisel veriyi aynı sorguda birleştirebilme (ör. "yalnızca bu koleksiyondaki parçalar"); SQL bilgin doğrudan işe yarar | Çok büyük ölçekte özel vektör veritabanları kadar hızlı olmayabilir |
| Ayrı vektör veritabanı (ör. Qdrant, Chroma) | Vektör aramaya özel özellikler | İkinci bir sistem: ayrı yedekleme, iki veri arasında tutarlılık sorunu, kullanıcı yetkisini iki yerde uygulama |
| Windows'a kurulu PostgreSQL'e pgvector'ü elle kurmak | Docker gerekmez | Windows'ta derleme/kurulum zahmetli; ortam taşınabilir olmaz |

## Sonuçlar

- Embedding boyutu koda sabitlenmez; seçilen modelin gerçek boyutu doğrulanıp şemaya o zaman yazılır (Sprint 4).
- Embedding modeli adı ve boyutu her kayıtla birlikte tutulacak; farklı embedding uzayları karıştırılmayacak.
- Şema Alembic migration'larıyla yönetilecek.
- Host'ta PostgreSQL 18 zaten 5432'yi kullandığı için konteyner `127.0.0.1:5433`'e açılır.
