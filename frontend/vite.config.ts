import path from "path"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

export default defineConfig({
  plugins: [react()],
  base: "/farseer/dev/",
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  optimizeDeps: {
    include: ["lightweight-charts"],
  },
  server: {
    host: "0.0.0.0",
    port: parseInt(process.env.VITE_PORT || "5173"),
    proxy: {
      "/farseer/dev/api": {
        target: "http://localhost:8173",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/farseer\/dev\/api/, "/api"),
      },
      "/farseer/dev/docs": {
        target: "http://localhost:8173",
        changeOrigin: true,
      },
      "/farseer/dev/openapi.json": {
        target: "http://localhost:8173",
        changeOrigin: true,
      },
      "/farseer/dev/redoc": {
        target: "http://localhost:8173",
        changeOrigin: true,
      },
    },
  },
})
