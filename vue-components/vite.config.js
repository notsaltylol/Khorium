export default {
  base: "./",
  build: {
    lib: {
      entry: "./src/main.js",
      name: "khorium",
      formats: ["umd"],
      fileName: "khorium",
    },
    rollupOptions: {
      external: ["vue"],
      output: {
        globals: {
          vue: "Vue",
        },
      },
    },
    outDir: "../src/khorium/module/serve",
    assetsDir: ".",
  },
};
