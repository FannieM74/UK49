"use client";
import { useEffect, useState } from "react";
import { Draw, fetchDraws, triggerScrape } from "@/lib/api";
import DrawTable from "@/components/DrawTable";
import HotColdBalls from "@/components/HotColdBalls";
import { DRAW_TYPES, getNextDrawType } from "@/lib/drawTypes";

export default function Dashboard() {
  const [draws, setDraws] = useState<Draw[]>([]);
  const [loading, setLoading] = useState(true);
  const [scraping, setScraping] = useState(false);
  const [scrapeMsg, setScrapeMsg] = useState("");
  const [lastUpdated, setLastUpdated] = useState("");
  const initialDrawType = typeof window !== "undefined" ? getNextDrawType() : "lunchtime";
  const [drawType, setDrawType] = useState(initialDrawType);

  useEffect(() => {
    setLoading(true);
    fetchDraws(50, drawType).then((d) => {
      setDraws(d);
      if (d.length > 0) setLastUpdated(d[0].draw_date);
    }).finally(() => setLoading(false));
  }, [drawType]);

  const mainNumbers = draws.flatMap(d => [d.n1, d.n2, d.n3, d.n4, d.n5, d.n6]);
  const freq = new Map<number, number>();
  mainNumbers.forEach(n => freq.set(n, (freq.get(n) || 0) + 1));
  const sorted = [...freq.entries()].sort((a, b) => b[1] - a[1]);
  const hot = sorted.slice(0, 5).map(e => e[0]);
  const cold = sorted.slice(-5).map(e => e[0]);

  const handleScrape = async () => {
    setScraping(true);
    try {
      const res = await triggerScrape();
      setScrapeMsg(`Added ${res.draws_added} draws`);
      const newDraws = await fetchDraws(50, drawType);
      setDraws(newDraws);
      if (newDraws.length > 0) setLastUpdated(newDraws[0].draw_date);
    } catch {
      setScrapeMsg("Scrape failed");
    }
    setScraping(false);
  };

  return (
    <main className="min-h-screen bg-grid">
      <div className="bg-gradient-radial pt-4 sm:pt-8 pb-8 sm:pb-16">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between mb-6 sm:mb-8">
            <div>
              <h1 className="text-2xl sm:text-4xl font-bold tracking-tight">Dashboard</h1>
              {lastUpdated && (
                <p className="text-xs sm:text-sm text-gray-500 mt-1">Last draw: {lastUpdated}</p>
              )}
            </div>
            <button
              onClick={handleScrape}
              disabled={scraping}
              className="bg-gradient-to-r from-yellow-500 to-yellow-600 hover:from-yellow-400 hover:to-yellow-500 disabled:from-gray-700 disabled:to-gray-700 text-gray-950 font-semibold px-4 py-2 sm:px-5 sm:py-2.5 rounded-xl text-xs sm:text-sm transition-all duration-200 shadow-lg shadow-yellow-500/20 disabled:shadow-none"
            >
              {scraping ? (
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-3 border-2 border-gray-950 border-t-transparent rounded-full animate-spin" />
                  Syncing
                </span>
              ) : "Update"}
            </button>
          </div>
          {scrapeMsg && (
            <div className="mb-5 animate-fade-in">
              <span className="inline-flex items-center gap-1.5 bg-emerald-900/40 text-emerald-400 text-xs font-medium px-3 py-1.5 rounded-full border border-emerald-800/30">
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                {scrapeMsg}
              </span>
            </div>
          )}

          <div className="glass-card rounded-2xl p-4 sm:p-6 mb-6 sm:mb-8 animate-fade-in">
            <select
              value={drawType}
              onChange={(e) => setDrawType(e.target.value)}
              className="bg-gray-900 border border-gray-700/50 rounded-xl px-4 py-2.5 text-xs sm:text-sm text-gray-200 focus:outline-none focus:border-yellow-500/50 transition-colors min-w-[140px]"
            >
              {DRAW_TYPES.map((dt) => (
                <option key={dt.value} value={dt.value}>{dt.label}</option>
              ))}
            </select>
            <span className="ml-3 text-[11px] sm:text-xs text-gray-400">
              {draws.length > 0 ? `Showing last ${draws.length} draws` : "No draws found"}
            </span>
          </div>

          <div className="glass-card rounded-2xl p-5 sm:p-7 animate-fade-in" style={{ animationDelay: "0.05s" }}>
            <h2 className="text-base sm:text-xl font-semibold mb-4 sm:mb-5 flex items-center gap-2">
              <span className="w-1.5 h-5 bg-red-400 rounded-full" />
              Hot & Cold Numbers
            </h2>
            <HotColdBalls hot={hot} cold={cold} />
          </div>

          <div className="glass-card rounded-2xl p-5 sm:p-7 mt-5 sm:mt-6 animate-fade-in" style={{ animationDelay: "0.1s" }}>
            <h2 className="text-base sm:text-xl font-semibold mb-4 sm:mb-5 flex items-center gap-2">
              <span className="w-1.5 h-5 bg-blue-400 rounded-full" />
              Recent Draws
            </h2>
            {loading ? (
              <div className="space-y-2">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="loading-shimmer h-8 rounded-lg" />
                ))}
              </div>
            ) : (
              <DrawTable draws={draws} />
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
