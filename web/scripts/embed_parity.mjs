// Compare transformers.js (Xenova/bge-small-en-v1.5, fp32) query vectors against the Python
// pipeline's fastembed vectors in parity.json. Requires cosine > 0.99 for every text.
// Usage: node scripts/embed_parity.mjs [cls|mean]
import { readFileSync } from "node:fs";
import { pipeline } from "@huggingface/transformers";

const pooling = process.argv[2] || "cls";
const { texts, vectors } = JSON.parse(readFileSync(new URL("../parity.json", import.meta.url)));
const extractor = await pipeline("feature-extraction", "Xenova/bge-small-en-v1.5", { dtype: "fp32" });
let ok = true;
for (let i = 0; i < texts.length; i++) {
  const out = await extractor(texts[i], { pooling, normalize: true });
  const a = Array.from(out.data);
  const b = vectors[i];
  let dot = 0, na = 0, nb = 0;
  for (let k = 0; k < a.length; k++) { dot += a[k] * b[k]; na += a[k] ** 2; nb += b[k] ** 2; }
  const cos = dot / Math.sqrt(na * nb);
  if (!(cos > 0.99)) ok = false;
  console.log(`${cos.toFixed(6)}  ${texts[i]}`);
}
console.log(`pooling=${pooling} dtype=fp32 -> ${ok ? "PASS" : "FAIL"} (cosine > 0.99 required)`);
process.exit(ok ? 0 : 1);
