module.exports = {
  content: [
    "./src/pulseroute/web/templates/**/*.html",
    "./src/pulseroute/web/static/js/**/*.js",
  ],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        display: ["Fraunces", "Georgia", "serif"],
        sans: ["Work Sans", "Inter", "sans-serif"],
        mono: ["IBM Plex Mono", "JetBrains Mono", "monospace"],
      },
      colors: {
        paper: "#F3ECDC",
        paperDeep: "#E7DCC0",
        card: "#FBF8F0",
        ink: "#23222A",
        inkSoft: "#6B6659",
        line: "#D9CCA8",
        rail: "#146D6C",
        railDeep: "#0E5150",
        railTint: "#DCEAE6",
        stamp: "#BD4028",
        stampTint: "#F5E1D8",
        gold: "#B9861E",
        goldTint: "#F3E7C9",
        obsidian: "#07090A",
        carbon: "#0E1316",
        panel: "#141B1F",
        divider: "#202A30",
        alertRed: "#EF4444",
        alertRedDeep: "#991B1B",
        alertBg: "#450A0A",
      },
      borderRadius: {
        ticket: "8px",
      },
    },
  },
  plugins: [],
};
