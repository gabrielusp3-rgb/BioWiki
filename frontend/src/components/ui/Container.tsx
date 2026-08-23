import { createElement } from "react";
import type { ElementType, HTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";

type ContainerWidth = "narrow" | "default" | "wide" | "full";

export interface ContainerProps extends HTMLAttributes<HTMLDivElement> {
  as?: ElementType;
  width?: ContainerWidth;
}

const widths: Record<ContainerWidth, string> = {
  narrow: "max-w-3xl",
  default: "max-w-container",
  wide: "max-w-[1680px]",
  full: "max-w-none",
};

export function Container({
  as,
  width = "default",
  className,
  children,
  ...props
}: ContainerProps) {
  const Component = as ?? "div";
  return createElement(
    Component,
    {
      className: cn("mx-auto w-full px-5 sm:px-8 lg:px-12", widths[width], className),
      ...props,
    },
    children,
  );
}

export interface SectionProps extends HTMLAttributes<HTMLElement> {
  eyebrow?: string;
  title?: string;
  description?: string;
  /** Optional element rendered on the right of the header (e.g. a status badge). */
  action?: ReactNode;
}

export function Section({
  eyebrow,
  title,
  description,
  action,
  className,
  children,
  ...props
}: SectionProps) {
  return (
    <section className={cn("py-16 sm:py-20 lg:py-24", className)} {...props}>
      {(eyebrow || title || description || action) && (
        <header className="mb-10 flex flex-col gap-4">
          {action ? (
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="flex flex-col gap-4">
                {eyebrow && <span className="eyebrow">{eyebrow}</span>}
                {title && (
                  <h2 className="max-w-3xl text-balance font-display text-3xl font-bold uppercase tracking-tightest sm:text-4xl">
                    {title}
                  </h2>
                )}
                {description && (
                  <p className="max-w-2xl text-balance text-base leading-relaxed text-content-secondary">
                    {description}
                  </p>
                )}
              </div>
              <div className="shrink-0">{action}</div>
            </div>
          ) : (
            <>
              {eyebrow && <span className="eyebrow">{eyebrow}</span>}
              {title && (
                <h2 className="max-w-3xl text-balance font-display text-3xl font-bold uppercase tracking-tightest sm:text-4xl">
                  {title}
                </h2>
              )}
              {description && (
                <p className="max-w-2xl text-balance text-base leading-relaxed text-content-secondary">
                  {description}
                </p>
              )}
            </>
          )}
        </header>
      )}
      {children}
    </section>
  );
}
