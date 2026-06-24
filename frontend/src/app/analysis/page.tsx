"use client";
import { useEffect, useMemo, useState } from "react";
import { Draw, fetchDraws } from "@/lib/api";
import { DRAW_TYPES, getNextDrawType } from "@/lib/drawTypes";

function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="glass-card rounded-xl p-4 text-center">
      <p className="text-[10px] sm:text-xs text-gray-500 uppercase tracking-wider mb-1">{label}</p>
      <p className="text-lg sm:text-2xl font-bold text-gray-100">{value}</p>
      {sub ? <p className="text-[10px] sm:text-xs text-gray-600 mt-0.5">{sub}</p> : null}
    </div>
  );
}

export default function AnalysisPage() {
  const [draws, setDraws] = useState<Draw[]>([]);
  const initialDrawType = useMemo(() => getNextDrawType(), []);
  const [drawType, setDrawType] = useState(initialDrawType);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    const loadDraws = async () => {
      setLoading(true);
      try {
        const data = await fetchDraws(100, drawType);
        if (isMounted) setDraws(data);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    void loadDraws();

    return () => {
      isMounted = false;
    };
  }, [drawType]);

  const mainNumbers = draws.flatMap(d => [d.n1, d.n2, d.n3, d.n4, d.n5, d.n6]);
  const freq = new Map<number, number>();
  mainNumbers.forEach(n => freq.set(n, (freq.get(n) || 0) + 1));
  const sorted = [...freq.entries()].sort((a, b) => a[0] - b[0]);
  const maxCount = Math.max(...sorted.map(e => e[1]), 1);

  const odd = mainNumbers.filter(n => n % 2 === 1).length;
  const even = mainNumbers.length - odd;
  const low = mainNumbers.filter(n => n <= 24).length;
  const high = mainNumbers.filter(n => n > 24).length;
  const total = mainNumbers.length || 1;

  return (
    <main className="min-h-screen bg-grid">
      <div className="bg-gradient-radial pt-4 sm:pt-8 pb-8 sm:pb-16">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <h1 className="text-2xl sm:text-4xl font-bold tracking-tight mb-6 sm:mb-8">Analysis</h1>

          <div className="glass-card rounded-2xl p-4 sm:p-6 mb-6 sm:mb-8">
            <select
              value={drawType}
              onChange={(e) => setDrawType(e.target.value)}
              className="bg-gray-900 border border-gray-700/50 rounded-xl px-4 py-2.5 text-xs sm:text-sm text-gray-200 focus:outline-none focus:border-yellow-500/50 transition-colors w-full sm:w-auto"
            >
              {DRAW_TYPES.map((dt) => (
                <option key={dt.value} value={dt.value}>{dt.label}</option>
              ))}
            </select>
          </div>

          {loading ? (
            <div className="space-y-6">
              <div className="glass-card rounded-2xl p-5 sm:p-7">
                <div className="loading-shimmer h-5 w-36 rounded mb-5" />
                <div className="loading-shimmer h-32 rounded-lg" />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
                {[...Array(2)].map((_, i) => (
                  <div key={i} className="glass-card rounded-2xl p-5">
                    <div className="loading-shimmer h-5 w-24 rounded mb-4" />
                    <div className="loading-shimmer h-6 rounded-lg mb-2" />
                    <div className="loading-shimmer h-4 w-32 rounded" />
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <>
              <div className="glass-card rounded-2xl p-5 sm:p-7 mb-6 animate-fade-in">
                <h2 className="text-base sm:text-xl font-semibold mb-4 sm:mb-5 flex items-center gap-2">
                  <span className="w-1.5 h-5 bg-violet-400 rounded-full" />
                  Frequency (Last 100)
                </h2>
                <div className="flex items-end gap-[1.5px] sm:gap-[3px] overflow-x-auto pb-2">
                  {sorted.map(([num, count]) => {
                    const height = (count / maxCount) * 140;
                    return (
                      <div key={num} className="flex flex-col items-center min-w-[16px] sm:min-w-[24px] group">
                        <div className="relative w-full">
                          <div
                            className="bg-gradient-to-t from-violet-600 to-violet-400 w-full rounded-t-sm transition-all duration-300 group-hover:opacity-80"
                            style={{ height: `${Math.max(height, 3)}px` }}
                          />
                        </div>
                        <span className="text-[6px] sm:text-[8px] text-gray-500 mt-1 font-mono">{num}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6 mb-6">
                <div className="glass-card rounded-2xl p-5 sm:p-7 animate-fade-in" style={{ animationDelay: "0.05s" }}>
                  <h3 className="text-xs sm:text-sm font-semibold text-gray-300 mb-3 sm:mb-4 flex items-center gap-2">
                    <span className="w-1 h-4 bg-green-400 rounded-full" />
                    Odd / Even
                  </h3>
                  <div className="flex h-5 sm:h-7 rounded-full overflow-hidden mb-3 shadow-inner">
                    <div className="bg-gradient-to-r from-green-500 to-green-400 transition-all duration-500" style={{ width: `${(odd / total) * 100}%` }} />
                    <div className="bg-gradient-to-r from-purple-500 to-purple-400 transition-all duration-500" style={{ width: `${(even / total) * 100}%` }} />
                  </div>
                  <div className="flex justify-between text-xs sm:text-sm">
                    <span className="text-green-400 font-medium">{odd} odd</span>
                    <span className="text-purple-400 font-medium">{even} even</span>
                  </div>
                </div>

                <div className="glass-card rounded-2xl p-5 sm:p-7 animate-fade-in" style={{ animationDelay: "0.1s" }}>
                  <h3 className="text-xs sm:text-sm font-semibold text-gray-300 mb-3 sm:mb-4 flex items-center gap-2">
                    <span className="w-1 h-4 bg-orange-400 rounded-full" />
                    Low / High
                  </h3>
                  <div className="flex h-5 sm:h-7 rounded-full overflow-hidden mb-3 shadow-inner">
                    <div className="bg-gradient-to-r from-orange-500 to-orange-400 transition-all duration-500" style={{ width: `${(low / total) * 100}%` }} />
                    <div className="bg-gradient-to-r from-cyan-500 to-cyan-400 transition-all duration-500" style={{ width: `${(high / total) * 100}%` }} />
                  </div>
                  <div className="flex justify-between text-xs sm:text-sm">
                    <span className="text-orange-400 font-medium">{low} low (1-24)</span>
                    <span className="text-cyan-400 font-medium">{high} high (25-49)</span>
                  </div>
                </div>
              </div>

              {draws.length > 0 && (
                <div className="glass-card rounded-2xl p-5 sm:p-7 animate-fade-in" style={{ animationDelay: "0.15s" }}>
                  <h3 className="text-xs sm:text-sm font-semibold text-gray-300 mb-4 sm:mb-5 flex items-center gap-2">
                    <span className="w-1 h-4 bg-yellow-400 rounded-full" />
                    Stats
                  </h3>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
                    <StatCard label="Draws" value={String(draws.length)} />
                    <StatCard
                      label="Hottest"
                      value={sorted.length > 0 ? String(sorted.reduce((a, b) => a[1] > b[1] ? a : b)[0]) : "—"}
                      sub={`${sorted.length > 0 ? sorted.reduce((a, b) => a[1] > b[1] ? a : b)[1] : 0}x`}
                    />
                    <StatCard label="Odd:Even" value={`${odd}:${even}`} sub={`${((odd / total) * 100).toFixed(0)}% / ${((even / total) * 100).toFixed(0)}%`} />
                    <StatCard label="Low:High" value={`${low}:${high}`} sub={`${((low / total) * 100).toFixed(0)}% / ${((high / total) * 100).toFixed(0)}%`} />
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </main>
  );
}
