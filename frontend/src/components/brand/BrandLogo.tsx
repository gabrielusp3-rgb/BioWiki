import Image from "next/image";

type BrandLogoProps = {
  className?: string;
  priority?: boolean;
};

/**
 * Local lockup. The file is a static asset (not user input), so `unoptimized`
 * skips the image pipeline. A sized wrapper keeps next/image from laying out
 * at the file's intrinsic 1024px width and covering the primary navigation.
 */
export function BrandLogo({ className = "", priority = false }: BrandLogoProps) {
  return (
    <span className={`relative inline-block h-8 w-[7.5rem] shrink-0 overflow-hidden ${className}`.trim()}>
      <Image
        src="/brand-logo.png"
        alt="BioWiki"
        fill
        className="object-contain object-left"
        sizes="120px"
        priority={priority}
        unoptimized
      />
    </span>
  );
}
