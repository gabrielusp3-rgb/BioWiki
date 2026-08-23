"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import { Button, Navbar } from "@/components/ui";
import { CloseIcon } from "@/components/ui/Icons";
import { drawerVariants, overlayVariants } from "@/lib/animations";

const NAV_ITEMS = [
  { label: "DNA", href: "/dna" },
  { label: "RNA", href: "/rna" },
  { label: "Proteins", href: "/proteins" },
  { label: "CRISPR", href: "/crispr" },
  { label: "Genomes", href: "/genomes" },
  { label: "Virus", href: "/virus" },
  { label: "Organisms", href: "/organisms" },
  { label: "Downloads", href: "/downloads" },
  { label: "API", href: "/api" },
];

export function SiteHeader({ activeHref = "/" }: { activeHref?: string }) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [open]);

  return (
    <>
      <Navbar items={NAV_ITEMS} activeHref={activeHref} onMenuClick={() => setOpen(true)} />

      <AnimatePresence>
        {open && (
          <div className="fixed inset-0 z-[300] lg:hidden">
            <motion.div
              variants={overlayVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              onClick={() => setOpen(false)}
              className="absolute inset-0 bg-black/75 backdrop-blur-sm"
            />
            <motion.nav
              variants={drawerVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              className="glass-strong absolute left-0 top-0 flex h-full w-80 max-w-[85vw] flex-col"
            >
              <div className="flex items-center justify-between border-b border-glass-divider px-6 py-4">
                <span className="flex items-center">
                  <img src="/brand-logo.png" alt="BioWiki" className="h-8 w-auto" />
                </span>
                <button
                  type="button"
                  onClick={() => setOpen(false)}
                  aria-label="Close menu"
                  className="grid h-9 w-9 place-items-center border border-glass-border text-content-secondary hover:text-content-primary"
                >
                  <CloseIcon className="h-5 w-5" />
                </button>
              </div>

              <div className="flex flex-1 flex-col gap-0.5 overflow-y-auto p-4">
                {NAV_ITEMS.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setOpen(false)}
                    className="border-l-2 border-l-transparent px-3 py-3 font-display text-sm font-medium uppercase tracking-wide text-content-secondary transition-colors hover:border-l-category-dna hover:bg-white/[0.03] hover:text-content-primary"
                  >
                    {item.label}
                  </Link>
                ))}
              </div>

              <div className="flex flex-col gap-3 border-t border-glass-divider p-4">
                <Link href="/search" onClick={() => setOpen(false)}>
                  <Button variant="outline" fullWidth>
                    Search
                  </Button>
                </Link>
                <Link href="/dna" onClick={() => setOpen(false)}>
                  <Button variant="primary" fullWidth>
                    Explore Database
                  </Button>
                </Link>
              </div>
            </motion.nav>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}
