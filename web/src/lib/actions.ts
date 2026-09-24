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

/**
 * The search journey (docs/07-ui.md): a light runs root → topic with the camera following, the camera
 * closes in on the question's own dot, and only then does its card slide in.
 */
export async function goToQuestion(path: string[], questionId: string) {
  anim.trackStar = -1;
  useStore.getState().set({ panel: { kind: "none" }, focusStar: -1 });
  const nodeId = path[path.length - 1];
  const where = starIndex(nodeId, questionId);
  await travel(path);
  const i = await where;
  if (i >= 0) await landOnStar(i);
  openQuestion(questionId);
}

/** "I'm feeling lucky": any displayable question, uniformly at random, with the same journey. */
export async function feelingLucky() {
  const d = starData();
  if (!d) return;
  const i = Math.floor(Math.random() * d.count);
  const nodeId = d.nodeIds[d.node[i]];
  const q = (await loadTexts(nodeId))[i - d.offsets.get(nodeId)![0]];
  if (q) await goToQuestion(ancestors(nodeId), q.id);
}

export interface Walk { node: string; confidence: number; separation: number; runner_up?: string; path_probs: [string, string, number][] }

/** Jev's own walk as a second (gold) light; it forks visibly where it leaves the embedding path. */
export async function showJevWalk(query: string): Promise<Walk | { error: string }> {
  const r = await fetch(`/api/walk?q=${encodeURIComponent(query)}`);
  const data = await r.json();
  if (!r.ok || data.error) return { error: data.error ?? `walk failed (${r.status})` };
  const walk = data as Walk;
  const path = ["root", ...walk.path_probs.map((p) => p[0])];
  await ensurePath(path);
  await frames(2);
  const a = anim.A.path;
  let fork = -1;
  for (let i = 0; i < path.length; i++) if (a[i] !== path[i]) { fork = i; break; }
  if (fork === -1 && a.length > path.length) fork = path.length; // Jev stopped higher up
  anim.fork = fork > 0 && fork < path.length ? fork : -1;
  useStore.getState().set({ pathB: path });
  // Wait for the embedding light to land, then send Jev's light down the tree.
  const waitA = Math.max(0, anim.A.t0 * 1000 + lightMs(a.length, PER_LEVEL) - performance.now());
  await new Promise((res) => setTimeout(res, waitA + 150));
  startLight("B", path, PER_LEVEL);
  if (anim.fork > 0) {
    // Frame both endpoints once Jev's light has passed the fork.
    setTimeout(() => {
      const pa = anim.placed.get(a[a.length - 1]);
      const pb = anim.placed.get(path[path.length - 1]);
      if (!pa || !pb || anim.userMoved > anim.B.t0) return;
      const span = Math.hypot(pa.x - pb.x, pa.y - pb.y, pa.z - pb.z);
      flyTo([(pa.x + pb.x) / 2, (pa.y + pb.y) / 2, (pa.z + pb.z) / 2], Math.max(14, span * 1.4 + 8), 1.4);
    }, lightMs(anim.fork + 1, PER_LEVEL));
  }
  return walk;
}

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
