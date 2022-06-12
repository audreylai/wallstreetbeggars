module.exports = {
  content: ["./templates/**/*.{html,js}"],
  darkMode: "class",
  theme: {
    extend: {
      backgroundImage: (theme) => ({
        check: "url('/static/check.svg')",
      }),
    },
  },
  variants: {
    extend: {
      backgroundColor: ["checked"],
      borderColor: ["checked"],
      inset: ["checked"],
      zIndex: ["hover", "active"],
    },
  },
  plugins: [],
};
