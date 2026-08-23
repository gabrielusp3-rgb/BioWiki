"use client";

import type { ChangeEvent } from "react";
import { Button } from "@/components/ui";
import { CAS_SYSTEM_OPTIONS, CRISPR_SOURCE_OPTIONS } from "@/lib/crispr";
import type { CasSystem, CrisprFilters as Filters } from "@/types/crispr";

interface CRISPRFiltersProps {
  filters: Filters;
  onChange: (filters: Filters) => void;
  onReset: () => void;
}

const fieldClass =
  "h-11 w-full border border-glass-border bg-glass-surface px-3 font-body text-sm text-content-primary outline-none transition-colors focus:border-category-crispr [color-scheme:dark]";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-2">
      <span className="eyebrow">{label}</span>
      {children}
    </label>
  );
}

export function CRISPRFilters({ filters, onChange, onReset }: CRISPRFiltersProps) {
  const handleNumber =
    (key: "minLength" | "maxLength") => (event: ChangeEvent<HTMLInputElement>) => {
      const raw = event.target.value;
      onChange({ ...filters, [key]: raw === "" ? null : Math.max(0, Number(raw)) });
    };

  return (
    <div className="glass hairline grid grid-cols-1 gap-5 p-6 sm:grid-cols-2 lg:grid-cols-3">
      <Field label="Organism">
        <input
          value={filters.organism}
          onChange={(e) => onChange({ ...filters, organism: e.target.value })}
          placeholder="e.g. Homo sapiens"
          className={fieldClass}
        />
      </Field>

      <Field label="Target gene">
        <input
          value={filters.targetGene}
          onChange={(e) => onChange({ ...filters, targetGene: e.target.value })}
          placeholder="e.g. EMX1"
          className={fieldClass}
        />
      </Field>

      <Field label="PAM">
        <input
          value={filters.pam}
          onChange={(e) => onChange({ ...filters, pam: e.target.value.toUpperCase() })}
          placeholder="e.g. NGG"
          className={fieldClass}
        />
      </Field>

      <Field label="Cas system">
        <select
          value={filters.system}
          onChange={(e) => onChange({ ...filters, system: e.target.value as CasSystem | "all" })}
          className={fieldClass}
        >
          {CAS_SYSTEM_OPTIONS.map((o) => (
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
          {CRISPR_SOURCE_OPTIONS.map((o) => (
            <option key={o.value} value={o.value} className="bg-bg-secondary">
              {o.label}
            </option>
          ))}
        </select>
      </Field>

      <div className="grid grid-cols-2 gap-3">
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
      </div>

      <div className="flex items-end justify-end sm:col-span-2 lg:col-span-3">
        <Button variant="ghost" size="sm" onClick={onReset}>
          Clear filters
        </Button>
      </div>
    </div>
  );
}
