import type { HTMLAttributes } from "react";
import { cn } from "@/lib/cn";
import type { CategoryKey } from "@/lib/design-tokens";
import { CATEGORY_META } from "@/lib/categories";

type BadgeTone = "neutral" | "success" | "warning" | "danger" | "info";

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  category?: CategoryKey;
  tone?: BadgeTone;
  dot?: boolean;
}

const tones: Record<BadgeTone, { color: string; border: string }> = {
  neutral: { color: "#8A8A8A", border: "rgba(255,255,255,0.14)" },
  success: { color: "#39FF14", border: "rgba(57,255,20,0.35)" },
  warning: { color: "#FFFF00", border: "rgba(255,255,0,0.35)" },
  danger: { color: "#FF4444", border: "rgba(255,68,68,0.35)" },
  info: { color: "#00F2FF", border: "rgba(0,242,255,0.35)" },
};

export function Badge({
  category,
  tone = "neutral",
  dot = false,
  className,
  children,
  style,
  ...props
}: BadgeProps) {
  const meta = category ? CATEGORY_META[category] : undefined;
  const color = meta ? meta.color : tones[tone].color;
  const border = meta ? `${meta.color}59` : tones[tone].border;

  return (
    <span
      style={{ color, borderColor: border, backgroundColor: `${color}14`, ...style }}
      className={cn(
        "inline-flex items-center gap-1.5 border px-2.5 py-1",
        "font-display text-[10px] font-semibold uppercase tracking-wider",
        className,
      )}
      {...props}
    >
      {dot && (
        <span
          aria-hidden
          className="h-1.5 w-1.5"
          style={{ backgroundColor: color, boxShadow: `0 0 8px ${color}` }}
        />
      )}
      {children ?? meta?.label}
    </span>
  );
}
