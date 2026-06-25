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

export interface AnalysisResponse {
  generated_at: string;
  draw_type: string;
  tiers: PredictionTier[];
  analysis: Record<string, unknown>;
}

export async function runAnalysis(drawType = getNextDrawType(), method = "frequency"): Promise<AnalysisResponse> {
  const res = await fetch(`${API_BASE}/api/analyze?draw_type=${drawType}&method=${method}`, { method: "POST" });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(typeof data.detail === "string" ? data.detail : `Failed to analyze: ${res.status}`);
  }
  return res.json();
}

export interface EvaluateResult {
  draw_type: string;
  test_count: number;
  ranking: string[];
  methods: Record<string, {
    avg_main_hits: number;
    bonus_hit_rate: number;
    any_match_rate: number;
    tests: number;
    tiers: Record<string, {
      avg_main_hits: number;
      bonus_hit_rate: number;
      any_match_rate: number;
      tests: number;
    }>;
  }>;
}

export async function evaluateMethods(drawType = "lunchtime"): Promise<EvaluateResult> {
  const res = await fetch(`${API_BASE}/api/evaluate?draw_type=${drawType}`);
  if (!res.ok) throw new Error(`Failed to evaluate: ${res.status}`);
  return res.json();
}
