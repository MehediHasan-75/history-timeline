/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./assets/js/**/*.js"
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ["Libre Baskerville", "Noto Serif Bengali", "Georgia", "serif"],
        sans: ["Inter", "Noto Sans Bengali", "ui-sans-serif", "system-ui", "sans-serif"]
      },
      boxShadow: {
        paper: "0 18px 50px -24px rgba(68, 64, 60, 0.32)"
      },
      backgroundImage: {
        grain: "radial-gradient(circle at 20% 10%, rgba(180, 83, 9, 0.08), transparent 28%), radial-gradient(circle at 80% 0%, rgba(120, 113, 108, 0.10), transparent 25%)"
      }
    }
  },
  plugins: []
};
