"use client";

import type { ChangeEvent } from "react";
import { Button } from "@/components/ui";
import { PROTEIN_SOURCE_OPTIONS, REVIEWED_OPTIONS, STRUCTURE_OPTIONS } from "@/lib/protein";
import type { ProteinFilters as Filters } from "@/types/protein";

interface ProteinFiltersProps {
  filters: Filters;
  onChange: (filters: Filters) => void;
  onReset: () => void;
}

const fieldClass =
  "h-11 w-full border border-glass-border bg-glass-surface px-3 font-body text-sm text-content-primary outline-none transition-colors focus:border-category-protein [color-scheme:dark]";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-2">
      <span className="eyebrow">{label}</span>
      {children}
    </label>
  );
}

export function ProteinFilters({ filters, onChange, onReset }: ProteinFiltersProps) {
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
          {PROTEIN_SOURCE_OPTIONS.map((o) => (
            <option key={o.value} value={o.value} className="bg-bg-secondary">
              {o.label}
            </option>
          ))}
        </select>
      </Field>

      <Field label="Review status">
        <select
          value={filters.reviewed}
          onChange={(e) => onChange({ ...filters, reviewed: e.target.value as Filters["reviewed"] })}
          className={fieldClass}
        >
          {REVIEWED_OPTIONS.map((o) => (
            <option key={o.value} value={o.value} className="bg-bg-secondary">
              {o.label}
            </option>
          ))}
        </select>
      </Field>

      <Field label="Structure">
        <select
          value={filters.structure}
          onChange={(e) => onChange({ ...filters, structure: e.target.value as Filters["structure"] })}
          className={fieldClass}
        >
          {STRUCTURE_OPTIONS.map((o) => (
            <option key={o.value} value={o.value} className="bg-bg-secondary">
              {o.label}
            </option>
          ))}
        </select>
      </Field>

      <Field label="Min length (aa)">
        <input
          type="number"
          min={0}
          value={filters.minLength ?? ""}
          onChange={handleNumber("minLength")}
          placeholder="0"
          className={fieldClass}
        />
      </Field>

      <Field label="Max length (aa)">
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
