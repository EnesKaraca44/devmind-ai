import BackendStatus from "@/components/BackendStatus";
import DocumentManager from "@/components/DocumentManager";

// Bu bir Server Component (varsayılan): sunucuda render edilir, tarayıcıya hazır HTML gider.
// İçindeki BackendStatus ve DocumentManager ise tarayıcıda çalışan Client Component'ler.
export default function Home() {
  return (
    <main className="flex flex-1 flex-col items-center gap-6 p-8">
      <h1 className="text-3xl font-semibold">DevMind AI</h1>
      <BackendStatus />
      <DocumentManager />
    </main>
  );
}
