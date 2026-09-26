"use client";
import { useState } from "react";
import { useStore } from "@/lib/store";
import { useResource, prefetch } from "@/lib/cache";
import { nodeUrl, questionUrl } from "@/lib/panelData";
import { openQuestion, selectNode } from "@/lib/actions";
import { attention, rampColor } from "@/lib/color";
import type { Indicator } from "@/lib/types";
import { Crumbs } from "./Panel";

interface NodeData {
  node: { id: string; label: string; description: string; not_for: string | null; examples: string[]; hemisphere: string; depth: number; source: string; locked: boolean };
  stats: { scope: string; n_questions: number; n_asked: number; kind_counts: Record<string, number> | null; stability: number | null; frame_gap: number | null; human_gap: number | null; calibration_ece: number | null; placement_conf: number | null; fragile_share: number | null }[];
  ancestors: { id: string; label: string }[];
  children: { id: string; label: string; n_questions: number }[];
  questions: { id: string; text: string; primitive: string; kind: string | null; shape: string | null; ask_count: number; display_ok: boolean; top: string | null; p_top: number | null; stability: number | null; node_id: string }[];
  total: number;
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

export function NodeView({ id, onClose }: { id: string; onClose: () => void }) {
  const filters = useStore((s) => s.filters);
  const showHidden = useStore((s) => s.showHidden);
  const [scope, setScope] = useState<"subtree" | "direct">("subtree");
  const url = nodeUrl(id, scope, filters, showHidden);
  const { data: fresh, error: err } = useResource<NodeData>(url);
  // switching scope keeps the list on screen until the other one arrives
  const [last, setLast] = useState<NodeData | undefined>(fresh);
  if (fresh && fresh !== last) setLast(fresh);
  const data = fresh ?? last;
  const [extra, setExtra] = useState<{ url: string; qs: NodeData["questions"] }>({ url, qs: [] });
  const [allKids, setAllKids] = useState(false);

  const loadMore = async () => {
    if (!data) return;
    const more = extra.url === url ? extra.qs : [];
    const off = data.questions.length + more.length;
    const d = await fetch(`${url}&offset=${off}`).then((r) => r.json());
    setExtra({ url, qs: [...more, ...d.questions] });
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
            <span className="tag num">{(sub?.n_questions ?? 0).toLocaleString()} question{sub?.n_questions === 1 ? "" : "s"}</span>
            {(sub?.n_asked ?? 0) > 0 && <span className="tag gold num">{sub?.n_asked} asked here</span>}
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
          <h4>Indicators <small>rolled up over this branch</small></h4>
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
          {qs.length === 0 && <p className="note">No questions here yet{filters.kind || filters.primitive || filters.origin ? " for these filters" : ""}. Use the ask box to add one.</p>}
          <div className="qlist">
            {qs.map((qq) => (
              <button key={qq.id} className="qitem" data-testid="question-item" onClick={() => openQuestion(qq.id)} onPointerEnter={() => prefetch(questionUrl(qq.id))}>
                <span className="qt">{qq.text}</span>
                <span className="qm">
                  <span>{qq.primitive}</span>
                  {(qq.kind || qq.shape) && <span>{qq.kind || qq.shape}</span>}
                  {qq.top && <span className="num">top: {qq.top.replace(/_/g, " ")} {qq.p_top !== null ? `${Math.round((qq.p_top ?? 0) * 100)}%` : ""}</span>}
                  {qq.stability !== null && qq.stability < 0.67 && <span className="fragile">fragile</span>}
                  {qq.ask_count > 1 && <span className="num">asked {qq.ask_count}×</span>}
                  {!qq.display_ok && <span className="fragile">hidden</span>}
                </span>
              </button>
            ))}
          </div>
          {qs.length < data.total && <button className="more" onClick={loadMore}>Show more questions</button>}
        </section>
      </div>
    </>
  );
}
