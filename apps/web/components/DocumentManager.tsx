"use client";

import { useEffect, useRef, useState } from "react";
import {
  ApiError,
  createCollection,
  deleteDocument,
  fetchCollections,
  fetchDocuments,
  uploadDocument,
  type Collection,
  type DocumentItem,
  type DocumentStatus,
} from "@/lib/api";

type Notice = { kind: "success" | "error"; text: string } | null;

const STATUS_LABEL: Record<DocumentStatus, string> = {
  pending: "Bekliyor",
  processing: "İşleniyor",
  ready: "Hazır",
  failed: "Okunamadı",
};

const STATUS_STYLE: Record<DocumentStatus, string> = {
  pending: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  processing: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200",
  ready: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  failed: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
};

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function errorText(error: unknown): string {
  return error instanceof ApiError ? error.message : "Beklenmeyen bir hata oluştu.";
}

export default function DocumentManager() {
  const [collections, setCollections] = useState<Collection[] | null>(null);
  const [selectedId, setSelectedId] = useState<string>("");
  // Listeyi HANGİ koleksiyon için yüklediğimizi de saklıyoruz: seçim değişince
  // eski koleksiyonun listesi yeni liste gelene kadar yanlışlıkla görünmesin.
  const [loaded, setLoaded] = useState<{
    collectionId: string;
    items: DocumentItem[];
  } | null>(null);
  const [newName, setNewName] = useState("");
  const [notice, setNotice] = useState<Notice>(null);
  const [busy, setBusy] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  // Sayfa açılınca koleksiyonları getir.
  useEffect(() => {
    fetchCollections()
      .then((items) => {
        setCollections(items);
        setSelectedId((current) => current || items[0]?.id || "");
      })
      .catch((error) => {
        setCollections([]);
        setNotice({ kind: "error", text: errorText(error) });
      });
  }, []);

  // Seçili koleksiyon değişince dokümanlarını getir.
  useEffect(() => {
    if (!selectedId) return;
    let cancelled = false; // hızlı seçim değişiminde eski cevap yenisini ezmesin
    fetchDocuments(selectedId)
      .then((items) => {
        if (!cancelled) setLoaded({ collectionId: selectedId, items });
      })
      .catch((error) => {
        if (!cancelled) setNotice({ kind: "error", text: errorText(error) });
      });
    return () => {
      cancelled = true;
    };
  }, [selectedId]);

  async function refreshDocuments() {
    const items = await fetchDocuments(selectedId);
    setLoaded({ collectionId: selectedId, items });
  }

  async function handleCreateCollection(event: React.FormEvent) {
    event.preventDefault();
    const name = newName.trim();
    if (!name) return;
    setBusy(true);
    try {
      const created = await createCollection(name);
      setCollections((current) => [created, ...(current ?? [])]);
      setSelectedId(created.id);
      setNewName("");
      setNotice({ kind: "success", text: `"${created.name}" koleksiyonu oluşturuldu.` });
    } catch (error) {
      setNotice({ kind: "error", text: errorText(error) });
    } finally {
      setBusy(false);
    }
  }

  async function handleUpload(event: React.FormEvent) {
    event.preventDefault();
    const file = fileInput.current?.files?.[0];
    if (!file || !selectedId) return;
    setBusy(true);
    setNotice(null);
    try {
      const document = await uploadDocument(selectedId, file);
      await refreshDocuments();
      setNotice(
        document.status === "failed"
          ? { kind: "error", text: `Yüklendi ama okunamadı: ${document.error_message}` }
          : { kind: "success", text: `"${document.filename}" yüklendi.` },
      );
      if (fileInput.current) fileInput.current.value = "";
    } catch (error) {
      setNotice({ kind: "error", text: errorText(error) });
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(item: DocumentItem) {
    if (!window.confirm(`"${item.filename}" silinsin mi? Bu işlem geri alınamaz.`)) return;
    setBusy(true);
    try {
      await deleteDocument(item.id);
      await refreshDocuments();
      setNotice({ kind: "success", text: `"${item.filename}" silindi.` });
    } catch (error) {
      setNotice({ kind: "error", text: errorText(error) });
    } finally {
      setBusy(false);
    }
  }

  const documents =
    loaded && loaded.collectionId === selectedId ? loaded.items : null;

  return (
    <section className="w-full max-w-2xl space-y-6">
      {notice && (
        <p
          role={notice.kind === "error" ? "alert" : "status"}
          data-testid="notice"
          className={
            notice.kind === "error"
              ? "rounded border border-red-300 bg-red-50 p-3 text-sm text-red-800 dark:border-red-800 dark:bg-red-950 dark:text-red-200"
              : "rounded border border-green-300 bg-green-50 p-3 text-sm text-green-800 dark:border-green-800 dark:bg-green-950 dark:text-green-200"
          }
        >
          {notice.text}
        </p>
      )}

      {/* 1) Koleksiyon seç / oluştur */}
      <div className="space-y-3 rounded border border-zinc-200 p-4 dark:border-zinc-800">
        <h2 className="font-medium">Koleksiyon</h2>
        {collections === null ? (
          <p className="text-sm text-zinc-500">Yükleniyor…</p>
        ) : collections.length > 0 ? (
          <select
            aria-label="Koleksiyon seç"
            value={selectedId}
            onChange={(event) => setSelectedId(event.target.value)}
            className="w-full rounded border border-zinc-300 bg-transparent p-2 dark:border-zinc-700"
          >
            {collections.map((collection) => (
              <option key={collection.id} value={collection.id}>
                {collection.name}
              </option>
            ))}
          </select>
        ) : (
          <p className="text-sm text-zinc-500">Henüz koleksiyon yok. Aşağıdan oluştur.</p>
        )}
        <form onSubmit={handleCreateCollection} className="flex gap-2">
          <input
            aria-label="Yeni koleksiyon adı"
            value={newName}
            onChange={(event) => setNewName(event.target.value)}
            maxLength={200}
            placeholder="Yeni koleksiyon adı"
            className="flex-1 rounded border border-zinc-300 bg-transparent p-2 dark:border-zinc-700"
          />
          <button
            type="submit"
            disabled={busy || !newName.trim()}
            className="rounded bg-zinc-900 px-4 py-2 text-white disabled:opacity-40 dark:bg-zinc-100 dark:text-zinc-900"
          >
            Oluştur
          </button>
        </form>
      </div>

      {/* 2) Dosya yükle */}
      {selectedId && (
        <form
          onSubmit={handleUpload}
          className="space-y-3 rounded border border-zinc-200 p-4 dark:border-zinc-800"
        >
          <h2 className="font-medium">Doküman yükle</h2>
          <input
            ref={fileInput}
            type="file"
            aria-label="Dosya seç"
            accept=".pdf,.txt,.md"
            className="block w-full text-sm"
          />
          <p className="text-xs text-zinc-500">PDF, TXT veya Markdown · en fazla 20 MB</p>
          <button
            type="submit"
            disabled={busy}
            className="rounded bg-zinc-900 px-4 py-2 text-white disabled:opacity-40 dark:bg-zinc-100 dark:text-zinc-900"
          >
            {busy ? "Çalışıyor…" : "Yükle"}
          </button>
        </form>
      )}

      {/* 3) Doküman listesi */}
      {selectedId && (
        <div className="space-y-3 rounded border border-zinc-200 p-4 dark:border-zinc-800">
          <h2 className="font-medium">Dokümanlar</h2>
          {documents === null ? (
            <p className="text-sm text-zinc-500">Yükleniyor…</p>
          ) : documents.length === 0 ? (
            <p className="text-sm text-zinc-500">Bu koleksiyonda henüz doküman yok.</p>
          ) : (
            <ul className="divide-y divide-zinc-200 dark:divide-zinc-800" data-testid="document-list">
              {documents.map((item) => (
                <li key={item.id} className="flex items-start justify-between gap-3 py-3">
                  <div className="min-w-0 space-y-1">
                    <p className="truncate font-medium">{item.filename}</p>
                    <p className="text-xs text-zinc-500">
                      {formatSize(item.file_size)}
                      {item.page_count !== null && ` · ${item.page_count} sayfa`}
                    </p>
                    {item.error_message && (
                      <p className="text-xs text-red-600 dark:text-red-400">
                        {item.error_message}
                      </p>
                    )}
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <span
                      className={`rounded px-2 py-0.5 text-xs ${STATUS_STYLE[item.status]}`}
                    >
                      {STATUS_LABEL[item.status]}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleDelete(item)}
                      disabled={busy}
                      className="text-sm text-red-600 hover:underline disabled:opacity-40 dark:text-red-400"
                    >
                      Sil
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}
