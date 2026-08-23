"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const LINKS = [
  { href: "/dna", label: "DNA" },
  { href: "/rna", label: "RNA" },
  { href: "/proteins", label: "Proteins" },
  { href: "/crispr", label: "CRISPR" },
  { href: "/viruses", label: "Viruses" },
  { href: "/genomes", label: "Genomes" },
  { href: "/organisms", label: "Organisms" },
  { href: "/search", label: "Search" },
  { href: "/api", label: "API" },
];

export function Navbar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-white/5 bg-black/60 backdrop-blur-xl">
      <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between px-6 lg:px-10">
        <Link href="/" className="display text-lg tracking-tight text-white">
          BIO<span className="text-dna">WIKI</span>
        </Link>

        <nav className="hidden items-center gap-1 lg:flex">
          {LINKS.map((l) => {
            const active = pathname === l.href;
            return (
              <Link
                key={l.href}
                href={l.href}
                className={`px-3 py-2 text-[0.7rem] font-semibold uppercase tracking-widest transition-colors ${
                  active ? "text-dna" : "text-neutral-400 hover:text-white"
                }`}
              >
                {l.label}
              </Link>
            );
          })}
        </nav>

        <button
          className="glass px-3 py-2 text-[0.7rem] uppercase tracking-widest text-white lg:hidden"
          onClick={() => setOpen((v) => !v)}
        >
          Menu
        </button>
      </div>

      {open && (
        <nav className="grid grid-cols-2 gap-px border-t border-white/5 bg-white/5 lg:hidden">
          {LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              onClick={() => setOpen(false)}
              className="bg-black px-6 py-4 text-[0.7rem] font-semibold uppercase tracking-widest text-neutral-300"
            >
              {l.label}
            </Link>
          ))}
        </nav>
      )}
    </header>
  );
}
