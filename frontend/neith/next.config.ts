import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Required for the Docker multi-stage build (frontend/neith/Dockerfile).
  // Produces a self-contained server bundle under .next/standalone/.
  output: "standalone",
};

export default nextConfig;
