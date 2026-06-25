export const DRAW_TYPES = [
  { value: "lunchtime", label: "Lunchtime" },
  { value: "teatime", label: "Teatime" },
] as const;

export function getNextDrawType(now = new Date()) {
  const hour = now.getHours();
  if (hour < 13) return "lunchtime";
  return "teatime";
}
