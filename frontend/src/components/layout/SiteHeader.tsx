"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import { BrandLogo } from "@/components/brand/BrandLogo";
import { Button, Navbar } from "@/components/ui";
import { CloseIcon } from "@/components/ui/Icons";
import { drawerVariants, overlayVariants } from "@/lib/animations";
import { useLocale } from "@/lib/i18n/LocaleProvider";
import type { MessageKey } from "@/lib/i18n/messages";

const NAV_ITEMS: { href: string; labelKey: MessageKey }[] = [
  { labelKey: "navDna", href: "/dna" },
  { labelKey: "navRna", href: "/rna" },
  { labelKey: "navProteins", href: "/proteins" },
  { labelKey: "navCrispr", href: "/crispr" },
  { labelKey: "navGenomes", href: "/genomes" },
  { labelKey: "navVirus", href: "/virus" },
  { labelKey: "navOrganisms", href: "/organisms" },
  { labelKey: "navPaleogenomics", href: "/paleogenomics" },
  { labelKey: "navPublications", href: "/publications" },
  { labelKey: "navDownloads", href: "/downloads" },
];

export function SiteHeader({ activeHref = "/" }: { activeHref?: string }) {
  const [open, setOpen] = useState(false);
  const { t } = useLocale();
  const items = NAV_ITEMS.map((item) => ({ href: item.href, label: t(item.labelKey) }));

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
      <Navbar items={items} activeHref={activeHref} onMenuClick={() => setOpen(true)} />

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
                  <BrandLogo />
                </span>
                <button
                  type="button"
                  onClick={() => setOpen(false)}
                  aria-label={t("actionCloseMenu")}
                  className="grid h-9 w-9 place-items-center border border-glass-border text-content-secondary hover:text-content-primary"
                >
                  <CloseIcon className="h-5 w-5" />
                </button>
              </div>

              <div className="flex flex-1 flex-col gap-0.5 overflow-y-auto p-4">
                {items.map((item) => (
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
                    {t("actionSearch")}
                  </Button>
                </Link>
                <Link href="/dna" onClick={() => setOpen(false)}>
                  <Button variant="primary" fullWidth>
                    {t("actionExploreDatabase")}
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
