import "server-only";
import type { FeatureExtractionPipeline } from "@huggingface/transformers";

// Local BAAI/bge-small-en-v1.5 (ONNX, fp32). CLS pooling + L2 normalize matches fastembed:
// parity cosine 0.999999 on 5 sample texts (web/scripts/embed_parity.mjs). Never a gateway model.
const g = globalThis as unknown as { __askjevEmbed?: Promise<FeatureExtractionPipeline> };

function extractor(): Promise<FeatureExtractionPipeline> {
  if (!g.__askjevEmbed) {
    g.__askjevEmbed = import("@huggingface/transformers").then(
      ({ pipeline }) =>
        pipeline("feature-extraction", "Xenova/bge-small-en-v1.5", { dtype: "fp32" }) as Promise<FeatureExtractionPipeline>,
    );
  }
  return g.__askjevEmbed;
}

export async function embed(text: string): Promise<Float32Array> {
  const out = await (await extractor())(text, { pooling: "cls", normalize: true });
  return out.data as Float32Array;
}
