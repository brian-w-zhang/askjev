"use client";
import { anim, lightMs, startLight } from "./anim";
import { ensurePath, filterQuery, loadSubtree, useStore } from "./store";
import { flyTo } from "@/components/scene/CameraRig";

const DIST = [82, 50, 34, 24, 19, 16, 14];
const PER_LEVEL = 0.4; // seconds per tree level: slow enough for the eye to follow

const frames = (n = 2) => new Promise<void>((r) => {
  const step = (k: number) => (k <= 0 ? r() : requestAnimationFrame(() => step(k - 1)));
  step(n);
});

export function selectNode(id: string, opts: { fly?: boolean; panel?: boolean } = {}) {
  const s = useStore.getState();
  s.set({ selected: id, ...(opts.panel === false ? {} : { panel: { kind: "node", id } }) });
  const p = anim.placed.get(id);
  const n = s.nodes[id];
  if (p && n && opts.fly !== false) flyTo([p.x, p.y, p.z], DIST[Math.min(n.depth, DIST.length - 1)]);
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
      const span = Math.hypot(pa.x - pb.x, pa.z - pb.z);
      flyTo([(pa.x + pb.x) / 2, (pa.y + pb.y) / 2, (pa.z + pb.z) / 2], Math.max(24, span * 1.35 + 10), 1.4);
    }, lightMs(anim.fork + 1, PER_LEVEL));
  }
  return walk;
}

/** Refresh `n_match` on everything loaded after a filter change. */
export async function refreshFilters() {
  const s = useStore.getState();
  const expanded = Object.keys(s.children);
  if (!expanded.length) return;
  const r = await fetch(`/api/tree?expand=${expanded.map(encodeURIComponent).join(",")}${filterQuery(s.filters, s.showHidden)}`);
  const { nodes } = await r.json();
  for (const n of nodes) if (!("n_match" in n)) n.n_match = undefined;
  useStore.getState().mergeNodes(nodes, expanded);
}
