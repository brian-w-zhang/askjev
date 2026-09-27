import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  serverExternalPackages: ["@huggingface/transformers", "onnxruntime-node"],
  devIndicators: false,
  // R3F's renderer is torn down by StrictMode's dev-only double mount (WebGL "Context Lost").
  reactStrictMode: false,
  // Production functions (docs/07-ui.md, Deployment): only the search route needs the embedding model and
  // its Linux runtime; everything else stays well under Vercel's function size limit.
  // Read-only data changes only when the database is synced (and a deploy clears the CDN), so Vercel's edge
  // serves repeats: most visits never reach a function or the database. Browsers still revalidate.
  async headers() {
    const edge = [{ key: "Cache-Control", value: "public, max-age=0, s-maxage=86400, stale-while-revalidate=604800" }];
    return ["/api/tree", "/api/node/:id*", "/api/question/:id*", "/api/stars", "/api/stars/:path*", "/api/layout", "/api/search"].map((source) => ({ source, headers: edge }));
  },
  outputFileTracingIncludes: {
    // onnxruntime-node is loaded by a dynamic import the tracer can't follow, so it's listed explicitly
    "/api/search": ["./models/**/*", "./node_modules/onnxruntime-node/package.json",
      "./node_modules/onnxruntime-node/dist/**/*", "./node_modules/onnxruntime-node/bin/napi-v*/linux/x64/**/*", "./node_modules/onnxruntime-common/**/*"],
  },
  outputFileTracingExcludes: {
    "/**": ["./node_modules/onnxruntime-node/bin/napi-v*/darwin/**", "./node_modules/onnxruntime-node/bin/napi-v*/win32/**", "./node_modules/@huggingface/transformers/.cache/**", "./node_modules/onnxruntime-web/**", "./.hf-cache/**"],
  },
};

export default nextConfig;
