import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        charcoal: "#111315",
        panel: "#171b1f",
        accent: "#0f3d2e",
        accentSoft: "#1f6b52"
      }
    }
  },
  plugins: []
};

export default config;
