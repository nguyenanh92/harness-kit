import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { readFileSync } from "fs";
import { homedir } from "os";
import { join } from "path";

const certsDir = join(homedir(), ".office-addin-dev-certs");

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    https: {
      cert: readFileSync(join(certsDir, "localhost.crt")),
      key: readFileSync(join(certsDir, "localhost.key")),
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
  },
});
