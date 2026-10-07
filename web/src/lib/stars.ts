"use client";
// Question stars (docs/07-ui.md): one entry per displayable question, loaded once from /api/stars.
// Positions are node center + the local unit-ball offset shaped by the layout (`starLocal`), turned slowly around
// the node by `spin`. The shader and `starWorld` below use the same formula so picking matches the picture.
import { starLocal, type Placed, type V3 } from "./layout";
import { bootFetch } from "./boot";

export interface StarData {
  count: number;
  nodeIds: string[]; // node index -> node id
  offsets: Map<string, [number, number]>; // node id -> [first star, count]
  node: Uint16Array; // star -> node index
  local: Float32Array; // star -> unit-ball offset (xyz)
  prim: Uint8Array; // 0 noul, 1 choice, 2 score
  stability: Uint8Array; // 0..254, 255 = none (also humanGap, frameGap, placement)
  humanGap: Uint8Array;
  frameGap: Uint8Array;
  placement: Uint8Array;
  correct: Uint8Array; // 0 unknown, 1 correct, 2 wrong
}

export interface StarText { id: string; text: string; label: string; primitive: string }

let data: StarData | null = null;
let loading: Promise<StarData> | null = null;
let counts: Map<string, number> | null = null;
let indexing: Promise<StarIndex> | null = null;
const texts = new Map<string, StarText[]>();
const textLoads = new Map<string, Promise<StarText[]>>();

interface StarIndex { nodes: [string, number, number][]; count: number; version: string }

export function starData(): StarData | null {
  return data;
}

/** Questions per node, from the small index: enough to lay the map out while the dots are still downloading. */
export function starCounts(): Map<string, number> | null {
  return counts;
}

export function loadStarIndex(): Promise<StarIndex> {
  indexing ??= bootFetch("/api/stars")
    .then((r) => r.json())
    .then((idx: StarIndex) => {
      counts = new Map(idx.nodes.map(([id, , n]) => [id, n]));
      return idx;
    });
  return indexing;
}

const binUrl = (v: string) => `/api/stars?bin=1&v=${encodeURIComponent(v)}`;
const fetchBin = (v: string) => bootFetch(binUrl(v)).then((r) => r.arrayBuffer());

/**
 * Every dot. The page names the snapshot's version (and starts fetching the dots by it), so the 12 MB start downloading
 * alongside the index instead of after it; asked for by version, the browser keeps them for return visits.
 */
export function loadStars(version?: string): Promise<StarData> {
  if (loading) return loading;
  loading = (async () => {
    const early = version ? fetchBin(version) : null;
    const idx = await loadStarIndex();
    // the page was built against another snapshot: fetch the one the index names (the early one is wasted)
    const bin = await (early && version === idx.version ? early : fetchBin(idx.version));
    const n = idx.count;
    const d: StarData = {
      count: n,
      nodeIds: idx.nodes.map((x) => x[0]),
      offsets: new Map(idx.nodes.map(([id, off, c]) => [id, [off, c]])),
      node: new Uint16Array(n),
      local: new Float32Array(n * 3),
      prim: new Uint8Array(n),
      stability: new Uint8Array(n),
      humanGap: new Uint8Array(n),
      frameGap: new Uint8Array(n),
      placement: new Uint8Array(n),
      correct: new Uint8Array(n),
    };
    // 12 bytes per star (scripts/star_layout.py): u16 node (little-endian), 3 × i8 offset, 6 × u8, 1 spare
    const u = new Uint8Array(bin);
    const s8 = new Int8Array(bin);
    for (let i = 0, o = 0; i < n; i++, o += 12) {
      d.node[i] = u[o] | (u[o + 1] << 8);
      d.local[i * 3] = s8[o + 2] / 127;
      d.local[i * 3 + 1] = s8[o + 3] / 127;
      d.local[i * 3 + 2] = s8[o + 4] / 127;
      d.prim[i] = u[o + 5];
      d.stability[i] = u[o + 6];
      d.humanGap[i] = u[o + 7];
      d.frameGap[i] = u[o + 8];
      d.placement[i] = u[o + 9];
      d.correct[i] = u[o + 10];
    }
    data = d;
    return d;
  })();
  return loading;
}

/** Question text for a node's stars, in star order (cached). */
export function loadTexts(nodeId: string): Promise<StarText[]> {
  const have = texts.get(nodeId);
  if (have) return Promise.resolve(have);
  let p = textLoads.get(nodeId);
  if (!p) {
    p = fetch(`/api/stars/text?node=${encodeURIComponent(nodeId)}`)
      .then((r) => r.json())
      .then(({ questions }: { questions: (Omit<StarText, "label"> & { label?: string })[] }) => {
        // the server leaves out a label that's just the text
        const list = questions.map((q) => ({ ...q, label: q.label ?? (q.text.length > 140 ? q.text.slice(0, 139).trimEnd() + "…" : q.text) }));
        texts.set(nodeId, list);
        return list;
      });
    textLoads.set(nodeId, p);
    p.catch(() => textLoads.delete(nodeId));
  }
  return p;
}

/** The question id of star i: from its node's texts when they're here, else one small lookup. */
export async function starId(i: number): Promise<string | undefined> {
  const t = starText(i);
  if (t) return t.id;
  const d = data!;
  const nodeId = d.nodeIds[d.node[i]];
  const k = i - d.offsets.get(nodeId)![0];
  const r = await fetch(`/api/stars/text?node=${encodeURIComponent(nodeId)}&at=${k}`);
  return r.ok ? ((await r.json()) as { id?: string }).id : undefined;
}

export function starText(i: number): StarText | undefined {
  if (!data) return undefined;
  const nodeId = data.nodeIds[data.node[i]];
  const off = data.offsets.get(nodeId);
  const list = texts.get(nodeId);
  return off && list ? list[i - off[0]] : undefined;
}

export const metric = (v: number) => (v === 255 ? null : v / 254);

const tmp: V3 = [0, 0, 0];

/** World position of star i at time t (seconds): same math as the star vertex shader. */
export function starWorld(i: number, p: Placed, t: number, out: [number, number, number]): [number, number, number] {
  const d = data!;
  const [lx, ly, lz] = starLocal(d.local[i * 3], d.local[i * 3 + 1], d.local[i * 3 + 2], p, tmp);
  const a = p.spin * t;
  const c = Math.cos(a), s = Math.sin(a);
  out[0] = p.x + c * lx + s * lz;
  out[1] = p.y + ly;
  out[2] = p.z - s * lx + c * lz;
  return out;
}
