import path from "path"
import react from "@vitejs/plugin-react"
import { defineConfig, loadEnv } from "vite"

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "")
  const base = env.VITE_BASE || "/farseer/dev/"
  const backendPort = env.VITE_BACKEND_PORT || "8173"
  
  return {
    plugins: [react()],
    base,
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
      port: parseInt(env.VITE_PORT || "5173"),
      proxy: {
        [`${base}api`]: {
          target: `http://localhost:${backendPort}`,
          changeOrigin: true,
          rewrite: (path) => path.replace(new RegExp(`^${base}api`), "/api"),
        },
        [`${base}docs`]: {
          target: `http://localhost:${backendPort}`,
          changeOrigin: true,
        },
        [`${base}openapi.json`]: {
          target: `http://localhost:${backendPort}`,
          changeOrigin: true,
        },
        [`${base}redoc`]: {
          target: `http://localhost:${backendPort}`,
          changeOrigin: true,
        },
      },
    },
  }
})
