/** @type {import('tailwindcss').Config} */
//tells tailwind where to look for classes to include in the final CSS build
export default {
    content: [
      "./index.html",
      "./src/**/*.{js,ts,jsx,tsx}",
    ],
    corePlugins: {
      preflight: false, // Disable Tailwind's base styles to prevent conflicts with MUI
    },
    theme: {
      extend: {},
    },
    plugins: [],
  }