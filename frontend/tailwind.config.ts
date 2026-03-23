import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        sand: {
          50: "#faf7f1",
          100: "#f4efe4",
          200: "#eadfc7",
        },
        forge: {
          500: "#d95d39",
          600: "#c44c29",
          700: "#a73e1f",
        },
      },
      boxShadow: {
        panel: "0 20px 70px rgba(72, 45, 27, 0.12)",
      },
      borderRadius: {
        "4xl": "2rem",
      },
      fontFamily: {
        sans: ["var(--font-space-grotesk)", "ui-sans-serif", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;

