"use client";
import { useState } from "react";
import { Info } from "./Info";
import { useStore } from "@/lib/store";
import { useResource, prefetch } from "@/lib/cache";
import { nodeUrl, questionUrl } from "@/lib/panelData";
import { openQuestion, selectNode } from "@/lib/actions";
import { attention, rampColor } from "@/lib/color";
import { starData } from "@/lib/stars";
import type { Indicator } from "@/lib/types";
import { Crumbs } from "./Panel";

interface NodeData {
  node: { id: string; label: string; description: string; not_for: string | null; examples: string[]; hemisphere: string; depth: number; source: string; locked: boolean };
  stats: { scope: string; n_questions: number; n_asked: number; kind_counts: Record<string, number> | null; stability: number | null; frame_gap: number | null; human_gap: number | null; calibration_ece: number | null; placement_conf: number | null; fragile_share: number | null }[];
  ancestors: { id: string; label: string }[];
  children: { id: string; label: string; n_questions: number }[];
  questions: { id: string; text: string; primitive: string; kind: string | null; shape: string | null; ask_count: number; display_ok: boolean; top: string | null; p_top: number | null; stability: number | null; node_id: string }[];
  total: number;
  next: string | null; // cursor for the next page of questions (null: that's all of them)
  shown: number; // displayable questions in the whole branch
}

const IND: { k: Indicator | "fragile_share"; label: string; fmt: (v: number) => string }[] = [
  { k: "stability", label: "Stability", fmt: (v) => `${Math.round(v * 100)}%` },
  { k: "human_gap", label: "Human gap", fmt: (v) => v.toFixed(2) },
  { k: "frame_gap", label: "Frame gap", fmt: (v) => v.toFixed(2) },
  { k: "placement_conf", label: "Placement confidence", fmt: (v) => `${Math.round(v * 100)}%` },
  { k: "calibration_ece", label: "Calibration error", fmt: (v) => v.toFixed(3) },
  { k: "fragile_share", label: "Fragile questions", fmt: (v) => `${Math.round(v * 100)}%` },
];
const KIDS_SHOWN = 12;
const KIND_COLORS = ["#4B5BD6", "#F386A1", "#E8663D", "#D45BB6", "#7D89E6", "var(--ink)", "#ABBAB9", "#E9A23B"];

/**
 * What the map already knows about a topic, so the panel can open on a click without waiting for the server: its
 * name, description, indicators and subtopics from the loaded tree, and its shown questions counted from the dots.
 * The question list (and the "not here" notes) fill in when the topic's data arrives.
 */
function fromTree(id: string): NodeData | undefined {
  const s = useStore.getState();
  const n = s.nodes[id];
  if (!n) return undefined;
  const ancestors: NodeData["ancestors"] = [];
  for (let a: typeof n | undefined = n; a; a = a.parent_id ? s.nodes[a.parent_id] : undefined) ancestors.unshift({ id: a.id, label: a.label });
  const d = starData();
  let shown: number | undefined;
  if (d) {
    shown = 0;
    for (const [nid, [, c]] of d.offsets) if (id === "root" || nid === id || nid.startsWith(id + ".")) shown += c;
  }
  const filtered = s.filters.kind || s.filters.primitive || s.filters.origin || s.showHidden;
  return {
    node: { id, label: n.label, description: n.description, not_for: null, examples: [], hemisphere: n.hemisphere, depth: n.depth, source: "", locked: false },
    stats: [{ scope: "subtree", n_questions: n.n_questions, n_asked: n.n_asked, kind_counts: n.kind_counts, stability: n.stability, frame_gap: n.frame_gap,
      human_gap: n.human_gap, calibration_ece: n.calibration_ece, placement_conf: n.placement_conf, fragile_share: n.fragile_share }],
    ancestors,
    children: (s.children[id] ?? []).map((c) => ({ id: c, label: s.nodes[c]?.label ?? c, n_questions: s.nodes[c]?.n_questions ?? 0 })),
    questions: [],
    total: filtered ? n.n_match ?? 0 : shown ?? n.n_questions,
    next: null,
    shown: shown ?? n.n_questions,
  };
}

export function NodeView({ id, onClose }: { id: string; onClose: () => void }) {
  const filters = useStore((s) => s.filters);
  const showHidden = useStore((s) => s.showHidden);
  const [scope, setScope] = useState<"subtree" | "direct">("subtree");
  const url = nodeUrl(id, scope, filters, showHidden);
  const { data: fresh, error: err } = useResource<NodeData>(url);
  // switching scope keeps the list on screen until the other one arrives
  const [last, setLast] = useState<NodeData | undefined>(fresh);
  if (fresh && fresh !== last) setLast(fresh);
  const [stub] = useState(() => fromTree(id));
  const data = fresh ?? last ?? stub;
  const loading = !fresh && !last;
  const [extra, setExtra] = useState<{ url: string; qs: NodeData["questions"]; next: string | null | undefined }>({ url, qs: [], next: undefined });
  const [paging, setPaging] = useState<{ url: string; state: "loading" | "error" } | null>(null);
  const [allKids, setAllKids] = useState(false);

  // "Show more": the next page by cursor (a few ms even on the whole tree), one request at a time
  const mine = extra.url === url;
  const next = mine && extra.next !== undefined ? extra.next : data?.next ?? null;
  const loadMore = async () => {
    if (!data || !next || (paging?.url === url && paging.state === "loading")) return;
    setPaging({ url, state: "loading" });
    try {
      const r = await fetch(`${url}&page=1&after=${encodeURIComponent(next)}`);
      if (!r.ok) throw new Error(String(r.status));
      const d = (await r.json()) as { questions: NodeData["questions"]; next: string | null };
      setExtra((e) => ({ url, qs: [...(e.url === url ? e.qs : []), ...d.questions], next: d.next }));
      setPaging(null);
    } catch {
      setPaging({ url, state: "error" });
    }
  };

  if (err) return <div className="panel-body"><p className="err">{err}</p></div>;
  if (!data) return <div className="panel-body"><div className="working"><span className="spinner" />Loading topic</div></div>;
  const { node } = data;
  const sub = data.stats.find((s) => s.scope === "subtree");
  const kinds = Object.entries(sub?.kind_counts ?? {}).sort((a, b) => b[1] - a[1]);
  const kindTotal = kinds.reduce((s, [, v]) => s + v, 0);
  const qs = [...data.questions, ...(extra.url === url ? extra.qs : [])];

  return (
    <>
      <Crumbs items={data.ancestors.slice(0, -1)} onClose={onClose} />
      <div className="panel-body" data-testid="node-view">
        <section>
          <div className="tags">
            <span className={`tag hemi-${node.hemisphere}`}>{node.hemisphere === "root" ? "Whole tree" : node.hemisphere}</span>
            <span className="tag num">{(data.shown ?? sub?.n_questions ?? 0).toLocaleString()} question{(data.shown ?? sub?.n_questions) === 1 ? "" : "s"}</span>
          </div>
          <h2 className="title">{node.label}</h2>
          <p className="desc">{node.description}</p>
          {node.not_for && <p className="note">Not here: {node.not_for}</p>}
          {node.examples?.length > 0 && <p className="note">For example: {node.examples.map((e) => `“${e}”`).join("  ")}</p>}
        </section>

        <section>
          <ol className="trail">
            {data.ancestors.slice(0, -1).map((a, i) => (
              <li key={a.id} style={{ ["--d" as string]: i }}>
                <button onClick={() => selectNode(a.id)} onPointerEnter={() => prefetch(nodeUrl(a.id))}>{i === 0 ? "All questions" : a.label}</button>
              </li>
            ))}
            <li className="here" style={{ ["--d" as string]: data.ancestors.length - 1 }} aria-current="true">
              <span>{node.label}</span>
            </li>
            {(allKids ? data.children : data.children.slice(0, KIDS_SHOWN)).map((c) => (
              <li key={c.id} className="kid" style={{ ["--d" as string]: data.ancestors.length }}>
                <button onClick={() => selectNode(c.id)} onPointerEnter={() => prefetch(nodeUrl(c.id))}>
                  {c.label}<small className="num">{c.n_questions.toLocaleString()}</small>
                </button>
              </li>
            ))}
          </ol>
          {data.children.length > KIDS_SHOWN && (
            <button className="more" onClick={() => setAllKids(!allKids)}>
              {allKids ? "Fewer subtopics" : `All ${data.children.length} subtopics`}
            </button>
          )}
        </section>

        <section>
          <h4>
            <span className="h4t">
              Indicators
              <Info label="Indicators">
                Each one rolled up over every question in this branch. Bars fill toward where Jev is jagged.
                <span><b>Stability:</b> share of reruns with the options reordered that kept the same top answer.</span>
                <span><b>Frame gap:</b> how far Jev&apos;s own answers are from its &ldquo;most people&rdquo; answers.</span>
                <span><b>Human gap:</b> how far its &ldquo;most people&rdquo; answers are from real surveys and polls.</span>
                <span><b>Placement confidence:</b> how sure the tree placement was, where Jev placed questions.</span>
                <span><b>Calibration error:</b> how far Jev&apos;s confidence is from how often it&apos;s right, where answers are known.</span>
                <span><b>Fragile questions:</b> share whose top answer flips when the options are reordered.</span>
              </Info>
            </span>
            <small>rolled up over this branch</small>
          </h4>
          <div className="indgrid">
            {IND.map(({ k, label, fmt }) => {
              const v = sub ? (sub[k as keyof typeof sub] as number | null) : null;
              const a = k === "fragile_share" ? v : attention({ ...(sub as object), [k]: v } as never, k as Indicator);
              return (
                <div className="ind" key={k}>
                  <div className="k">{label}</div>
                  {v === null || v === undefined ? (
                    <div className="v none">No data yet</div>
                  ) : (
                    <>
                      <div className="v num">{fmt(v)}</div>
                      <div className="meter"><i style={{ width: `${Math.max(4, (a ?? 0) * 100)}%`, background: `#${rampColor(a ?? 0).getHexString()}` }} /></div>
                    </>
                  )}
                </div>
              );
            })}
          </div>
          <p className="hint">Bars fill toward where Jev is jagged. They are indicators, not grades.</p>
        </section>

        {kinds.length > 0 && (
          <section>
            <h4>Kinds of judgment</h4>
            <div className="mix">
              {kinds.map(([k, v], i) => <i key={k} style={{ flex: v, background: KIND_COLORS[i % KIND_COLORS.length] }} title={`${k}: ${v}`} />)}
            </div>
            <div className="mixlegend">
              {kinds.map(([k, v], i) => (
                <span key={k}><span style={{ color: KIND_COLORS[i % KIND_COLORS.length] }}>●</span> {k} <span className="num">{Math.round((v / kindTotal) * 100)}%</span></span>
              ))}
            </div>
          </section>
        )}

        <section>
          <h4>
            Questions <small className="num">{data.total}</small>
            <span className="seg">
              <button aria-pressed={scope === "subtree"} onClick={() => setScope("subtree")}>With subtopics</button>
              <button aria-pressed={scope === "direct"} onClick={() => setScope("direct")}>Here only</button>
            </span>
          </h4>
          {loading && <div className="working"><span className="spinner" />Loading questions</div>}
          {!loading && qs.length === 0 && <p className="note">No questions here yet{filters.kind || filters.primitive || filters.origin ? " for these filters" : ""}. Use the ask box to add one.</p>}
          <div className="qlist">
            {qs.map((qq) => (
              <button key={qq.id} className="qitem" data-testid="question-item" onClick={() => openQuestion(qq.id)} onPointerEnter={() => prefetch(questionUrl(qq.id))}>
                <span className="qt">{qq.text}</span>
                <span className="qm">
                  <span>{qq.primitive}</span>
                  {(qq.kind || qq.shape) && <span>{qq.kind || qq.shape}</span>}
                  {qq.top && <span className="num">top: {qq.top.replace(/_/g, " ")} {qq.p_top !== null ? `${Math.round((qq.p_top ?? 0) * 100)}%` : ""}</span>}
                  {qq.stability !== null && qq.stability < 0.67 && <span className="fragile">fragile</span>}
                  {qq.ask_count > 1 && <span className="num">asked {qq.ask_count} times</span>}
                  {!qq.display_ok && <span className="fragile">hidden</span>}
                </span>
              </button>
            ))}
          </div>
          {next && (
            <button className="more" onClick={loadMore} disabled={paging?.url === url && paging.state === "loading"}>
              {paging?.url === url && paging.state === "loading"
                ? "Loading questions…"
                : paging?.url === url && paging.state === "error"
                  ? "Couldn't load more. Try again"
                  : `Show more questions (${qs.length.toLocaleString()} of ${data.total.toLocaleString()})`}
            </button>
          )}
        </section>
      </div>
    </>
  );
}
