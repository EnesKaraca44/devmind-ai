// Backend adresi tek yerde durur. NEXT_PUBLIC_ önekli değişkenler tarayıcıya gömülür,
// bu yüzden buraya asla secret/parola koyma.
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type HealthResponse = {
  status: string;
  service: string;
};

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/health`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Backend ${response.status} döndü`);
  }
  return response.json();
}
