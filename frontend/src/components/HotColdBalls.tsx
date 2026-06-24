"use client";
import NumberBall from "@/components/NumberBall";

interface Props {
  hot: number[];
  cold: number[];
}

export default function HotColdBalls({ hot, cold }: Props) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:gap-8">
      <div>
        <div className="flex items-center gap-2 mb-3">
          <span className="w-2 h-2 rounded-full bg-red-400 animate-glow-pulse" />
          <h3 className="text-xs sm:text-sm font-semibold text-red-400 uppercase tracking-wider">Hot</h3>
        </div>
        <div className="flex gap-1.5 sm:gap-2 flex-wrap">
          {hot.map((n, i) => (
            <NumberBall key={n} num={n} index={i} />
          ))}
        </div>
      </div>
      <div>
        <div className="flex items-center gap-2 mb-3">
          <span className="w-2 h-2 rounded-full bg-blue-400" />
          <h3 className="text-xs sm:text-sm font-semibold text-blue-400 uppercase tracking-wider">Cold</h3>
        </div>
        <div className="flex gap-1.5 sm:gap-2 flex-wrap">
          {cold.map((n, i) => (
            <NumberBall key={n} num={n} index={i} />
          ))}
        </div>
      </div>
    </div>
  );
}
