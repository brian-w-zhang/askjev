import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  serverExternalPackages: ["@huggingface/transformers", "onnxruntime-node"],
  devIndicators: false,
  // R3F's renderer is torn down by StrictMode's dev-only double mount (WebGL "Context Lost").
  reactStrictMode: false,
};

export default nextConfig;
