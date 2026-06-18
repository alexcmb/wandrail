/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Palette Wandrail : violet SNCF Connect + neutres
        violet: {
          DEFAULT: '#7c3aed',
          dark: '#4c1d95',
        },
        ink: '#111111',
        muted: '#6b6b6b',
        line: 'rgba(0,0,0,0.09)',
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
        display: ['"Space Grotesk"', '"Plus Jakarta Sans"', 'sans-serif'],
      },
      maxWidth: {
        page: '1280px',
      },
      boxShadow: {
        card: '0 1px 4px rgba(0,0,0,0.05)',
        cardHover: '0 14px 40px rgba(0,0,0,0.12)',
      },
    },
  },
  plugins: [],
}
