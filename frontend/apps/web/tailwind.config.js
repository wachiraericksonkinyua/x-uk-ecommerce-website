/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,ts,js}"],
  theme: {
    extend: {
      colors: {
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
      boxShadow: {
        brand: "0 12px 30px -12px rgba(255, 79, 0, 0.35)",
      },
      keyframes: {
        marquee: {
          "0%": { transform: "translate3d(0, 0, 0)" },
          "100%": { transform: "translate3d(-50%, 0, 0)" },
        },
        "marquee-up": {
          "0%": { transform: "translate3d(0, 0, 0)" },
          "100%": { transform: "translate3d(0, -50%, 0)" },
        },
        "marquee-down": {
          "0%": { transform: "translate3d(0, -50%, 0)" },
          "100%": { transform: "translate3d(0, 0, 0)" },
        },
      },
      animation: {
        marquee: "marquee 40s linear infinite",
        "marquee-up": "marquee-up 28s linear infinite",
        "marquee-down": "marquee-down 34s linear infinite",
      },
    },
  },
};
