import type { HTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export interface DividerProps extends HTMLAttributes<HTMLDivElement> {
  orientation?: "horizontal" | "vertical";
  label?: string;
}

export function Divider({
  orientation = "horizontal",
  label,
  className,
  ...props
}: DividerProps) {
  if (orientation === "vertical") {
    return (
      <div
        role="separator"
        aria-orientation="vertical"
        className={cn("w-px self-stretch bg-glass-divider", className)}
        {...props}
      />
    );
  }

  if (label) {
    return (
      <div className={cn("flex items-center gap-4", className)} {...props}>
        <span className="h-px flex-1 bg-glass-divider" />
        <span className="eyebrow">{label}</span>
        <span className="h-px flex-1 bg-glass-divider" />
      </div>
    );
  }

  return (
    <div
      role="separator"
      aria-orientation="horizontal"
      className={cn("h-px w-full bg-glass-divider", className)}
      {...props}
    />
  );
}
