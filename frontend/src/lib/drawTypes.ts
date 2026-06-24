export const DRAW_TYPES = [
  { value: "brunchtime", label: "Brunchtime" },
  { value: "lunchtime", label: "Lunchtime" },
  { value: "drivetime", label: "Drivetime" },
  { value: "teatime", label: "Teatime" },
] as const;

export function getNextDrawType(now = new Date()) {
  const hour = now.getHours();

  if (hour < 10) return "brunchtime";
  if (hour < 13) return "lunchtime";
  if (hour < 17) return "drivetime";
  return "teatime";
}
