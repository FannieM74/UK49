"use client";
import { useEffect, useState } from "react";
import { EvaluateResult, evaluateMethods } from "@/lib/api";
import { DRAW_TYPES } from "@/lib/drawTypes";

const METHOD_LABELS: Record<string, string> = {
  frequency: "Frequency",
  weighted_recent: "Weighted Recent",
  delta: "Delta Analysis",
  pair: "Pair Frequency",
  cold_recovery: "Cold Recovery",
  sum_targeting: "Sum Targeting",
  ensemble: "Ensemble",
};

function Bar({ value, max, color }: { value: number; max: number; color: string }) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
      <div
        className={`h-full rounded-full transition-all duration-700 ${color}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

export default function SuccessPage() {
  const [result, setResult] = useState<EvaluateResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [drawType, setDrawType] = useState("lunchtime");

  useEffect(() => {
    setLoading(true);
    setError("");
    evaluateMethods(drawType)
      .then(setResult)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [drawType]);

  const maxMain = result
    ? Math.max(...Object.values(result.methods).map((m) => m.avg_main_hits))
    : 1;
  const maxBonus = result
    ? Math.max(...Object.values(result.methods).map((m) => m.bonus_hit_rate))
    : 1;
  const maxAny = result
    ? Math.max(...Object.values(result.methods).map((m) => m.any_match_rate))
    : 1;

  const tierKeys = ["2+bonus", "3+bonus", "4+bonus", "5+bonus", "6+bonus"];

  return (
    <main className="min-h-screen bg-grid">
      <div className="bg-gradient-radial pt-4 sm:pt-8 pb-8 sm:pb-16">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-6 sm:mb-8">
            <h1 className="text-2xl sm:text-4xl font-bold tracking-tight">Success Rate</h1>
            <select
              value={drawType}
              onChange={(e) => setDrawType(e.target.value)}
              className="bg-gray-900 border border-gray-700/50 rounded-xl px-4 py-2.5 text-xs sm:text-sm text-gray-200 focus:outline-none focus:border-yellow-500/50 transition-colors min-w-[140px]"
            >
              {DRAW_TYPES.map((dt) => (
                <option key={dt.value} value={dt.value}>{dt.label}</option>
              ))}
            </select>
          </div>

          {loading && (
            <div className="space-y-4">
              {[...Array(7)].map((_, i) => (
                <div key={i} className="glass-card rounded-2xl p-5">
                  <div className="loading-shimmer h-5 w-32 rounded mb-3" />
                  <div className="loading-shimmer h-3 rounded-full mb-2" />
                  <div className="loading-shimmer h-3 rounded-full w-3/4" />
                </div>
              ))}
            </div>
          )}

          {error && (
            <div className="text-center py-16">
              <p className="text-red-400 text-sm">{error}</p>
              {error.includes("requires_scrape") && (
                <p className="text-gray-500 text-xs mt-2">Run Update on the Dashboard first, then come back.</p>
              )}
            </div>
          )}

          {result && (
            <>
              <div className="glass-card rounded-2xl p-5 sm:p-7 mb-6">
                <h2 className="text-base sm:text-xl font-semibold mb-2 flex items-center gap-2">
                  <span className="w-1.5 h-5 bg-yellow-400 rounded-full" />
                  Overall Ranking
                </h2>
                <p className="text-xs text-gray-500 mb-5">
                  Backtested over {result.test_count} draws — {METHOD_LABELS[drawType] || drawType}
                </p>
                <div className="space-y-4">
                  {result.ranking.map((name, rank) => {
                    const m = result.methods[name];
                    return (
                      <div key={name} className="flex items-center gap-3 sm:gap-4">
                        <span className="text-lg sm:text-2xl font-bold text-gray-600 w-6 sm:w-8 text-right shrink-0">
                          {rank + 1}
                        </span>
                        <div className="flex-1 min-w-0">
                          <div className="flex flex-wrap items-baseline justify-between gap-1 mb-1">
                            <span className="text-xs sm:text-sm font-semibold text-gray-200 truncate">
                              {METHOD_LABELS[name] || name}
                            </span>
                            <span className="text-[10px] sm:text-xs text-gray-500">
                              {m.avg_main_hits} main · {m.bonus_hit_rate}% bonus
                            </span>
                          </div>
                          <div className="flex items-center gap-2 sm:gap-3">
                            <div className="flex-1">
                              <Bar value={m.avg_main_hits} max={maxMain} color="bg-gradient-to-r from-yellow-500 to-yellow-400" />
                            </div>
                            <span className="text-[10px] sm:text-xs font-mono text-gray-400 w-10 sm:w-14 text-right shrink-0">
                              {m.any_match_rate}%
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-xs sm:text-sm">
                  <thead>
                    <tr className="border-b border-gray-700/50">
                      <th className="text-left py-2.5 pr-3 text-gray-500 font-medium text-[10px] sm:text-xs uppercase tracking-wider">Method</th>
                      {tierKeys.map((tk) => (
                        <th key={tk} className="text-center py-2.5 px-2 text-gray-500 font-medium text-[10px] sm:text-xs uppercase tracking-wider">{tk}</th>
                      ))}
                      <th className="text-center py-2.5 pl-2 text-gray-500 font-medium text-[10px] sm:text-xs uppercase tracking-wider">Overall</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.ranking.map((name) => {
                      const m = result.methods[name];
                      const tiers = tierKeys.map((tk) => m.tiers[tk]);
                      return (
                        <tr key={name} className="border-b border-gray-800/30 hover:bg-white/[0.02]">
                          <td className="py-3 pr-3 font-medium text-gray-200 whitespace-nowrap">{METHOD_LABELS[name] || name}</td>
                          {tiers.map((t) => (
                            <td key={name + t.avg_main_hits} className="text-center py-3 px-2">
                              <div className="text-gray-200">{t.avg_main_hits}</div>
                              <div className="text-[10px] text-gray-500">{t.bonus_hit_rate}%</div>
                            </td>
                          ))}
                          <td className="text-center py-3 pl-2">
                            <div className="text-yellow-400 font-semibold">{m.avg_main_hits}</div>
                            <div className="text-[10px] text-gray-500">{m.bonus_hit_rate}%</div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
