import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import { VitePWA } from "vite-plugin-pwa";

// The dev server proxies /api to FastAPI so the browser sees one origin,
// matching production behind Caddy (see docs/adr/0007-cookie-session-auth.md).
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      manifest: {
        name: "Family Hub",
        short_name: "Family Hub",
        description: "Our household's shared systems",
        lang: "zh-TW",
        theme_color: "#2f6f4f",
        background_color: "#ffffff",
        display: "standalone",
        start_url: "/",
        icons: [{ src: "icon.svg", sizes: "any", type: "image/svg+xml", purpose: "any" }],
      },
      workbox: {
        // Never cache API responses: they hold private, fast-changing data.
        navigateFallbackDenylist: [/^\/api\//],
      },
    }),
  ],
  server: {
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
