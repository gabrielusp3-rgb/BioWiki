"use client";

import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export interface Column<T> {
  key: string;
  header: ReactNode;
  align?: "left" | "right" | "center";
  width?: string;
  render?: (row: T, index: number) => ReactNode;
  accessor?: (row: T) => ReactNode;
}

export interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  rowKey: (row: T, index: number) => string;
  onRowClick?: (row: T) => void;
  emptyLabel?: string;
  dense?: boolean;
  className?: string;
}

const alignment = {
  left: "text-left",
  right: "text-right",
  center: "text-center",
};

export function Table<T>({
  columns,
  data,
  rowKey,
  onRowClick,
  emptyLabel = "No records available.",
  dense = false,
  className,
}: TableProps<T>) {
  return (
    <div className={cn("glass overflow-hidden", className)}>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-glass-divider">
              {columns.map((col) => (
                <th
                  key={col.key}
                  scope="col"
                  style={{ width: col.width }}
                  className={cn(
                    "whitespace-nowrap px-5 py-4 font-display text-[11px] font-semibold uppercase tracking-wider text-content-secondary",
                    alignment[col.align ?? "left"],
                  )}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-5 py-12 text-center text-sm text-content-muted"
                >
                  {emptyLabel}
                </td>
              </tr>
            ) : (
              data.map((row, index) => (
                <tr
                  key={rowKey(row, index)}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                  className={cn(
                    "border-b border-glass-divider/60 transition-colors duration-150",
                    onRowClick && "cursor-pointer hover:bg-white/[0.03]",
                  )}
                >
                  {columns.map((col) => {
                    const content = col.render
                      ? col.render(row, index)
                      : col.accessor
                        ? col.accessor(row)
                        : null;
                    return (
                      <td
                        key={col.key}
                        className={cn(
                          "px-5 text-content-primary",
                          dense ? "py-2.5" : "py-4",
                          alignment[col.align ?? "left"],
                        )}
                      >
                        {content}
                      </td>
                    );
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
