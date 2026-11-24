# ADR-001: Modüler monolith ile başla

**Durum:** Kabul edildi
**Tarih:** 2026-11-24

## Bağlam

DevMind AI birkaç parçadan oluşacak: doküman işleme, embedding, arama, RAG, agent, MCP.
Parçaları baştan ayrı servislere (mikroservis) bölmek mümkün, ama proje tek geliştiricili ve öncelik öğrenmek.

## Karar

Backend **tek bir uygulama** (monolith) olarak yazılır, içi **modüllere** ayrılır
(`api`, `core`; ileride `ingestion`, `embeddings`, `retrieval`, `rag`, `agents`, `mcp`).
Frontend ayrı bir uygulamadır (`apps/web`); veritabanı ayrı bir konteynerdir.

## Alternatifler

| Seçenek | Artı | Eksi |
|---|---|---|
| **Modüler monolith (seçildi)** | Tek yerde çalıştır/test et, hata ayıklaması kolay, ağ gecikmesi ve servisler arası sözleşme yükü yok | Her şey aynı süreçte; bir modül yük bindirirse hepsi etkilenir |
| Mikroservisler | Parçalar bağımsız ölçeklenir ve dağıtılır | Ağ, dağıtım, izleme karmaşıklığı; tek kişilik bir proje için aşırı yük; öğrenme odağını dağıtır |

## Sonuçlar

- Modüller arası bağımlılığı bilinçli tutacağız: bir modül diğerinin iç ayrıntısına dokunmaz, tanımlı bir arayüzle konuşur. Bu sınır, ileride bir modülü ayrı servise çıkarmayı mümkün kılar.
- Henüz var olmayan modül klasörlerini önceden oluşturmuyoruz; gerçek ihtiyaç doğunca ekliyoruz.
- Karar ilerideki ölçek ihtiyacına göre yeniden değerlendirilebilir.
