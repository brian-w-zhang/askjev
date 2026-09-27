// Puts the search embedding model inside the app (web/models) so production functions load it from disk
// instead of downloading it on a cold start. Runs before `next build` (package.json "prebuild").
import { env, pipeline } from "@huggingface/transformers";
import { cpSync, existsSync } from "node:fs";
import path from "node:path";

const MODEL = "Xenova/bge-small-en-v1.5";
const out = path.join(process.cwd(), "models", MODEL);
if (existsSync(path.join(out, "onnx", "model_fp16.onnx"))) {
  console.log("model already in", out);
} else {
  env.cacheDir = path.join(process.cwd(), ".hf-cache");
  await pipeline("feature-extraction", MODEL, { dtype: "fp16" }); // downloads into cacheDir
  cpSync(path.join(env.cacheDir, MODEL), out, { recursive: true });
  console.log("model copied to", out);
}
