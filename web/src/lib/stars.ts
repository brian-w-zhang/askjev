"use client";
// Question stars (docs/07-ui.md): one entry per displayable question, loaded once from /api/stars.
// Positions are node center + (local unit-ball offset × the node's ball radius), turned slowly around
// the node by `spin`. The shader and `starWorld` below use the same formula so picking matches the picture.
import type { Placed } from "./layout";

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
const texts = new Map<string, StarText[]>();
const textLoads = new Map<string, Promise<StarText[]>>();

export function starData(): StarData | null {
  return data;
}

export function loadStars(): Promise<StarData> {
  if (loading) return loading;
  loading = (async () => {
    const [idx, bin] = await Promise.all([
      fetch("/api/stars").then((r) => r.json()) as Promise<{ nodes: [string, number, number][]; count: number }>,
      fetch("/api/stars?bin=1").then((r) => r.arrayBuffer()),
    ]);
    const n = idx.count;
    const dv = new DataView(bin);
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
    for (let i = 0; i < n; i++) {
      const o = i * 12;
      d.node[i] = dv.getUint16(o, true);
      d.local[i * 3] = dv.getInt8(o + 2) / 127;
      d.local[i * 3 + 1] = dv.getInt8(o + 3) / 127;
      d.local[i * 3 + 2] = dv.getInt8(o + 4) / 127;
      d.prim[i] = dv.getUint8(o + 5);
      d.stability[i] = dv.getUint8(o + 6);
      d.humanGap[i] = dv.getUint8(o + 7);
      d.frameGap[i] = dv.getUint8(o + 8);
      d.placement[i] = dv.getUint8(o + 9);
      d.correct[i] = dv.getUint8(o + 10);
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
      .then(({ questions }: { questions: StarText[] }) => {
        texts.set(nodeId, questions);
        return questions;
      });
    textLoads.set(nodeId, p);
    p.catch(() => textLoads.delete(nodeId));
  }
  return p;
}

export function starText(i: number): StarText | undefined {
  if (!data) return undefined;
  const nodeId = data.nodeIds[data.node[i]];
  const off = data.offsets.get(nodeId);
  const list = texts.get(nodeId);
  return off && list ? list[i - off[0]] : undefined;
}

export const metric = (v: number) => (v === 255 ? null : v / 254);

/** World position of star i at time t (seconds): same math as the star vertex shader. */
export function starWorld(i: number, p: Placed, t: number, out: [number, number, number]): [number, number, number] {
  const d = data!;
  const lx = d.local[i * 3] * p.ball, ly = d.local[i * 3 + 1] * p.ball, lz = d.local[i * 3 + 2] * p.ball;
  const a = p.spin * t;
  const c = Math.cos(a), s = Math.sin(a);
  out[0] = p.x + c * lx + s * lz;
  out[1] = p.y + ly;
  out[2] = p.z - s * lx + c * lz;
  return out;
}
