/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        'dash-bg-from': '#081028',
        'dash-bg-to': '#0a183f',
        'dash-blue': '#2398ff',
        'dash-purple': '#914cff',
        'dash-red': '#ff4a78',
        'dash-muted': '#b0c4e8',
      },
      boxShadow: {
        glow: '0 0 20px rgba(35, 152, 255, 0.35)',
        'glow-purple': '0 0 24px rgba(145, 76, 255, 0.4)',
      },
      animation: {
        'flow-line': 'flowLine 2s linear infinite',
        'pulse-soft': 'pulseSoft 4s ease-in-out infinite',
        ripple: 'ripple 2s ease-out infinite',
      },
      keyframes: {
        flowLine: {
          '0%': { backgroundPosition: '0% 50%' },
          '100%': { backgroundPosition: '200% 50%' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '0.85' },
          '50%': { opacity: '1' },
        },
        ripple: {
          '0%': { transform: 'scale(0.8)', opacity: '0.6' },
          '100%': { transform: 'scale(2.2)', opacity: '0' },
        },
      },
    },
  },
  plugins: [],
};
