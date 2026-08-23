import type { ReactNode } from "react";

export function GlassCard({
  children,
  className = "",
  accent,
  hover = false,
}: {
  children: ReactNode;
  className?: string;
  accent?: string;
  hover?: boolean;
}) {
  return (
    <div
      className={`glass ${hover ? "glass-hover" : ""} relative overflow-hidden ${className}`}
    >
      {accent && (
        <span
          className="absolute left-0 top-0 h-full w-[3px]"
          style={{ background: accent }}
        />
      )}
      {children}
    </div>
  );
}
