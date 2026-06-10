/**
 * Design tokens for consistent spacing, sizing, and typography
 */

export const tokens = {
  // Spacing scale
  space: {
    xs: "0.25rem",  // 4px
    sm: "0.5rem",   // 8px
    md: "0.75rem",  // 12px
    lg: "1rem",     // 16px
    xl: "1.5rem",   // 24px
    "2xl": "2rem",  // 32px
    "3xl": "3rem",  // 48px
  },

  // Component sizes
  size: {
    input: {
      sm: "h-8 px-2 text-xs",
      md: "h-9 px-3 text-sm",
      lg: "h-10 px-4 text-base",
    },
    button: {
      sm: "h-8 px-2 text-xs",
      md: "h-9 px-3 text-sm",
      lg: "h-10 px-4 text-base",
    },
    card: {
      sm: "p-3",
      md: "p-4",
      lg: "p-6",
    },
  },

  // Typography
  text: {
    xs: "text-xs",     // 12px
    sm: "text-sm",     // 14px
    base: "text-base", // 16px
    lg: "text-lg",     // 18px
    xl: "text-xl",     // 20px
    "2xl": "text-2xl", // 24px
  },

  // Layout
  layout: {
    maxWidth: "max-w-6xl",
    container: "max-w-6xl mx-auto px-4",
    section: "space-y-4",
  },
} as const
