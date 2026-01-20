import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  experimental: {
    // @ts-expect-error: Turbopack root config is new
    turbopack: {
      root: "../../"
    }
  }
};

export default nextConfig;
