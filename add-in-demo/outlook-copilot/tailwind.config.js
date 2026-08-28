/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "media",
  theme: {
    extend: {
      colors: {
        // Fluent UI / Outlook blue palette
        outlook: {
          50: "#f0f6ff",
          100: "#dbeafe",
          500: "#0078d4",
          600: "#106ebe",
          700: "#005a9e",
        },
      },
    },
  },
  plugins: [],
};
