import "server-only";
import { q } from "./db";
import { stars } from "./stars";

// Node positions for the "semantic" nebula layout (docs/07-ui.md, Layouts): each node's mean question
// embedding, projected to 3D so topics that ask similar things sit near each other whatever their branch.
// A small UMAP-style projection over a k-nearest-neighbor graph (PCA start, fixed seed), computed on the
// server from the local embeddings only and cached until the star snapshot changes.

const K = 12;
const EPOCHS = 400;
const NEG = 5;

type V3 = [number, number, number];
let cache: { mtime: number; out: Promise<Record<string, V3>> } | null = null;

export async function semanticCoords(): Promise<Record<string, V3>> {
  const { mtime } = await stars();
  if (cache?.mtime !== mtime) {
    cache = { mtime, out: compute() };
    cache.out.catch(() => { cache = null; });
  }
  return cache.out;
}

function rng(seed: number) {
  return () => {
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

async function compute(): Promise<Record<string, V3>> {
  const rows = await q<{ node_id: string; c: string }>(
    `select q.node_id, avg(q.embedding)::text c
       from questions q join nodes n on n.id = q.node_id and n.status = 'active'
      where q.display_ok and q.embedding is not null
      group by q.node_id order by q.node_id`,
  );
  const n = rows.length;
  if (n < 4) return {};
  const dim = JSON.parse(rows[0].c).length as number;
  const X = new Float32Array(n * dim);
  rows.forEach((r, i) => {
    const v = JSON.parse(r.c) as number[];
    const l = Math.hypot(...v) || 1;
    for (let d = 0; d < dim; d++) X[i * dim + d] = v[d] / l;
  });

  // k nearest neighbors by cosine similarity
  const nbr: number[][] = [];
  const sims = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < n; j++) {
      let s = 0;
      for (let d = 0; d < dim; d++) s += X[i * dim + d] * X[j * dim + d];
      sims[j] = j === i ? -Infinity : s;
    }
    nbr.push([...sims.keys()].sort((a, b) => sims[b] - sims[a]).slice(0, K));
  }
  const edges = new Set<string>();
  const E: [number, number][] = [];
  nbr.forEach((ks, i) => ks.forEach((j) => {
    const key = i < j ? `${i},${j}` : `${j},${i}`;
    if (!edges.has(key)) { edges.add(key); E.push([i, j]); }
  }));

  // PCA start: top 3 components by power iteration on the centered data
  const mean = new Float32Array(dim);
  for (let i = 0; i < n; i++) for (let d = 0; d < dim; d++) mean[d] += X[i * dim + d] / n;
  const C = X.map((v, k) => v - mean[k % dim]);
  const comps: Float32Array[] = [];
  for (let c = 0; c < 3; c++) {
    let v = new Float32Array(dim).map((_, d) => Math.sin(d * (c + 1) * 1.7) + 0.1);
    for (let it = 0; it < 60; it++) {
      const proj = new Float32Array(n);
      for (let i = 0; i < n; i++) { let s = 0; for (let d = 0; d < dim; d++) s += C[i * dim + d] * v[d]; proj[i] = s; }
      const nv = new Float32Array(dim);
      for (let i = 0; i < n; i++) for (let d = 0; d < dim; d++) nv[d] += C[i * dim + d] * proj[i];
      for (const u of comps) { let s = 0; for (let d = 0; d < dim; d++) s += nv[d] * u[d]; for (let d = 0; d < dim; d++) nv[d] -= s * u[d]; }
      const l = Math.hypot(...nv) || 1;
      v = nv.map((x) => x / l);
    }
    comps.push(v);
  }
  const Y: V3[] = [];
  for (let i = 0; i < n; i++) {
    const p = comps.map((u) => { let s = 0; for (let d = 0; d < dim; d++) s += C[i * dim + d] * u[d]; return s; });
    Y.push([p[0], p[1], p[2]]);
  }
  const sd = Math.sqrt(Y.reduce((s, p) => s + p[0] ** 2 + p[1] ** 2 + p[2] ** 2, 0) / n) || 1;
  for (const p of Y) for (let a = 0; a < 3; a++) p[a] = (p[a] / sd) * 6;

  // UMAP-style optimization: neighbors attract, random pairs repel
  const rand = rng(7);
  const clip = (x: number) => Math.max(-4, Math.min(4, x));
  for (let e = 0; e < EPOCHS; e++) {
    const lr = 1 - e / EPOCHS;
    for (const [i, j] of E) {
      const a = Y[i], b = Y[j];
      const d2 = (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2;
      const g = -2 / (1 + d2);
      for (let k = 0; k < 3; k++) {
        const s = clip(g * (a[k] - b[k])) * lr;
        a[k] += s;
        b[k] -= s;
      }
      for (let m = 0; m < NEG; m++) {
        const c = Y[Math.floor(rand() * n)];
        if (c === a) continue;
        const e2 = (a[0] - c[0]) ** 2 + (a[1] - c[1]) ** 2 + (a[2] - c[2]) ** 2;
        const h = 2 / ((0.001 + e2) * (1 + e2));
        for (let k = 0; k < 3; k++) a[k] += clip(h * (a[k] - c[k])) * lr;
      }
    }
  }

  // center, and scale so 95% of nodes sit within radius 1
  const cm: V3 = [0, 0, 0];
  for (const p of Y) for (let a = 0; a < 3; a++) cm[a] += p[a] / n;
  const rs = Y.map((p) => Math.hypot(p[0] - cm[0], p[1] - cm[1], p[2] - cm[2])).sort((a, b) => a - b);
  const R = rs[Math.floor(n * 0.95)] || 1;
  const out: Record<string, V3> = {};
  rows.forEach((r, i) => { out[r.node_id] = [(Y[i][0] - cm[0]) / R, (Y[i][1] - cm[1]) / R, (Y[i][2] - cm[2]) / R]; });
  return out;
}
