"use client";

import type { HTMLAttributes, MouseEvent } from "react";
import { cn } from "@/lib/cn";

export interface TagProps extends HTMLAttributes<HTMLSpanElement> {
  active?: boolean;
  removable?: boolean;
  onRemove?: () => void;
}

export function Tag({
  active = false,
  removable = false,
  onRemove,
  className,
  children,
  ...props
}: TagProps) {
  const handleRemove = (event: MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    onRemove?.();
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 border px-3 py-1.5 font-mono text-xs transition-colors duration-200 ease-standard",
        active
          ? "border-category-dna/60 bg-category-dna/10 text-category-dna"
          : "border-glass-border bg-glass-surface text-content-secondary hover:border-white/25 hover:text-content-primary",
        className,
      )}
      {...props}
    >
      {children}
      {removable && (
        <button
          type="button"
          onClick={handleRemove}
          aria-label="Remove tag"
          className="grid h-3.5 w-3.5 place-items-center text-current opacity-60 transition-opacity hover:opacity-100"
        >
          <svg viewBox="0 0 12 12" className="h-3 w-3" fill="none" stroke="currentColor" strokeWidth="1.6">
            <path d="M2.5 2.5l7 7M9.5 2.5l-7 7" strokeLinecap="square" />
          </svg>
        </button>
      )}
    </span>
  );
}
