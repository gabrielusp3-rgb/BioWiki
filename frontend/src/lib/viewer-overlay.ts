import type { CSSProperties } from "react";
import { cn } from "@/lib/cn";

/** Full-screen dimmer that never grows past the viewport. */
export function viewerOverlayClass(fullscreen = false) {
  return cn(
    "fixed inset-0 z-[1000] flex h-[100dvh] w-full items-center justify-center overflow-hidden",
    fullscreen ? "p-0" : "p-3 sm:p-6",
  );
}

/**
 * Scrollable body of a viewer. Must stay a column (block / flex-col).
 * A row flex here stacks Length/Function/Sequence side-by-side and collapses
 * residue lines into a single vertical letter column.
 */
export const viewerBodyClass =
  "flex min-h-0 flex-1 flex-col overflow-y-auto overscroll-contain";

/** Glass panel capped to the overlay, so header/footer stay on screen. */
export function viewerPanelClass(options: { fullscreen?: boolean; maxWidth?: string } = {}) {
  const { fullscreen = false, maxWidth = "max-w-4xl" } = options;
  return cn(
    "glass-strong relative z-10 flex w-full min-h-0 flex-col overflow-hidden",
    fullscreen ? "h-full max-h-full max-w-none" : cn("max-h-full", maxWidth),
  );
}

/**
 * Inline caps so a tall sequence cannot stretch the flex item past the
 * viewport (flex min-height:auto would otherwise ignore max-height).
 */
export function viewerPanelStyle(fullscreen = false): CSSProperties {
  if (fullscreen) {
    return { height: "100%", maxHeight: "100%", minHeight: 0, overflow: "hidden" };
  }
  return { maxHeight: "100%", minHeight: 0, overflow: "hidden" };
}
