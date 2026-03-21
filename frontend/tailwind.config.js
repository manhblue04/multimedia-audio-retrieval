/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#e8f4fd",
          100: "#bee3f8",
          400: "#4299e1",
          500: "#3182ce",
          600: "#2b6cb0",
          900: "#1a365d",
        },
        dark: {
          800: "#1a1a2e",
          900: "#0f0f23",
          950: "#080816",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
