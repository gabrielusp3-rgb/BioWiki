"use client";

import type { ChangeEvent } from "react";
import { cn } from "@/lib/cn";
import { Button, Tag } from "@/components/ui";
import {
  CATEGORY_OPTIONS,
  COMPLEXITY_OPTIONS,
  SEARCH_SOURCES,
  SEARCH_TYPES,
} from "@/lib/search-config";
import type { CategoryKey } from "@/lib/design-tokens";
import {
  type ComplexityLevel,
  type SearchFilters as Filters,
  type SearchType,
} from "@/types/search";

interface SearchFiltersProps {
  filters: Filters;
  onChange: (filters: Filters) => void;
  onReset: () => void;
}

function FieldLabel({ children }: { children: string }) {
  return <span className="eyebrow mb-2 block">{children}</span>;
}

const selectClass =
  "h-11 w-full border border-glass-border bg-glass-surface px-3 font-body text-sm text-content-primary outline-none transition-colors focus:border-category-dna [color-scheme:dark]";

export function SearchFilters({ filters, onChange, onReset }: SearchFiltersProps) {
  const toggleType = (type: SearchType) => {
    const next = filters.types.includes(type)
      ? filters.types.filter((t) => t !== type)
      : [...filters.types, type];
    onChange({ ...filters, types: next });
  };

  const handleNumber =
    (key: "minLength" | "maxLength") => (event: ChangeEvent<HTMLInputElement>) => {
      const raw = event.target.value;
      onChange({ ...filters, [key]: raw === "" ? null : Math.max(0, Number(raw)) });
    };

  return (
    <div className="glass hairline flex flex-col gap-6 p-6">
      <div>
        <FieldLabel>Type</FieldLabel>
        <div className="flex flex-wrap gap-2">
          {SEARCH_TYPES.map((meta) => (
            <Tag
              key={meta.type}
              active={filters.types.includes(meta.type)}
              onClick={() => toggleType(meta.type)}
            >
              {meta.label}
            </Tag>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        <div>
          <FieldLabel>Organism</FieldLabel>
          <input
            value={filters.organism}
            onChange={(e) => onChange({ ...filters, organism: e.target.value })}
            placeholder="e.g. Homo sapiens"
            className={selectClass}
          />
        </div>

        <div>
          <FieldLabel>Source</FieldLabel>
          <select
            value={filters.source}
            onChange={(e) => onChange({ ...filters, source: e.target.value })}
            className={selectClass}
          >
            {SEARCH_SOURCES.map((s) => (
              <option key={s.value} value={s.value} className="bg-bg-secondary">
                {s.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <FieldLabel>Category</FieldLabel>
          <select
            value={filters.category}
            onChange={(e) =>
              onChange({ ...filters, category: e.target.value as CategoryKey | "all" })
            }
            className={selectClass}
          >
            {CATEGORY_OPTIONS.map((c) => (
              <option key={c.value} value={c.value} className="bg-bg-secondary">
                {c.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <FieldLabel>Min length</FieldLabel>
          <input
            type="number"
            min={0}
            value={filters.minLength ?? ""}
            onChange={handleNumber("minLength")}
            placeholder="0"
            className={selectClass}
          />
        </div>

        <div>
          <FieldLabel>Max length</FieldLabel>
          <input
            type="number"
            min={0}
            value={filters.maxLength ?? ""}
            onChange={handleNumber("maxLength")}
            placeholder="—"
            className={selectClass}
          />
        </div>

        <div>
          <FieldLabel>Complexity</FieldLabel>
          <select
            value={filters.complexity}
            onChange={(e) =>
              onChange({ ...filters, complexity: e.target.value as ComplexityLevel })
            }
            className={selectClass}
          >
            {COMPLEXITY_OPTIONS.map((c) => (
              <option key={c.value} value={c.value} className="bg-bg-secondary">
                {c.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className={cn("flex items-center justify-end gap-3 border-t border-glass-divider pt-4")}>
        <Button variant="ghost" size="sm" onClick={onReset}>
          Clear filters
        </Button>
      </div>
    </div>
  );
}
