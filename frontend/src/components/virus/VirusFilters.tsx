"use client";

import type { ChangeEvent } from "react";
import { Button } from "@/components/ui";
import { GENOME_TYPE_OPTIONS, VIRUS_SOURCE_OPTIONS } from "@/lib/virus";
import type { GenomeType, VirusFilters as Filters } from "@/types/virus";

interface VirusFiltersProps {
  filters: Filters;
  onChange: (filters: Filters) => void;
  onReset: () => void;
}

const fieldClass =
  "h-11 w-full border border-glass-border bg-glass-surface px-3 font-body text-sm text-content-primary outline-none transition-colors focus:border-category-virus [color-scheme:dark]";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-2">
      <span className="eyebrow">{label}</span>
      {children}
    </label>
  );
}

export function VirusFilters({ filters, onChange, onReset }: VirusFiltersProps) {
  const handleNumber =
    (key: "minLength" | "maxLength") => (event: ChangeEvent<HTMLInputElement>) => {
      const raw = event.target.value;
      onChange({ ...filters, [key]: raw === "" ? null : Math.max(0, Number(raw)) });
    };

  return (
    <div className="glass hairline grid grid-cols-1 gap-5 p-6 sm:grid-cols-2 lg:grid-cols-3">
      <Field label="Viral family">
        <input
          value={filters.family}
          onChange={(e) => onChange({ ...filters, family: e.target.value })}
          placeholder="e.g. Coronaviridae"
          className={fieldClass}
        />
      </Field>

      <Field label="Host">
        <input
          value={filters.host}
          onChange={(e) => onChange({ ...filters, host: e.target.value })}
          placeholder="e.g. Homo sapiens"
          className={fieldClass}
        />
      </Field>

      <Field label="Genome type">
        <select
          value={filters.genomeType}
          onChange={(e) => onChange({ ...filters, genomeType: e.target.value as GenomeType | "all" })}
          className={fieldClass}
        >
          {GENOME_TYPE_OPTIONS.map((o) => (
            <option key={o.value} value={o.value} className="bg-bg-secondary">
              {o.label}
            </option>
          ))}
        </select>
      </Field>

      <Field label="Source">
        <select
          value={filters.source}
          onChange={(e) => onChange({ ...filters, source: e.target.value })}
          className={fieldClass}
        >
          {VIRUS_SOURCE_OPTIONS.map((o) => (
            <option key={o.value} value={o.value} className="bg-bg-secondary">
              {o.label}
            </option>
          ))}
        </select>
      </Field>

      <Field label="Min length">
        <input
          type="number"
          min={0}
          value={filters.minLength ?? ""}
          onChange={handleNumber("minLength")}
          placeholder="0"
          className={fieldClass}
        />
      </Field>

      <Field label="Max length">
        <input
          type="number"
          min={0}
          value={filters.maxLength ?? ""}
          onChange={handleNumber("maxLength")}
          placeholder="—"
          className={fieldClass}
        />
      </Field>

      <div className="flex items-end justify-end sm:col-span-2 lg:col-span-3">
        <Button variant="ghost" size="sm" onClick={onReset}>
          Clear filters
        </Button>
      </div>
    </div>
  );
}
