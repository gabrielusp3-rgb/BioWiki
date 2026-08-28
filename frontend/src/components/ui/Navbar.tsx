"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { cn } from "@/lib/cn";
import { BrandLogo } from "@/components/brand/BrandLogo";
import { Button } from "@/components/ui/Button";
import { MenuIcon, SearchIcon } from "@/components/ui/Icons";

export interface NavItem {
  label: string;
  href: string;
}

export interface NavbarProps {
  items?: NavItem[];
  activeHref?: string;
  onMenuClick?: () => void;
}

const DEFAULT_ITEMS: NavItem[] = [
  { label: "DNA", href: "/dna" },
  { label: "RNA", href: "/rna" },
  { label: "Proteins", href: "/proteins" },
  { label: "CRISPR", href: "/crispr" },
  { label: "Genomes", href: "/genomes" },
  { label: "Virus", href: "/virus" },
];

export function Navbar({
  items = DEFAULT_ITEMS,
  activeHref,
  onMenuClick,
}: NavbarProps) {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={cn(
        "fixed inset-x-0 top-0 z-[200] transition-colors duration-300 ease-standard",
        scrolled
          ? "border-b border-glass-divider bg-black/60 backdrop-blur-glass backdrop-saturate-[1.8]"
          : "border-b border-transparent",
      )}
    >
      <nav className="mx-auto flex h-16 w-full max-w-[1680px] items-center justify-between gap-6 px-5 sm:px-8 lg:px-12">
        <Link href="/" className="group relative z-10 flex shrink-0 items-center">
          <BrandLogo priority />
        </Link>

        <ul className="hidden items-center gap-1 lg:flex">
          {items.map((item) => {
            const active = item.href === activeHref;
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    "relative px-3 py-2 font-display text-xs font-medium uppercase tracking-wide transition-colors duration-200",
                    active
                      ? "text-content-primary"
                      : "text-content-secondary hover:text-content-primary",
                  )}
                >
                  {item.label}
                  {active && (
                    <span className="absolute inset-x-3 -bottom-px h-px bg-category-dna shadow-glow-dna" />
                  )}
                </Link>
              </li>
            );
          })}
        </ul>

        <div className="flex items-center gap-2">
          <Link href="/search" className="hidden sm:inline-flex">
            <Button
              variant="ghost"
              size="sm"
              leadingIcon={<SearchIcon className="h-4 w-4" />}
            >
              Search
            </Button>
          </Link>
          <Link href="/dna" className="hidden sm:inline-flex">
            <Button variant="primary" size="sm">
              Explore
            </Button>
          </Link>
          <button
            type="button"
            onClick={onMenuClick}
            aria-label="Open menu"
            className="grid h-10 w-10 place-items-center border border-glass-border bg-glass-surface text-content-primary lg:hidden"
          >
            <MenuIcon className="h-5 w-5" />
          </button>
        </div>
      </nav>
    </header>
  );
}
