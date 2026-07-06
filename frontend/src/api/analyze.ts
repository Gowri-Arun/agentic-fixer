import type { AnalyzeRequest, AnalyzeResponse } from "../types/audit";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function analyzePage(
  payload: AnalyzeRequest,
): Promise<AnalyzeResponse> {
  const response = await fetch(`${API_BASE_URL}/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    let detail = "Failed to analyze page.";

    try {
      const data = await response.json();
      detail = data.detail ?? detail;
    } catch {
      // Keep default error message.
    }

    throw new Error(detail);
  }

  return response.json();
}
