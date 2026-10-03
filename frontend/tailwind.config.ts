import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        background: '#F7F8FA',
        surface: '#FFFFFF',
        'surface-subtle': '#F1F3F6',
        border: '#D9DEE5',
        'border-strong': '#B8C0CC',
        'text-primary': '#1B2430',
        'text-secondary': '#4A5565',
        'text-muted': '#6B7686',
        accent: '#2F5D8A',
        'accent-hover': '#264C72',
        'accent-subtle': '#E6EEF6',
        'status-neutral': '#4A5565',
        'status-attention': '#7A5A12',
        'status-info': '#2F5D8A',
      },
      fontFamily: {
        sans: ['Inter', 'IBM Plex Sans', 'system-ui', 'sans-serif'],
        mono: ['IBM Plex Mono', 'JetBrains Mono', 'monospace'],
      },
      spacing: {
        base: '1rem',
      },
      borderRadius: {
        sm: '4px',
        md: '6px',
      },
    },
  },
  plugins: [],
}

export default config
