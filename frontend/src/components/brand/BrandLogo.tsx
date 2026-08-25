type BrandLogoProps = {
  className?: string;
  priority?: boolean;
};

/**
 * Site mark (transparent PNG) plus the BIOWIKI wordmark in type, so the header
 * is not a raster lockup with a rectangular backdrop. A plain img is used so the
 * mark cannot be absolutely positioned against the footer's `relative` box.
 */
export function BrandLogo({ className = "", priority = false }: BrandLogoProps) {
  return (
    <span className={`inline-flex items-center gap-2.5 ${className}`.trim()}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/brand-logo.png"
        alt=""
        width={32}
        height={32}
        className="pointer-events-none h-8 w-8 shrink-0 object-contain"
        decoding="async"
        fetchPriority={priority ? "high" : "auto"}
      />
      <span className="font-display text-sm font-bold uppercase tracking-tightest text-content-primary sm:text-base">
        BIOWIKI
      </span>
    </span>
  );
}
