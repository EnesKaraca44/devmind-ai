import BackendStatus from "@/components/BackendStatus";

// Bu bir Server Component (varsayılan): sunucuda render edilir, tarayıcıya hazır HTML gider.
// İçindeki BackendStatus ise tarayıcıda çalışan bir Client Component.
export default function Home() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-4 p-8">
      <h1 className="text-3xl font-semibold">DevMind AI</h1>
      <BackendStatus />
    </main>
  );
}
