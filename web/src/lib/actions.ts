"use client";
import { anim, lightMs, now, startLight } from "./anim";
import { loadTexts, starData, starWorld } from "./stars";
import { ensurePath, filterQuery, loadSubtree, useStore, type PanelView } from "./store";
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

const JOURNEY_PER_LEVEL = 0.45; // seconds per level on a journey: quick, but slow enough to read each node
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
 * The journey (docs/07-ui.md): from a search result or a lucky pick, the camera flies straight down the
 * question's stored path, one level at a time behind a lit trail, closes in on the question's dot, and only
 * then opens its card. No Jev call on the way: the result was already chosen by the embedding search and
 * Jev's rerank. (Jev's own walk is on demand, from the card: `jevFile`.)
 */
export async function journey(o: { path: string[]; questionId?: string }) {
  const run = ++journeyRun;
  const live = () => run === journeyRun;
  const tree = o.path;
  anim.trackStar = -1;
  anim.fork = -1;
  anim.A.active = anim.B.active = false;
  anim.journey = { phase: "hop", probs: new Map() };
  useStore.getState().set({ panel: { kind: "none" }, focusStar: -1, pathA: [], pathB: [], selected: null });
  await ensurePath(tree);
  await frames(2); // let the layout pick up newly loaded rings
  if (!live()) return;
  useStore.getState().set({ pathA: tree });
  startLight("A", tree, JOURNEY_PER_LEVEL);
  anim.follow = "A";
  await sleep(lightMs(tree.length, JOURNEY_PER_LEVEL) + 300);
  if (!live()) return;
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

/**
 * "How would Jev file this?" (docs/07-ui.md): Jev walks the tree for the question's text, one decision per
 * level, as a green trail with its confidence at each node, beside the ink trail of where the question is
 * stored, so any disagreement shows where the paths part. One /api/walk call, only when asked.
 */
export async function jevFile(text: string, stored: string[]): Promise<Walk | { error: string }> {
  const run = ++journeyRun;
  const w = await fetchWalk(text);
  if ("error" in w || run !== journeyRun) return w;
  const jev = ["root", ...w.path_probs.map((p) => p[0])];
  await ensurePath([...stored, ...jev]);
  await frames(2);
  let shared = 0;
  while (shared < Math.min(jev.length, stored.length) && jev[shared] === stored[shared]) shared++;
  anim.fork = shared < jev.length ? shared : -1;
  anim.trackStar = -1;
  anim.journey = { phase: "jev", probs: new Map(w.path_probs.map((p) => [p[0], p[2]])) };
  useStore.getState().set({ pathA: stored, pathB: jev });
  startLight("A", stored, 0.001); // where it's stored: lit at once, in ink
  startLight("B", jev, JOURNEY_PER_LEVEL);
  anim.follow = "B";
  await sleep(lightMs(jev.length, JOURNEY_PER_LEVEL) + 300);
  if (run === journeyRun) {
    anim.follow = null;
    anim.journey.phase = "landed";
  }
  return w;
}

/** "I'm feeling lucky": any displayable question, uniformly at random. */
export async function feelingLucky() {
  const d = starData();
  if (!d) return;
  const i = Math.floor(Math.random() * d.count);
  const nodeId = d.nodeIds[d.node[i]];
  const q = (await loadTexts(nodeId))[i - d.offsets.get(nodeId)![0]];
  if (q) await journey({ path: ancestors(nodeId), questionId: q.id });
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

// Side panel history (docs/07-ui.md, Side panel): like a browser, every topic or question the panel moves to
// is remembered until it closes, so Back and Forward retrace the way you came.
const back: PanelView[] = [];
const fwd: PanelView[] = [];
let stepping = false;
const same = (a: PanelView, b: PanelView) => a.kind === b.kind && (a as { id?: string }).id === (b as { id?: string }).id;

useStore.subscribe((s, prev) => {
  if (s.panel === prev.panel) return;
  if (s.panel.kind === "none") { back.length = 0; fwd.length = 0; }
  else if (stepping) stepping = false;
  else if (prev.panel.kind !== "none" && !same(prev.panel, s.panel)) { back.push(prev.panel); fwd.length = 0; }
  const canBack = back.length > 0, canForward = fwd.length > 0;
  if (s.canBack !== canBack || s.canForward !== canForward) useStore.setState({ canBack, canForward });
});

function show(v: PanelView) {
  stepping = true;
  if (v.kind === "node") selectNode(v.id);
  else useStore.getState().set({ panel: v });
}

export function goBack() {
  const v = back.pop();
  if (!v) return;
  fwd.push(useStore.getState().panel);
  show(v);
}

export function goForward() {
  const v = fwd.pop();
  if (!v) return;
  back.push(useStore.getState().panel);
  show(v);
}

/** Open a question from its dot (or its label): fly in to it, then open its card. */
export async function openStar(i: number) {
  const d = starData();
  if (!d) return;
  const nodeId = d.nodeIds[d.node[i]];
  const q = (await loadTexts(nodeId))[i - d.offsets.get(nodeId)![0]];
  if (!q) return;
  useStore.getState().set({ selected: nodeId, hoverStar: -1 });
  await landOnStar(i, 1.0);
  openQuestion(q.id);
}
