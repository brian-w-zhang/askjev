"use client";
import { create } from "zustand";
import type { Filters, Indicator, TreeNode } from "./types";
import type { LayoutKind, V3 } from "./layout";
import type { Theme } from "./theme";

export type ToolId = "layout" | "color" | "filters";

export type PanelView =
  | { kind: "node"; id: string }
  | { kind: "question"; id: string; note?: string }
  | { kind: "ask"; text?: string }
  | { kind: "none" };


interface State {
  nodes: Record<string, TreeNode>;
  children: Record<string, string[]>; // parent id -> ordered child ids (present once expanded)
  born: Record<string, number>; // node id -> performance.now() when it arrived (grow-in animation)
  indicator: Indicator;
  layout: LayoutKind; // how the nebula is arranged (docs/07-ui.md, Layouts)
  theme: Theme;
  tool: ToolId | null; // the search window's open tool panel
  canBack: boolean; // the side panel has somewhere to go back to
  canForward: boolean;
  layoutTick: number; // bumps when a layout computed in the background is ready
  semantic: Record<string, V3> | null; // node positions for the semantic layout, once loaded
  filters: Filters;
  showHidden: boolean;
  panel: PanelView;
  selected: string | null;
  hovered: string | null;
  hoverStar: number; // star index under the pointer, -1 for none
  starsReady: boolean;
  focusStar: number; // the question dot a search or "feeling lucky" flight landed on, -1 for none
  pathA: string[]; // embedding path (root → result node)
  pathB: string[]; // Jev's own walk
  relevance: Record<string, number>; // node id -> 0..1 search relevance (branches brighten)
  mergeNodes: (rows: TreeNode[], expanded: string[]) => void;
  set: (p: Partial<State>) => void;
}

export const useStore = create<State>((set) => ({
  nodes: {},
  children: {},
  born: {},
  indicator: "hemisphere",
  layout: "force",
  theme: "light",
  tool: null,
  canBack: false,
  canForward: false,
  layoutTick: 0,
  semantic: null,
  filters: { kind: "", primitive: "", origin: "" },
  showHidden: false,
  panel: { kind: "none" },
  selected: null,
  hovered: null,
  hoverStar: -1,
  starsReady: false,
  focusStar: -1,
  pathA: [],
  pathB: [],
  relevance: {},
  mergeNodes: (rows, expanded) =>
    set((s) => {
      const nodes = { ...s.nodes };
      const born = { ...s.born };
      const now = typeof performance !== "undefined" ? performance.now() : 0;
      for (const r of rows) {
        if (!nodes[r.id]) born[r.id] = now;
        nodes[r.id] = { ...nodes[r.id], ...r };
      }
      const children = { ...s.children };
      const byParent: Record<string, TreeNode[]> = {};
      for (const r of Object.values(nodes)) if (r.parent_id) (byParent[r.parent_id] ??= []).push(r);
      for (const pid of expanded) {
        children[pid] = (byParent[pid] ?? [])
          .sort((a, b) => (a.ord ?? 999) - (b.ord ?? 999) || a.id.localeCompare(b.id))
          .map((n) => n.id);
      }
      return { nodes, children, born };
    }),
  set: (p) => set(p),
}));

export function filterQuery(f: Filters, showHidden: boolean): string {
  const p = new URLSearchParams();
  if (f.kind) p.set("kind", f.kind);
  if (f.primitive) p.set("primitive", f.primitive);
  if (f.origin) p.set("origin", f.origin);
  if (showHidden) p.set("hidden", "1");
  const s = p.toString();
  return s ? "&" + s : "";
}

const inflight = new Map<string, Promise<void>>();

/** Load `depth` levels below `root` (marks every returned node with children in range as expanded). */
export function loadSubtree(root: string, depth = 2): Promise<void> {
  const key = `sub:${root}:${depth}`;
  if (inflight.has(key)) return inflight.get(key)!;
  const { filters, showHidden } = useStore.getState();
  const p = fetch(`/api/tree?root=${encodeURIComponent(root)}&depth=${depth}${filterQuery(filters, showHidden)}`)
    .then((r) => r.json())
    .then(({ nodes }: { nodes: TreeNode[] }) => {
      const base = nodes.find((n) => n.id === root)?.depth ?? 0;
      const expanded = nodes.filter((n) => n.depth < base + depth).map((n) => n.id);
      useStore.getState().mergeNodes(nodes, expanded);
    });
  inflight.set(key, p);
  p.finally(() => setTimeout(() => inflight.delete(key), 2000));
  return p;
}

/** Make sure every node on `path` (and its siblings) is loaded, so the path can be laid out and lit. */
export async function ensurePath(path: string[]): Promise<void> {
  const { children } = useStore.getState();
  const need = path.slice(0, -1).filter((id) => !children[id]);
  if (!need.length) return;
  const { filters, showHidden } = useStore.getState();
  const r = await fetch(`/api/tree?expand=${need.map(encodeURIComponent).join(",")}${filterQuery(filters, showHidden)}`);
  const { nodes } = (await r.json()) as { nodes: TreeNode[] };
  useStore.getState().mergeNodes(nodes, need);
}

let semanticLoad: Promise<void> | null = null;

/** Node positions for the semantic layout (computed on the server from question embeddings, ~5 s cold). */
export function loadSemantic(): Promise<void> {
  semanticLoad ??= fetch("/api/layout")
    .then((r) => r.json())
    .then(({ coords }: { coords?: Record<string, V3> }) => {
      if (!coords) throw new Error("no semantic layout");
      useStore.getState().set({ semantic: coords });
    })
    .catch((e) => {
      semanticLoad = null;
      throw e;
    });
  return semanticLoad;
}
