"use client";
import { Draw } from "@/lib/api";
import NumberBall from "@/components/NumberBall";

interface Props {
  draws: Draw[];
}

const TYPE_BADGES: Record<string, string> = {
  lunchtime: "badge badge-lunchtime",
  teatime: "badge badge-teatime",
  brunchtime: "badge badge-brunchtime",
  drivetime: "badge badge-drivetime",
};

const TYPE_LABELS: Record<string, string> = {
  lunchtime: "L",
  teatime: "T",
  brunchtime: "B",
  drivetime: "D",
};

export default function DrawTable({ draws }: Props) {
  return (
    <div className="overflow-x-auto -mx-5 sm:mx-0">
      <table className="w-full text-xs sm:text-sm">
        <thead>
          <tr className="border-b border-gray-700/50">
            <th className="text-left py-2.5 pl-5 sm:pl-0 pr-3 text-gray-500 font-medium text-[10px] sm:text-xs uppercase tracking-wider">Date</th>
            <th className="text-left py-2.5 px-3 text-gray-500 font-medium text-[10px] sm:text-xs uppercase tracking-wider">Type</th>
            <th className="text-left py-2.5 px-3 text-gray-500 font-medium text-[10px] sm:text-xs uppercase tracking-wider">Numbers</th>
            <th className="text-left py-2.5 pr-5 sm:pr-0 pl-3 text-gray-500 font-medium text-[10px] sm:text-xs uppercase tracking-wider">Bonus</th>
          </tr>
        </thead>
        <tbody>
          {draws.map((d, rowIdx) => (
            <tr key={d.id} className="border-b border-gray-800/30 hover:bg-white/[0.02] transition-colors duration-150 animate-fade-in" style={{ animationDelay: `${rowIdx * 20}ms` }}>
              <td className="py-2.5 pl-5 sm:pl-0 pr-3 text-[11px] sm:text-sm text-gray-400 whitespace-nowrap">{d.draw_date.slice(5)}</td>
              <td className="py-2.5 px-3">
                <span className={TYPE_BADGES[d.draw_type] || "badge"}>{TYPE_LABELS[d.draw_type] || d.draw_type.slice(0, 1).toUpperCase()}</span>
              </td>
              <td className="py-2.5 px-3">
                <div className="flex gap-1 sm:gap-1.5">
                  {[d.n1, d.n2, d.n3, d.n4, d.n5, d.n6].map((n, i) => (
                    <NumberBall key={i} num={n} size="sm" index={i} />
                  ))}
                </div>
              </td>
              <td className="py-2.5 pr-5 sm:pr-0 pl-3">
                <NumberBall num={d.bonus} bonus size="sm" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
