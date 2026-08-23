"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { cn } from "@/lib/cn";
import { Badge } from "@/components/ui/Badge";
import { ExternalIcon, HelixIcon } from "@/components/ui/Icons";
import { hoverLift } from "@/lib/animations";
import { formatStatistic } from "@/lib/statistics";
import { GROUP_COLOR, GROUP_LABEL } from "@/lib/organisms";
import type { Organism } from "@/types/organism";

function initials(name: string): string {
  const parts = name.trim().split(/\s+/);
  const letters = parts.slice(0, 2).map((p) => p[0]?.toUpperCase() ?? "");
  return letters.join("");
}

function OrganismEmblem({ organism, color }: { organism: Organism; color: string }) {
  if (organism.imageUrl) {
    return (
      <div className="relative h-40 w-full overflow-hidden border-b border-glass-divider">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={organism.imageUrl}
          alt={organism.scientificName}
          loading="lazy"
          className="h-full w-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent" />
      </div>
    );
  }

  // Abstract scientific emblem — a visual identity, not fabricated data.
  return (
    <div
      className="grid-lines relative grid h-40 w-full place-items-center overflow-hidden border-b border-glass-divider"
      style={{
        background: `radial-gradient(120% 120% at 30% 0%, ${color}1F, transparent 60%), #0A0A0A`,
      }}
    >
      <HelixIcon
        className="absolute -right-4 -top-3 h-24 w-24 opacity-10"
        style={{ color }}
      />
      <span
        className="font-display text-5xl font-bold tracking-tightest"
        style={{ color, textShadow: `0 0 30px ${color}59` }}
      >
        {initials(organism.scientificName)}
      </span>
      <span className="absolute bottom-2 left-3 font-mono text-[10px] text-content-muted">
        taxid:{organism.taxId}
      </span>
    </div>
  );
}

export interface OrganismCardProps {
  organism: Organism;
  className?: string;
}

export function OrganismCard({ organism, className }: OrganismCardProps) {
  const color = GROUP_COLOR[organism.group] ?? "#00F2FF";
  const links = organism.links ?? [];
  const detailLink = links.find((l) => !l.external);
  const externalLinks = links.filter((l) => l.external);
  const lineageTail = (organism.lineage ?? []).slice(-3);

  return (
    <motion.article
      variants={hoverLift}
      initial="rest"
      whileHover="hover"
      className={cn(
        "glass hairline group flex h-full flex-col overflow-hidden transition-colors duration-300 hover:border-white/20",
        className,
      )}
    >
      <OrganismEmblem organism={organism} color={color} />

      <div className="flex flex-1 flex-col gap-4 p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex min-w-0 flex-col">
            <h3 className="truncate font-display text-lg font-bold tracking-tightest text-content-primary">
              {organism.commonName ?? organism.scientificName}
            </h3>
            <span className="truncate font-body text-sm italic text-content-secondary">
              {organism.scientificName}
            </span>
          </div>
          <Badge
            tone="neutral"
            dot
            style={{ color, borderColor: `${color}59`, backgroundColor: `${color}14` }}
          >
            {GROUP_LABEL[organism.group]}
          </Badge>
        </div>

        {/* Taxonomy */}
        <div className="flex flex-col gap-2 border-t border-glass-divider pt-3">
          <span className="eyebrow">Taxonomy{organism.rank ? ` · ${organism.rank}` : ""}</span>
          <div className="flex flex-wrap items-center gap-1.5 text-xs text-content-secondary">
            {lineageTail.map((node, i) => (
              <span key={`${i}-${node}`} className="flex items-center gap-1.5">
                {i > 0 && <span className="text-content-muted">/</span>}
                <span>{node}</span>
              </span>
            ))}
          </div>
        </div>

        {/* Sequence count + links */}
        <div className="mt-auto flex items-end justify-between gap-3 border-t border-glass-divider pt-4">
          <div className="flex flex-col">
            {organism.sequenceCount !== null ? (
              <span className="font-display text-xl font-bold tabular-nums text-content-primary">
                {formatStatistic(organism.sequenceCount)}
              </span>
            ) : (
              <span className="font-display text-xl font-bold text-content-muted">—</span>
            )}
            <span className="text-[10px] uppercase tracking-wider text-content-muted">
              {organism.sequenceCount !== null ? "Sequences" : "Awaiting database"}
            </span>
          </div>

          <div className="flex items-center gap-2">
            {externalLinks.map((link) => (
              <a
                key={link.url}
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                aria-label={link.label}
                className="grid h-9 w-9 place-items-center border border-glass-border text-content-secondary transition-colors hover:border-white/30 hover:text-content-primary"
              >
                <ExternalIcon className="h-4 w-4" />
              </a>
            ))}
            {detailLink && (
              <Link
                href={detailLink.url}
                className="border px-3 py-2 font-display text-[11px] font-semibold uppercase tracking-wide transition-colors"
                style={{ color, borderColor: `${color}59` }}
              >
                Explore
              </Link>
            )}
          </div>
        </div>
      </div>
    </motion.article>
  );
}
