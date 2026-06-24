"use client";
import { PredictionPick } from "@/lib/api";
import NumberBall from "@/components/NumberBall";

interface Props {
  tier: string;
  picks: PredictionPick[];
  rank?: number;
}

export default function PredictionCard({ tier, picks, rank = 0 }: Props) {
  const tierLabel = tier.replace("+bonus", " + Bonus");
  return (
    <div className="tier-card rounded-2xl p-4 sm:p-6 animate-slide-up" style={{ animationDelay: `${rank * 80}ms` }}>
      <div className="flex items-center justify-between mb-3 sm:mb-4">
        <h3 className="text-sm sm:text-lg font-bold text-gray-100">{tierLabel}</h3>
      </div>
      <div className="space-y-2.5 sm:space-y-3">
        {picks.map((pick, i) => (
          <div key={i} className="flex items-center gap-2 sm:gap-3 bg-gray-900/60 rounded-xl p-2.5 sm:p-3 border border-gray-800/30 hover:border-yellow-900/30 transition-colors duration-200">
            <span className="text-gray-600 text-[10px] sm:text-xs font-mono w-4 sm:w-5 text-right">#{i + 1}</span>
            <div className="flex gap-1 sm:gap-1.5 flex-wrap flex-1">
              {pick.numbers.map((n, j) => (
                <NumberBall key={j} num={n} size="sm" index={j} />
              ))}
              <NumberBall num={pick.bonus} bonus size="sm" index={pick.numbers.length} />
            </div>
            <span className="text-[9px] sm:text-[11px] text-gray-500 font-mono ml-auto tabular-nums">
              {(pick.probability * 100).toFixed(2)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
