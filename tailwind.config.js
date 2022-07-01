module.exports = {
  content: ["./templates/**/*.{html,js,css}"],
  darkMode: "class",
  theme: {
    extend: {
      backgroundImage: (theme) => ({
        check: "url('/static/check.svg')",
      }),
    },
  },
  plugins: [],
};
