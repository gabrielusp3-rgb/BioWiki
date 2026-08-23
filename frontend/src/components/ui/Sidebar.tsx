"use client";

import { useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { cn } from "@/lib/cn";
import { drawerVariants, overlayVariants } from "@/lib/animations";
import { CloseIcon } from "@/components/ui/Icons";
import type { CategoryKey } from "@/lib/design-tokens";
import { CATEGORY_META } from "@/lib/categories";

export interface SidebarItem {
  label: string;
  href: string;
  category?: CategoryKey;
}

export interface SidebarGroup {
  title: string;
  items: SidebarItem[];
}

export interface SidebarProps {
  groups: SidebarGroup[];
  activeHref?: string;
  open?: boolean;
  onClose?: () => void;
  className?: string;
}

function SidebarContent({
  groups,
  activeHref,
  onNavigate,
}: {
  groups: SidebarGroup[];
  activeHref?: string;
  onNavigate?: () => void;
}) {
  return (
    <nav className="flex flex-col gap-8 p-6">
      {groups.map((group) => (
        <div key={group.title} className="flex flex-col gap-2">
          <span className="eyebrow px-3">{group.title}</span>
          <ul className="flex flex-col gap-0.5">
            {group.items.map((item) => {
              const active = item.href === activeHref;
              const meta = item.category ? CATEGORY_META[item.category] : undefined;
              return (
                <li key={item.href}>
                  <a
                    href={item.href}
                    onClick={onNavigate}
                    className={cn(
                      "group flex items-center gap-3 border-l-2 px-3 py-2.5 font-display text-xs font-medium uppercase tracking-wide transition-colors duration-200",
                      active
                        ? "border-l-current bg-white/[0.04] text-content-primary"
                        : "border-l-transparent text-content-secondary hover:bg-white/[0.03] hover:text-content-primary",
                    )}
                    style={active && meta ? { color: meta.color } : undefined}
                  >
                    <span
                      className="h-1.5 w-1.5 shrink-0"
                      style={{
                        backgroundColor: meta?.color ?? "currentColor",
                        boxShadow: active && meta ? meta.glow : undefined,
                      }}
                    />
                    {item.label}
                  </a>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </nav>
  );
}

export function Sidebar({
  groups,
  activeHref,
  open = false,
  onClose,
  className,
}: SidebarProps) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose?.();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  return (
    <>
      {/* Persistent rail for large screens */}
      <aside
        className={cn(
          "sticky top-16 hidden h-[calc(100dvh-4rem)] w-72 shrink-0 overflow-y-auto border-r border-glass-divider bg-bg-secondary/60 backdrop-blur-glass lg:block",
          className,
        )}
      >
        <SidebarContent groups={groups} activeHref={activeHref} />
      </aside>

      {/* Mobile / tablet drawer */}
      <AnimatePresence>
        {open && (
          <div className="fixed inset-0 z-[250] lg:hidden">
            <motion.div
              variants={overlayVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              onClick={onClose}
              className="absolute inset-0 bg-black/70 backdrop-blur-sm"
            />
            <motion.aside
              variants={drawerVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              className="glass-strong absolute left-0 top-0 h-full w-80 max-w-[85vw] overflow-y-auto"
            >
              <div className="flex items-center justify-between border-b border-glass-divider px-6 py-4">
                <span className="font-display text-sm font-bold uppercase tracking-wider">
                  Navigation
                </span>
                <button
                  type="button"
                  onClick={onClose}
                  aria-label="Close menu"
                  className="grid h-9 w-9 place-items-center border border-glass-border text-content-secondary hover:text-content-primary"
                >
                  <CloseIcon className="h-5 w-5" />
                </button>
              </div>
              <SidebarContent groups={groups} activeHref={activeHref} onNavigate={onClose} />
            </motion.aside>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}
