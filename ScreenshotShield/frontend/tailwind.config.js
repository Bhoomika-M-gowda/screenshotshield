export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: { ink: '#050816', navy: '#0b1330', electric: '#3b82f6', violet: '#8b5cf6' },
      fontFamily: { sans: ['Inter', 'ui-sans-serif', 'system-ui', 'Segoe UI', 'Roboto', 'sans-serif'], mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'] },
      keyframes: {
        fadeUp: { '0%': { opacity: 0, transform: 'translateY(16px)' }, '100%': { opacity: 1, transform: 'none' } },
        scan: { '0%': { top: '0%' }, '100%': { top: '100%' } },
        glow: { '0%,100%': { opacity: 0.5 }, '50%': { opacity: 1 } },
      },
      animation: { fadeUp: 'fadeUp .6s ease both', scan: 'scan 2.2s linear infinite', glow: 'glow 3s ease-in-out infinite' },
    },
  },
  plugins: [],
}
