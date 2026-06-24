import { getNextDrawType } from "@/lib/drawTypes";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || (typeof window !== "undefined" ? `${window.location.protocol}//${window.location.hostname}:8000` : "http://localhost:8000");

export interface Draw {
  id: number;
  draw_date: string;
  draw_type: string;
  n1: number;
  n2: number;
  n3: number;
  n4: number;
  n5: number;
  n6: number;
  bonus: number;
}

export interface PredictionPick {
  numbers: number[];
  bonus: number;
  probability: number;
}

export interface PredictionTier {
  tier: string;
  picks: PredictionPick[];
}

export async function fetchDraws(limit = 50, drawType?: string): Promise<Draw[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (drawType) params.set("draw_type", drawType);
  const res = await fetch(`${API_BASE}/api/draws?${params}`);
  if (!res.ok) throw new Error(`Failed to fetch draws: ${res.status}`);
  return res.json();
}

export async function triggerScrape(): Promise<{ message: string; draws_added: number }> {
  const res = await fetch(`${API_BASE}/api/scrape`, { method: "POST" });
  if (!res.ok) throw new Error(`Failed to scrape: ${res.status}`);
  return res.json();
}

export async function runAnalysis(drawType = getNextDrawType()): Promise<{ status: string; result: string; cached?: boolean }> {
  const res = await fetch(`${API_BASE}/api/analyze?draw_type=${drawType}`, { method: "POST" });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(typeof data.detail === "string" ? data.detail : `Failed to analyze: ${res.status}`);
  }
  return res.json();
}
