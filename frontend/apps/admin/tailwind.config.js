/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,ts,js}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#070C15",
          900: "#0B1220",
          800: "#121C2E",
          700: "#1B283D",
          600: "#2A3A54",
        },
        "brand-orange": {
          DEFAULT: "#FF4F00",
          dark: "#C93B00",
          soft: "#FFF0E8",
        },
        "brand-blue": {
          DEFAULT: "#96C5F7",
          50: "#F3F8FE",
          100: "#E4F1FD",
          200: "#CFE5FB",
          300: "#B4D6F2",
          400: "#A5CDF5",
          500: "#96C5F7",
          600: "#6FAFE8",
          700: "#2F6FA3",
        },
        primary: "#FF4F00",
        secondary: "#96C5F7",
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
        display: [
          "Sora",
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "sans-serif",
        ],
      },
      boxShadow: {
        brand: "0 12px 30px -12px rgba(255, 79, 0, 0.35)",
        panel: "0 1px 2px rgba(16, 24, 40, 0.04), 0 1px 3px rgba(16, 24, 40, 0.06)",
        lift: "0 18px 40px -24px rgba(11, 18, 32, 0.35)",
      },
      borderRadius: {
        "2.5xl": "1.25rem",
      },
    },
  },
};
