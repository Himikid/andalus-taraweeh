import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        charcoal: "#dfece3",
        charcoalSoft: "#ebf3ed",
        charcoalLift: "#e4eee7",
        ivory: "#223028",
        muted: "#5b7267",
        green: "#2f7a59",
        line: "#b8ccc0"
      }
    }
  },
  plugins: []
};

export default config;
