import { getNumberColor, BONUS_COLOR } from "@/lib/colors";

interface Props {
  num: number;
  bonus?: boolean;
  size?: "sm" | "md";
  index?: number;
}

export default function NumberBall({ num, bonus, size = "md", index = 0 }: Props) {
  const { from, to } = bonus ? BONUS_COLOR : getNumberColor(num);
  const dims = size === "sm"
    ? "w-6 h-6 text-[9px] sm:w-7 sm:h-7 sm:text-[10px]"
    : "w-9 h-9 text-[11px] sm:w-11 sm:h-11 sm:text-sm";
  return (
    <span
      className={`${dims} rounded-full bg-gradient-to-b ${from} ${to} flex items-center justify-center font-bold text-white shadow-lg animate-ball-pop`}
      style={{ animationDelay: `${index * 40}ms`, animationFillMode: "both" }}
    >
      {num}
    </span>
  );
}
