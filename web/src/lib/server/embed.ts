import "server-only";
import fs from "node:fs";
import path from "node:path";
import type { FeatureExtractionPipeline } from "@huggingface/transformers";

// Local BAAI/bge-small-en-v1.5 (ONNX). CLS pooling + L2 normalize matches fastembed: parity cosine 0.999999
// on 5 sample texts (web/scripts/embed_parity.mjs). Never a gateway model. Half precision: 67 MB instead of
// 133, and the same top-1 and top-20 as full precision on 30 test queries (docs/07-ui.md, Search). In
// production the model ships inside the function (web/models, fetched at build by scripts/fetch_model.mjs).
const g = globalThis as unknown as { __askjevEmbed?: Promise<FeatureExtractionPipeline> };
const MODEL = "Xenova/bge-small-en-v1.5";

function extractor(): Promise<FeatureExtractionPipeline> {
  if (!g.__askjevEmbed) {
    g.__askjevEmbed = import("@huggingface/transformers").then(async ({ env, pipeline }) => {
      const bundled = path.join(process.cwd(), "models");
      if (fs.existsSync(path.join(bundled, MODEL))) {
        env.localModelPath = bundled;
        env.allowRemoteModels = false;
      } else if (process.env.VERCEL) {
        env.cacheDir = "/tmp/hf"; // the only writable place on Vercel
      }
      return pipeline("feature-extraction", MODEL, { dtype: "fp16" }) as Promise<FeatureExtractionPipeline>;
    });
  }
  return g.__askjevEmbed;
}

export async function embed(text: string): Promise<Float32Array> {
  const out = await (await extractor())(text, { pooling: "cls", normalize: true });
  return out.data as Float32Array;
}
