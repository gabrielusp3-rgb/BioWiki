"use client";

import { forwardRef, useId } from "react";
import type { InputHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
  leadingIcon?: ReactNode;
  trailingIcon?: ReactNode;
  inputSize?: "sm" | "md" | "lg";
}

const sizes = {
  sm: "h-9 text-xs",
  md: "h-11 text-sm",
  lg: "h-14 text-base",
};

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  {
    label,
    hint,
    error,
    leadingIcon,
    trailingIcon,
    inputSize = "md",
    className,
    id,
    disabled,
    ...props
  },
  ref,
) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  const describedBy = error
    ? `${inputId}-error`
    : hint
      ? `${inputId}-hint`
      : undefined;

  return (
    <div className={cn("flex w-full flex-col gap-2", disabled && "opacity-50")}>
      {label && (
        <label htmlFor={inputId} className="eyebrow">
          {label}
        </label>
      )}

      <div
        className={cn(
          "group relative flex items-center border bg-glass-surface transition-colors duration-200 ease-standard",
          "backdrop-blur-glass",
          error
            ? "border-state-danger"
            : "border-glass-border focus-within:border-category-dna",
        )}
      >
        {leadingIcon && (
          <span className="pointer-events-none flex h-full items-center pl-4 text-content-secondary">
            {leadingIcon}
          </span>
        )}

        <input
          ref={ref}
          id={inputId}
          disabled={disabled}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
          className={cn(
            "w-full bg-transparent px-4 font-body text-content-primary outline-none",
            "placeholder:text-content-muted",
            sizes[inputSize],
            leadingIcon && "pl-3",
            trailingIcon && "pr-3",
            className,
          )}
          {...props}
        />

        {trailingIcon && (
          <span className="flex h-full items-center pr-4 text-content-secondary">
            {trailingIcon}
          </span>
        )}
      </div>

      {error ? (
        <span id={`${inputId}-error`} className="text-xs text-state-danger">
          {error}
        </span>
      ) : hint ? (
        <span id={`${inputId}-hint`} className="text-xs text-content-secondary">
          {hint}
        </span>
      ) : null}
    </div>
  );
});
