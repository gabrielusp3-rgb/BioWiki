import type { Transition, Variants } from "framer-motion";
import { motion as motionTokens } from "@/lib/design-tokens";

const { duration, ease } = motionTokens;

/** Calm, scientific spring-free transitions. */
export const transitions = {
  standard: {
    duration: duration.base,
    ease: ease.standard,
  } satisfies Transition,
  fast: {
    duration: duration.fast,
    ease: ease.standard,
  } satisfies Transition,
  slow: {
    duration: duration.slow,
    ease: ease.entrance,
  } satisfies Transition,
};

export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: transitions.standard },
  exit: { opacity: 0, transition: transitions.fast },
};

export const fadeInUp: Variants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: transitions.slow },
  exit: { opacity: 0, y: 8, transition: transitions.fast },
};

export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.98 },
  visible: { opacity: 1, scale: 1, transition: transitions.standard },
  exit: { opacity: 0, scale: 0.98, transition: transitions.fast },
};

/** Overlay + panel pair for modals. */
export const overlayVariants: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: transitions.fast },
  exit: { opacity: 0, transition: transitions.fast },
};

export const modalVariants: Variants = {
  hidden: { opacity: 0, y: 24, scale: 0.98 },
  visible: { opacity: 1, y: 0, scale: 1, transition: transitions.standard },
  exit: { opacity: 0, y: 16, scale: 0.98, transition: transitions.fast },
};

/** Sidebar drawer for mobile/tablet. */
export const drawerVariants: Variants = {
  hidden: { x: "-100%" },
  visible: { x: 0, transition: transitions.standard },
  exit: { x: "-100%", transition: transitions.fast },
};

/** Container that staggers its children. */
export function staggerContainer(stagger = 0.06, delayChildren = 0.04): Variants {
  return {
    hidden: {},
    visible: {
      transition: {
        staggerChildren: stagger,
        delayChildren,
      },
    },
  };
}

export const hoverLift = {
  rest: { y: 0 },
  hover: { y: -4, transition: transitions.fast },
  tap: { y: 0, scale: 0.99, transition: transitions.fast },
};
