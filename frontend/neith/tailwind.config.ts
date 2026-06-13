import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        noir: "#111419",
        emerald: "#284139",
        egyptian: "#BB6830",
        khaki: "#F8E794",
        wasabi: "#809070",
        balsamico: "#150C0C",
        burnt: "#341E0F",
        honey: "#85431E",
        whiskey: "#D39858",
        champagne: "#EACEAA",
      },
      fontFamily: {
        temple: ["UnifrakturMaguntia", "cursive"],
        carved: ["Cinzel", "serif"],
        scroll: ["Crimson Text", "serif"],
      },
    },
  },
  plugins: [],
};
export default config;
