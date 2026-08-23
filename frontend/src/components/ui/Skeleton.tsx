import type { HTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  width?: string | number;
  height?: string | number;
}

/**
 * Loading placeholder for streamed/lazy content. Renders a glass surface with a
 * moving shimmer; it holds layout space and carries no fabricated content.
 */
export function Skeleton({ width, height, className, style, ...props }: SkeletonProps) {
  return (
    <div
      aria-hidden
      style={{ width, height, ...style }}
      className={cn(
        "relative overflow-hidden border border-glass-divider bg-glass-surface",
        className,
      )}
      {...props}
    >
      <span className="shimmer-mask absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-white/[0.06] to-transparent" />
    </div>
  );
}
