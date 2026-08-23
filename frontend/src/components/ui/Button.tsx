"use client";

import { forwardRef } from "react";
import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";
import type { CategoryKey } from "@/lib/design-tokens";
import { CATEGORY_META } from "@/lib/categories";

type ButtonVariant = "primary" | "glass" | "outline" | "ghost" | "category";
type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  category?: CategoryKey;
  leadingIcon?: ReactNode;
  trailingIcon?: ReactNode;
  loading?: boolean;
  fullWidth?: boolean;
}

const base =
  "relative inline-flex items-center justify-center gap-2 select-none font-display font-semibold uppercase tracking-wide " +
  "border transition-all duration-200 ease-standard outline-none " +
  "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-category-dna " +
  "disabled:cursor-not-allowed disabled:opacity-40 disabled:pointer-events-none";

const sizes: Record<ButtonSize, string> = {
  sm: "h-9 px-4 text-[11px]",
  md: "h-11 px-6 text-xs",
  lg: "h-14 px-8 text-sm",
};

const variants: Record<Exclude<ButtonVariant, "category">, string> = {
  primary:
    "bg-white text-bg-primary border-white hover:bg-white/90 active:bg-white/80 " +
    "shadow-[0_10px_40px_rgba(255,255,255,0.12)]",
  glass:
    "glass text-content-primary hover:bg-white/[0.07] active:bg-white/[0.05] " +
    "hover:border-white/20",
  outline:
    "bg-transparent text-content-primary border-glass-border hover:border-white/30 " +
    "hover:bg-white/[0.04] active:bg-white/[0.02]",
  ghost:
    "bg-transparent text-content-secondary border-transparent hover:text-content-primary " +
    "hover:bg-white/[0.04] active:bg-white/[0.02]",
};

const Spinner = () => (
  <span
    aria-hidden
    className="h-3.5 w-3.5 animate-spin border-2 border-current border-r-transparent"
  />
);

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  {
    variant = "glass",
    size = "md",
    category,
    leadingIcon,
    trailingIcon,
    loading = false,
    fullWidth = false,
    className,
    children,
    disabled,
    type = "button",
    style,
    ...props
  },
  ref,
) {
  const isCategory = variant === "category" && category;
  const meta = isCategory ? CATEGORY_META[category] : undefined;

  const categoryStyle =
    isCategory && meta
      ? {
          color: meta.color,
          borderColor: meta.color,
          boxShadow: meta.glow,
          ...style,
        }
      : style;

  return (
    <button
      ref={ref}
      type={type}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      style={categoryStyle}
      className={cn(
        base,
        sizes[size],
        isCategory
          ? "bg-transparent hover:bg-white/[0.05] active:bg-white/[0.03]"
          : variants[variant as Exclude<ButtonVariant, "category">],
        fullWidth && "w-full",
        className,
      )}
      {...props}
    >
      {loading ? <Spinner /> : leadingIcon}
      <span className={cn(loading && "opacity-70")}>{children}</span>
      {!loading && trailingIcon}
    </button>
  );
});
