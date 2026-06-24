"use client";
import { useMemo, useState, useEffect } from "react";
import { PredictionTier, runAnalysis, fetchDraws, Draw } from "@/lib/api";
import PredictionCard from "@/components/PredictionCard";
import DrawTable from "@/components/DrawTable";
import { DRAW_TYPES, getNextDrawType } from "@/lib/drawTypes";

export default function PredictionsPage() {
  const [drawsList, setDrawsList] = useState<Draw[]>([]);
  const [selectedDraw, setSelectedDraw] = useState<Draw | null>(null);
  const [tiers, setTiers] = useState<PredictionTier[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const initialDrawType = useMemo(() => getNextDrawType(), []);
  const [drawType, setDrawType] = useState(initialDrawType);
  // Load recent draws for the chosen draw type
  useEffect(() => {
    const load = async () => {
      try {
        const data = await fetchDraws(100, drawType);
        setDrawsList(data);
        // default to first draw if any
        if (data.length) setSelectedDraw(data[0]);
      } catch (e) {
        console.error('Failed to fetch draws for dropdown', e);
      }
    };
    load();
  }, [drawType]);
  const [cached, setCached] = useState(false);

  const handleAnalyze = async () => {
    setLoading(true);
    setError("");
    setCached(false);
    try {
      const result = await runAnalysis(drawType);
      const parsed = JSON.parse(result.result);
      const tierList = Object.entries(parsed).map(([key, val]) => ({
        tier: key,
        picks: val as { numbers: number[]; bonus: number; probability: number }[],
      }));
      setTiers(tierList);
      setCached(result.cached || false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed. Check backend & GROQ_API_KEY.");
    }
    setLoading(false);
  };

  return (
    <main className="min-h-screen bg-grid">
      <div className="bg-gradient-radial pt-4 sm:pt-8 pb-8 sm:pb-16">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <h1 className="text-2xl sm:text-4xl font-bold tracking-tight mb-6 sm:mb-8">Predictions</h1>

          <div className="glass-card rounded-2xl p-4 sm:p-6 mb-6 sm:mb-8">
            <div className="flex flex-wrap items-center gap-3">
                <select
    value={drawType}
    onChange={(e) => setDrawType(e.target.value)}
    className="bg-gray-900 border border-gray-700/50 rounded-xl px-4 py-2.5 text-xs sm:text-sm text-gray-200 focus:outline-none focus:border-yellow-500/50 transition-colors flex-1 sm:flex-none min-w-[140px]"
>
                {DRAW_TYPES.map((dt) => (
                  <option key={dt.value} value={dt.value}>{dt.label}</option>
                ))}
              </select>
              <span className="text-[11px] sm:text-xs text-gray-400">Defaulted to the next draw in your local time.</span>
              <button
                onClick={handleAnalyze}
                disabled={loading}
                className="bg-gradient-to-r from-yellow-500 to-yellow-600 hover:from-yellow-400 hover:to-yellow-500 disabled:from-gray-700 disabled:to-gray-700 text-gray-950 font-semibold px-6 py-2.5 rounded-xl text-xs sm:text-sm transition-all duration-200 shadow-lg shadow-yellow-500/20 disabled:shadow-none w-full sm:w-auto"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="w-4 h-4 border-2 border-gray-950 border-t-transparent rounded-full animate-spin" />
                    Analyzing
                  </span>
                ) : "Run Analysis"}
              </button>
            </div>
          </div>

          {error && (
            <div className="mb-6 animate-fade-in">
              <span className="inline-flex items-center gap-1.5 bg-red-900/30 text-red-400 text-xs font-medium px-3 py-1.5 rounded-full border border-red-800/30">
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                {error}
              </span>
            </div>
          )}

          {cached && (
            <div className="mb-5 animate-fade-in">
              <span className="inline-flex items-center gap-1.5 bg-blue-900/30 text-blue-400 text-xs font-medium px-3 py-1.5 rounded-full border border-blue-800/30">
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                Cached result (refreshes every 3 days)
              </span>
            </div>
          )}

          {loading && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="tier-card rounded-2xl p-4 sm:p-6">
                  <div className="loading-shimmer h-5 w-24 rounded mb-4" />
                  <div className="space-y-2.5">
                    {[...Array(3)].map((_, j) => (
                      <div key={j} className="loading-shimmer h-10 rounded-xl" />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {tiers.length === 0 && !loading && !error && (
            <div className="text-center py-16">
              <div className="text-5xl mb-4 opacity-30">🎱</div>
              <p className="text-gray-500 text-sm sm:text-base">Select a draw type and click Run Analysis</p>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
            {tiers.map((tier, i) => (
              <PredictionCard key={tier.tier} tier={tier.tier} picks={tier.picks} rank={i} />
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}
