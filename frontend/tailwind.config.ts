import type { Config } from 'tailwindcss'

/**
 * Colours are declared as CSS custom property references, never hex literals.
 * Tailwind emits `var(--color-surface)` into the utility, so the
 * `prefers-color-scheme: dark` block in tokens.css repaints every utility
 * without a single `dark:` variant.
 *
 * Consequence: opacity modifiers such as `bg-accent/10` cannot be used, because
 * a bare var() has no numeric channel to divide. Use the explicit hover and
 * subtle tokens instead.
 */
const config: Config = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        background: 'var(--color-background)',
        surface: 'var(--color-surface)',
        'surface-subtle': 'var(--color-surface-subtle)',
        'surface-sunken': 'var(--color-surface-sunken)',
        header: 'var(--color-header)',

        border: 'var(--color-border)',
        'border-subtle': 'var(--color-border-subtle)',
        'border-strong': 'var(--color-border-strong)',

        primary: 'var(--color-text-primary)',
        secondary: 'var(--color-text-secondary)',
        muted: 'var(--color-text-muted)',
        inverse: 'var(--color-text-inverse)',

        accent: 'var(--color-accent)',
        'accent-hover': 'var(--color-accent-hover)',
        'accent-active': 'var(--color-accent-active)',
        'accent-subtle': 'var(--color-accent-subtle)',
        'accent-subtle-hover': 'var(--color-accent-subtle-hover)',
        'accent-border': 'var(--color-accent-border)',

        'status-neutral-bg': 'var(--color-status-neutral-bg)',
        'status-neutral-fg': 'var(--color-status-neutral-fg)',
        'status-neutral-border': 'var(--color-status-neutral-border)',
        'status-attention-bg': 'var(--color-status-attention-bg)',
        'status-attention-fg': 'var(--color-status-attention-fg)',
        'status-attention-border': 'var(--color-status-attention-border)',
        'status-info-bg': 'var(--color-status-info-bg)',
        'status-info-fg': 'var(--color-status-info-fg)',
        'status-info-border': 'var(--color-status-info-border)',
      },
      fontFamily: {
        sans: ['var(--font-family-sans)'],
        mono: ['var(--font-family-mono)'],
      },
      fontSize: {
        xs: ['var(--text-xs)', { lineHeight: '1.4' }],
        sm: ['var(--text-sm)', { lineHeight: '1.45' }],
        base: ['var(--text-base)', { lineHeight: 'var(--line-height-normal)' }],
        lg: ['var(--text-lg)', { lineHeight: '1.4' }],
        xl: ['var(--text-xl)', { lineHeight: '1.35' }],
        '2xl': ['var(--text-2xl)', { lineHeight: '1.25' }],
        '3xl': ['var(--text-3xl)', { lineHeight: '1.2' }],
      },
      maxWidth: {
        content: 'var(--max-width-content)',
        prose: 'var(--max-width-prose)',
      },
      spacing: {
        panel: 'var(--panel-gap)',
        control: 'var(--control-min-height)',
      },
      borderRadius: {
        sm: 'var(--radius-sm)',
        md: 'var(--radius-md)',
        full: 'var(--radius-full)',
      },
      boxShadow: {
        panel: 'var(--shadow-panel)',
        raised: 'var(--shadow-raised)',
        overlay: 'var(--shadow-overlay)',
      },
      transitionDuration: {
        fast: 'var(--duration-fast)',
        base: 'var(--duration-base)',
      },
      transitionTimingFunction: {
        standard: 'var(--easing-standard)',
      },
      keyframes: {
        'fade-in': {
          from: { opacity: '0', transform: 'translateY(2px)' },
          to: { opacity: '1', transform: 'none' },
        },
        'progress-sweep': {
          from: { transform: 'translateX(-100%)' },
          to: { transform: 'translateX(100%)' },
        },
      },
      animation: {
        'fade-in': 'fade-in var(--duration-base) var(--easing-standard) both',
        'progress-sweep': 'progress-sweep 1.6s var(--easing-standard) infinite',
      },
    },
  },
  plugins: [],
}

export default config