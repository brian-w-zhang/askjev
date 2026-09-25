"use client";
import { anim, lightMs, now, startLight } from "./anim";
import { loadTexts, starData, starWorld } from "./stars";
import { ensurePath, filterQuery, loadSubtree, useStore } from "./store";
import { flyTo, frameDist } from "@/components/scene/CameraRig";
import type { TreeNode } from "./types";

const PER_LEVEL = 0.4; // seconds per tree level: slow enough for the eye to follow

const frames = (n = 2) => new Promise<void>((r) => {
  const step = (k: number) => (k <= 0 ? r() : requestAnimationFrame(() => step(k - 1)));
  step(n);
});

export function selectNode(id: string, opts: { fly?: boolean; panel?: boolean } = {}) {
  const s = useStore.getState();
  anim.trackStar = -1;
  s.set({ selected: id, focusStar: -1, ...(opts.panel === false ? {} : { panel: { kind: "node", id } }) });
  const p = anim.placed.get(id);
  const n = s.nodes[id];
  if (p && n && opts.fly !== false) flyTo([p.x, p.y, p.z], frameDist(id));
  if (n && n.n_children > 0 && !s.children[id]) loadSubtree(id, 2);
}

export function openQuestion(id: string, note?: string) {
  useStore.getState().set({ panel: { kind: "question", id, note } });
}

/** Light pulse root → ... → node at a human pace, with the camera following. Resolves on arrival. */
export async function travel(path: string[]): Promise<void> {
  if (!path.length) return;
  await ensurePath(path);
  await frames(2); // let the layout pick up newly loaded rings
  const s = useStore.getState();
  s.set({ pathA: path, pathB: [], selected: path[path.length - 1] });
  anim.B.active = false;
  anim.fork = -1;
  startLight("A", path, PER_LEVEL);
  anim.follow = "A";
  await new Promise((r) => setTimeout(r, lightMs(path.length, PER_LEVEL) + 120));
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

/** Root → ... → node ids for a node, from the loaded tree. */
export function ancestors(id: string): string[] {
  const { nodes } = useStore.getState();
  const out: string[] = [];
  let n: TreeNode | undefined = nodes[id];
  while (n) {
    out.unshift(n.id);
    n = n.parent_id ? nodes[n.parent_id] : undefined;
  }
  return out;
}

/** Star index of a question (its node's texts load if needed), or -1. */
async function starIndex(nodeId: string, questionId: string): Promise<number> {
  const off = starData()?.offsets.get(nodeId);
  if (!off) return -1;
  const k = (await loadTexts(nodeId)).findIndex((q) => q.id === questionId);
  return k < 0 ? -1 : off[0] + k;
}

/** Close in on one question dot and keep it centered; resolves when the camera has arrived. */
export async function landOnStar(i: number, dur = 1.4) {
  const d = starData();
  const p = d ? anim.placed.get(d.nodeIds[d.node[i]]) : undefined;
  if (!p) return;
  const at = starWorld(i, p, now() + dur, [0, 0, 0]); // where the dot will be when we get there
  anim.follow = null;
  useStore.getState().set({ focusStar: i });
  flyTo(at, Math.max(1.6, p.ball * 0.45), dur);
  await sleep(dur * 1000 + 60);
  anim.trackStar = i;
}

const JOURNEY_PER_LEVEL = 0.6; // seconds per level on a journey: slow enough to read each node's chip
let journeyRun = 0;
const last = <T,>(a: T[]) => a[a.length - 1];

async function fetchWalk(query: string): Promise<Walk | { error: string }> {
  try {
    const r = await fetch(`/api/walk?q=${encodeURIComponent(query)}`);
    const d = await r.json();
    return !r.ok || d.error ? { error: d.error ?? `walk failed (${r.status})` } : (d as Walk);
  } catch (e) {
    return { error: (e as Error).message };
  }
}

/**
 * The journey (docs/07-ui.md). Jev walks the tree for `query` from the root, one decision per level (green,
 * with its confidence at each node). If the chosen question lives elsewhere, an ink hop continues from where
 * the two paths part. Then the camera closes in on the question's dot and only then does its card open.
 * Without a query (or with "Show Jev's path" off) the ink tree path runs alone.
 */
export async function journey(o: { query?: string; path: string[]; questionId?: string }) {
  const run = ++journeyRun;
  const live = () => run === journeyRun;
  const tree = o.path;
  const s = useStore.getState();
  const useJev = !!o.query?.trim() && s.showJevPath;
  anim.trackStar = -1;
  anim.fork = -1;
  anim.A.active = anim.B.active = false;
  anim.journey = { phase: useJev ? "thinking" : "hop", probs: new Map() };
  s.set({
    panel: { kind: "none" }, focusStar: -1, pathA: [], pathB: [], selected: null,
    jevWalk: useJev ? { state: "walking", query: o.query, target: last(tree) } : { state: "idle" },
  });
  // settle near the root while Jev reads the query
  const root = anim.placed.get("root");
  if (root) flyTo([root.x, root.y, root.z], frameDist("root") * 0.55, 1.1);
  const t0 = performance.now();
  let jev: string[] | null = null;
  if (useJev) {
    const w = await fetchWalk(o.query!);
    if (!live()) return;
    if ("error" in w) {
      useStore.getState().set({ jevWalk: { state: "error", error: w.error, query: o.query, target: last(tree) } });
    } else {
      jev = ["root", ...w.path_probs.map((p) => p[0])];
      anim.journey.probs = new Map(w.path_probs.map((p) => [p[0], p[2]]));
      useStore.getState().set({ jevWalk: { state: "done", query: o.query, node: w.node, confidence: w.confidence, target: last(tree) } });
    }
  }
  await sleep(Math.max(0, 1150 - (performance.now() - t0))); // the camera arrives before anyone walks
  if (!live()) return;

  if (jev) {
    anim.journey.phase = "jev";
    useStore.getState().set({ pathB: jev });
    startLight("B", jev, JOURNEY_PER_LEVEL);
    anim.follow = "B";
    await sleep(lightMs(jev.length, JOURNEY_PER_LEVEL) + 300);
    if (!live()) return;
  }
  if (!jev || last(jev) !== last(tree)) {
    // shared prefix with Jev's path is already lit; the ink light picks up where the paths part
    let shared = 0;
    while (jev && shared < Math.min(jev.length, tree.length) && jev[shared] === tree[shared]) shared++;
    const skip = Math.max(0, shared - 1);
    anim.fork = jev && shared < jev.length ? shared : -1;
    anim.journey.phase = "hop";
    useStore.getState().set({ pathA: tree });
    startLight("A", tree, JOURNEY_PER_LEVEL);
    anim.A.t0 -= skip * JOURNEY_PER_LEVEL;
    anim.follow = "A";
    await sleep(lightMs(tree.length - skip, JOURNEY_PER_LEVEL) + 300);
    if (!live()) return;
  }
  anim.follow = null;
  useStore.getState().set({ selected: last(tree) });
  if (o.questionId) {
    const i = await starIndex(last(tree), o.questionId);
    if (!live()) return;
    if (i >= 0) await landOnStar(i);
    if (!live()) return;
    anim.journey.phase = "landed";
    openQuestion(o.questionId);
  } else {
    anim.journey.phase = "landed";
    selectNode(last(tree));
  }
}

/** "I'm feeling lucky": any displayable question, uniformly at random; Jev walks it by its own text. */
export async function feelingLucky() {
  const d = starData();
  if (!d) return;
  const i = Math.floor(Math.random() * d.count);
  const nodeId = d.nodeIds[d.node[i]];
  const q = (await loadTexts(nodeId))[i - d.offsets.get(nodeId)![0]];
  if (q) await journey({ query: q.text, path: ancestors(nodeId), questionId: q.id });
}

export interface Walk { node: string; confidence: number; separation: number; runner_up?: string; path_probs: [string, string, number][] }

/** Refresh `n_match` on every node after a filter change (the whole tree is loaded, so ask for all of it). */
export async function refreshFilters() {
  const s = useStore.getState();
  const expanded = Object.keys(s.children);
  if (!expanded.length) return;
  const r = await fetch(`/api/tree?root=root&depth=12${filterQuery(s.filters, s.showHidden)}`);
  const { nodes } = await r.json();
  for (const n of nodes) if (!("n_match" in n)) n.n_match = undefined;
  useStore.getState().mergeNodes(nodes, expanded);
}
