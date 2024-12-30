/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  // Enable dark mode with class strategy
  darkMode: 'class',
  theme: {
    extend: {
      // Add custom animations
      animation: {
        'loadingBar': 'loadingBar 2s infinite',
        'pulse-custom': 'pulse-custom 2s infinite',
        'fade-in': 'fadeIn 1s ease-in',
      },
      // Define keyframes for the animations
      keyframes: {
        loadingBar: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' }
        },
        'pulse-custom': {
          '0%, 100%': { opacity: 1 },
          '50%': { opacity: 0.3 }
        },
        fadeIn: {
          '0%': { opacity: 0 },
          '100%': { opacity: 1 }
        }
      },
      // Add custom colors if needed
      colors: {
        'primary': {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
      },
      // Add custom transition properties
      transitionProperty: {
        'height': 'height',
        'spacing': 'margin, padding',
      },
      // Add custom transition durations
      transitionDuration: {
        '2000': '2000ms',
      },
    },
  },
  plugins: [],
};