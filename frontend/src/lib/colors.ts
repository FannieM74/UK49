const RANGE_COLORS: { range: [number, number]; bg: string; from: string; to: string }[] = [
  { range: [1, 9], bg: "bg-red-600", from: "from-red-500", to: "to-red-700" },
  { range: [10, 19], bg: "bg-blue-600", from: "from-blue-500", to: "to-blue-700" },
  { range: [20, 29], bg: "bg-emerald-600", from: "from-emerald-500", to: "to-emerald-700" },
  { range: [30, 39], bg: "bg-orange-500", from: "from-orange-400", to: "to-orange-600" },
  { range: [40, 49], bg: "bg-violet-600", from: "from-violet-500", to: "to-violet-700" },
];

export function getNumberColor(n: number): { bg: string; from: string; to: string } {
  for (const c of RANGE_COLORS) {
    if (n >= c.range[0] && n <= c.range[1]) return c;
  }
  return { bg: "bg-gray-600", from: "from-gray-500", to: "to-gray-700" };
}

export const BONUS_COLOR = { bg: "bg-yellow-500", from: "from-yellow-400", to: "to-yellow-600" };
