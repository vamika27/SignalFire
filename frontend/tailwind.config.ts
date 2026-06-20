import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        sage: "#9CAF88",
        "light-sage": "#DDE8D2",
        "deep-sage": "#5F6F52",
        beige: "#F5EBDD",
        cream: "#FBF8F1",
        paper: "#FFFDF7",
        ink: "#25251F",
        muted: "#777568",
        line: "#DDD2BF",
        accent: "#B48A5A"
      },
      boxShadow: {
        paper: "0 24px 80px rgba(95, 111, 82, 0.14)",
        card: "0 14px 40px rgba(37, 37, 31, 0.08)"
      },
      borderRadius: {
        "3xl": "1.75rem"
      }
    }
  },
  plugins: []
};

export default config;
