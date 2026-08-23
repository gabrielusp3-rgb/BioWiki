"use client";

import type { ChangeEvent } from "react";
import { Button } from "@/components/ui";
import { CODING_OPTIONS, RNA_CLASS_OPTIONS, RNA_SOURCE_OPTIONS } from "@/lib/rna";
import type { RnaFilters as Filters, RnaClass } from "@/types/rna";

interface RNAFiltersProps {
  filters: Filters;
  onChange: (filters: Filters) => void;
  onReset: () => void;
}

const fieldClass =
  "h-11 w-full border border-glass-border bg-glass-surface px-3 font-body text-sm text-content-primary outline-none transition-colors focus:border-category-rna [color-scheme:dark]";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-2">
      <span className="eyebrow">{label}</span>
      {children}
    </label>
  );
}

export function RNAFilters({ filters, onChange, onReset }: RNAFiltersProps) {
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

      <Field label="Source">
        <select
          value={filters.source}
          onChange={(e) => onChange({ ...filters, source: e.target.value })}
          className={fieldClass}
        >
          {RNA_SOURCE_OPTIONS.map((o) => (
            <option key={o.value} value={o.value} className="bg-bg-secondary">
              {o.label}
            </option>
          ))}
        </select>
      </Field>

      <Field label="RNA class">
        <select
          value={filters.rnaClass}
          onChange={(e) => onChange({ ...filters, rnaClass: e.target.value as RnaClass | "all" })}
          className={fieldClass}
        >
          {RNA_CLASS_OPTIONS.map((o) => (
            <option key={o.value} value={o.value} className="bg-bg-secondary">
              {o.label}
            </option>
          ))}
        </select>
      </Field>

      <Field label="Coding potential">
        <select
          value={filters.coding}
          onChange={(e) =>
            onChange({ ...filters, coding: e.target.value as Filters["coding"] })
          }
          className={fieldClass}
        >
          {CODING_OPTIONS.map((o) => (
            <option key={o.value} value={o.value} className="bg-bg-secondary">
              {o.label}
            </option>
          ))}
        </select>
      </Field>

      <Field label="Min length (nt)">
        <input
          type="number"
          min={0}
          value={filters.minLength ?? ""}
          onChange={handleNumber("minLength")}
          placeholder="0"
          className={fieldClass}
        />
      </Field>

      <Field label="Max length (nt)">
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
