"use client";

import { forwardRef } from "react";
import type { HTMLAttributes, ReactNode } from "react";
import { motion, type HTMLMotionProps } from "framer-motion";
import { cn } from "@/lib/cn";
import type { CategoryKey } from "@/lib/design-tokens";
import { CATEGORY_META } from "@/lib/categories";
import { hoverLift } from "@/lib/animations";

type CardVariant = "glass" | "strong" | "outline";

export interface CardProps extends Omit<HTMLMotionProps<"div">, "ref" | "children"> {
  variant?: CardVariant;
  category?: CategoryKey;
  interactive?: boolean;
  padded?: boolean;
  children?: ReactNode;
}

const variants: Record<CardVariant, string> = {
  glass: "glass",
  strong: "glass-strong",
  outline: "surface-panel",
};

export const Card = forwardRef<HTMLDivElement, CardProps>(function Card(
  {
    variant = "glass",
    category,
    interactive = false,
    padded = true,
    className,
    children,
    style,
    ...props
  },
  ref,
) {
  const meta = category ? CATEGORY_META[category] : undefined;

  return (
    <motion.div
      ref={ref}
      variants={interactive ? hoverLift : undefined}
      initial={interactive ? "rest" : undefined}
      whileHover={interactive ? "hover" : undefined}
      whileTap={interactive ? "tap" : undefined}
      style={
        meta
          ? ({ ["--glow-color" as string]: meta.glow.split(" ").slice(-1)[0], ...style })
          : style
      }
      className={cn(
        "relative overflow-hidden",
        variants[variant],
        padded && "p-6",
        interactive &&
          "cursor-pointer transition-colors duration-200 ease-standard hover:border-white/20",
        className,
      )}
      {...props}
    >
      {meta && (
        <span
          aria-hidden
          className="absolute inset-x-0 top-0 h-px"
          style={{ background: meta.color, opacity: 0.7 }}
        />
      )}
      {children}
    </motion.div>
  );
});

export function CardHeader({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("mb-4 flex items-start justify-between gap-4", className)} {...props}>
      {children}
    </div>
  );
}

export function CardTitle({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn(
        "font-display text-lg font-bold uppercase tracking-tightest text-content-primary",
        className,
      )}
      {...props}
    >
      {children}
    </h3>
  );
}

export function CardDescription({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p className={cn("text-sm leading-relaxed text-content-secondary", className)} {...props}>
      {children}
    </p>
  );
}

export function CardBody({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("text-sm text-content-secondary", className)} {...props}>
      {children}
    </div>
  );
}

export function CardFooter({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLDivElement> & { children?: ReactNode }) {
  return (
    <div
      className={cn(
        "mt-6 flex items-center justify-between gap-4 border-t border-glass-divider pt-4",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}
