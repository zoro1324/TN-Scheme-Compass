/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eefbf3",
          100: "#d2f4df",
          200: "#a6e9bf",
          300: "#6ad798",
          400: "#2cb66a",
          500: "#149a53",
          600: "#0e7a43",
          700: "#0d6038",
          800: "#0e4d30",
          900: "#0b4028"
        },
        ink: "#1e232b"
      },
      fontFamily: {
        heading: ["'Space Grotesk'", "sans-serif"],
        body: ["'IBM Plex Sans'", "sans-serif"]
      },
      boxShadow: {
        lift: "0 18px 45px rgba(20, 154, 83, 0.25)"
      }
    }
  },
  plugins: [],
};
