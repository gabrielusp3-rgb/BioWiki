"use client";

import type { SyncInfo, SyncStatus } from "@/services/statisticsService";

/**
 * Honest, real-time synchronisation indicator for the "Scale of the Database"
 * section. The label mirrors the true state of the backend and stored data —
 * it never claims data that is not there.
 */
const STATUS_META: Record<
  SyncStatus,
  { label: string; color: string; description: string }
> = {
  connected: {
    label: "Connected",
    color: "#00F2FF",
    description: "Live database connected — figures below are real counts.",
  },
  importing: {
    label: "Importing",
    color: "#FFFF00",
    description: "An ingestion run is in progress; counts update as it finishes.",
  },
  updated: {
    label: "Up to date",
    color: "#39FF14",
    description: "Cached aggregates match the live rows — fully synchronised.",
  },
  empty: {
    label: "Empty",
    color: "#8A8A8A",
    description: "No records stored yet — nothing is shown that does not exist.",
  },
  error: {
    label: "Sync error",
    color: "#FF4444",
    description: "The most recent ingestion run failed; showing last known real data.",
  },
  offline: {
    label: "Offline",
    color: "#8A8A8A",
    description: "Database not reachable — no figures are estimated.",
  },
};

export function SyncStatusBadge({ sync }: { sync: SyncInfo | null }) {
  const status: SyncStatus = sync?.status ?? "offline";
  const meta = STATUS_META[status] ?? STATUS_META.offline;
  const pulse = status === "importing";

  return (
    <div
      className="inline-flex items-center gap-2.5 border px-3 py-1.5"
      style={{ borderColor: `${meta.color}59`, backgroundColor: `${meta.color}0F` }}
      title={meta.description}
    >
      <span
        className={`h-2 w-2 rounded-full${pulse ? " animate-pulse" : ""}`}
        style={{ backgroundColor: meta.color, boxShadow: `0 0 8px ${meta.color}` }}
      />
      <span
        className="font-display text-[11px] font-semibold uppercase tracking-wide"
        style={{ color: meta.color }}
      >
        {meta.label}
      </span>
      {status === "importing" && sync && sync.activeImports > 0 && (
        <span className="font-mono text-[11px] text-content-muted">
          {sync.activeImports} run{sync.activeImports > 1 ? "s" : ""}
        </span>
      )}
    </div>
  );
}
