import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import path from "path";
// We need loadEnv as we can't use import.meta.env.{whatever} until after this config is loaded
import { defineConfig, loadEnv } from "vite";

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd());
  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        "@": path.resolve(import.meta.dirname, "./src"),
      },
    },
    server: {
      host: "0.0.0.0",
      allowedHosts: ["capstoneteam4.com", "test-frontend.capstoneteam4.com"],
      proxy: {
        "/api": {
          target: env.VITE_API_URL || "http://backend:8000",
          changeOrigin: true,
        },
      },
    },
    test: {
      globals: true,
      environment: "jsdom",
      setupFiles: "./src/tests/setup.js",
    },
  };
});
