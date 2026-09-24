"use client";
import { useEffect, useMemo, useState } from "react";
import { useStore } from "@/lib/store";
import { openQuestion, selectNode, travel } from "@/lib/actions";
import { HEMI_COLOR } from "@/lib/layout";
import type { Hemisphere } from "@/lib/types";
import { Crumbs, pct } from "./Panel";

type Dist = Record<string, number>;
interface Probe { id: string; frame: string; variant_kind: string; variant_params: Record<string, unknown> | null; request_hash: string; model_served: string | null; distribution: Dist; confidence: number | null }
interface QData {
  question: { id: string; node_id: string; hemisphere: Hemisphere; kind: string | null; shape: string | null; primitive: "noul" | "choice" | "score"; text: string; options: unknown; state: unknown; origin: string; source: string | null; license: string | null; truth: unknown; flags: string[]; display_ok: boolean; ask_count: number };
  meta: Record<string, number | string | boolean | null> | null;
  probes: Probe[];
  human: { population: string; n: number | null; distribution: Dist; source: string | null; wave: string | null }[];
  links: { from_id: string; to_id: string; type: string; condition: Record<string, unknown> | null; other_text: string; direction: "in" | "out" }[];
  placements: { node_id: string; method: string; confidence: number | null; separation: number | null }[];
  ancestors: { id: string; label: string }[];
  calls: { request_hash: string; model_served: string | null; latency_ms: number | null }[];
}

const human = (k: string) => k.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase());

/** Ordered [key, label] pairs for a question's answer options. */
function optionList(primitive: string, options: unknown, dist?: Dist): [string, string][] {
  if (primitive === "noul") return [["true", "Yes"], ["false", "No"]];
  if (primitive === "score" && Array.isArray(options))
    return options.map((o, i) => [String(i), typeof o === "string" ? o : (o as { what?: string })?.what ?? JSON.stringify(o)]);
  if (options && typeof options === "object" && !Array.isArray(options))
    return Object.entries(options as Record<string, unknown>).map(([k, v]) => [k, typeof v === "string" ? v : (v as { what?: string } | null)?.what ?? human(k)]);
  return Object.keys(dist ?? {}).map((k) => [k, human(k)]);
}

const argmax = (d?: Dist) => (d ? Object.entries(d).sort((a, b) => b[1] - a[1])[0]?.[0] : undefined);

function truthKey(t: unknown): string | undefined {
  if (t === null || t === undefined) return undefined;
  if (typeof t === "boolean" || typeof t === "number" || typeof t === "string") return String(t);
  if (typeof t === "object") {
    const o = t as Record<string, unknown>;
    const v = o.answer ?? o.option ?? o.key ?? o.value;
    return v === undefined ? undefined : String(v);
  }
}

export function QuestionCard({ id, note, onClose }: { id: string; note?: string; onClose: () => void }) {
  const [d, setD] = useState<QData | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [frame, setFrame] = useState<string>("self");
  const [pop, setPop] = useState<string>("");
  const selected = useStore((s) => s.selected);

  useEffect(() => {
    let live = true;
    fetch(`/api/question/${encodeURIComponent(id)}`)
      .then((r) => r.json())
      .then((x) => {
        if (!live) return;
        if (x.error) return setErr(x.error);
        setD(x);
        const frames = new Set((x as QData).probes.filter((p) => p.variant_kind === "base").map((p) => p.frame));
        setFrame(frames.has("self") ? "self" : [...frames][0] ?? "self");
        setPop((x as QData).human[0]?.population ?? "");
      });
    return () => { live = false; };
  }, [id]);

  // Light the path to this question's node when the card opens from somewhere else.
  useEffect(() => {
    if (!d) return;
    const path = d.ancestors.map((a) => a.id);
    if (selected !== d.question.node_id) travel(path);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [d]);

  const view = useMemo(() => {
    if (!d) return null;
    const base = d.probes.filter((p) => p.variant_kind === "base");
    const order = (f: string) => (f === "self" ? 0 : f === "human" ? 1 : 2);
    const frames = [...new Set(base.map((p) => p.frame))].sort((a, b) => order(a) - order(b) || a.localeCompare(b));
    const main = base.find((p) => p.frame === frame) ?? base[0];
    const variants = d.probes.filter((p) => p.variant_kind !== "base" && p.frame === (main?.frame ?? "self"));
    const opts = optionList(d.question.primitive, d.question.options, main?.distribution);
    return { frames, main, variants, opts };
  }, [d, frame]);

  if (err) return <div className="panel-body"><p className="err">{err}</p></div>;
  if (!d || !view) return <div className="panel-body"><div className="working"><span className="spinner" />Loading question</div></div>;

  const { question: q, meta } = d;
  const isSelf = q.hemisphere === "self";
  const color = HEMI_COLOR[q.hemisphere];
  const dist = view.main?.distribution;
  const top = argmax(dist);
  const hd = d.human.find((h) => h.population === pop)?.distribution;
  const truth = truthKey(q.truth);
  const stability = meta?.stability as number | null | undefined;
  const fragile = typeof stability === "number" && stability < 0.67;
  const frameName = (f: string) => (f === "self" ? (isSelf ? "Jev's default" : "Jev") : f === "human" ? "Most people" : f.startsWith("human@") ? `People in ${f.slice(6)}` : human(f));
  const served = [...new Set([...d.calls.map((c) => c.model_served), meta?.model_served as string | null].filter(Boolean))];

  return (
    <>
      <Crumbs items={d.ancestors} onClose={onClose} />
      <div className="panel-body" data-testid="question-card">
        {note && <div className="notice">{note}</div>}
        <section>
          <div className="tags">
            <span className={`tag hemi-${q.hemisphere}`}>{q.hemisphere}</span>
            <span className="tag">{q.primitive === "noul" ? "Noul (yes / no)" : q.primitive === "choice" ? "Choice" : "Score"}</span>
            {(q.kind || q.shape) && <span className="tag">{q.kind || q.shape}</span>}
            {fragile && <span className="badge-fragile">Fragile</span>}
            {!q.display_ok && <span className="tag warn">Hidden from the map</span>}
            {q.flags.map((f) => <span key={f} className="tag warn">{f}</span>)}
          </div>
          <p className="qtext">{q.text}</p>
          {q.state != null && (
            <pre className="note" style={{ whiteSpace: "pre-wrap", fontSize: 12, background: "var(--win)", padding: 10, marginTop: 10, color: "var(--ink)", boxShadow: "inset 0 0 0 1px var(--ink)" }}>
              {typeof q.state === "string" ? q.state : JSON.stringify(q.state, null, 2)}
            </pre>
          )}
        </section>

        <section>
          <div className="framebar">
            <h4 style={{ margin: 0 }}>{view.main?.frame === "human" ? "What Jev thinks most people would say" : isSelf ? "Jev's default" : "Jev's answer"}</h4>
            {view.frames.length > 1 && (
              <span className="seg" role="group" aria-label="Frame">
                {view.frames.map((f) => (
                  <button key={f} aria-pressed={frame === f} onClick={() => setFrame(f)}>{frameName(f)}</button>
                ))}
              </span>
            )}
          </div>
          {!dist && <p className="note">Jev hasn&apos;t answered this question yet. It is queued for the next pipeline run.</p>}
          {dist && q.primitive !== "score" && (
            <div className="bars">
              {view.opts.map(([k, label]) => {
                const p = dist[k] ?? 0;
                return (
                  <div key={k} className={`bar ${k === top ? "top" : ""}`}>
                    <span className="lab">{label}{truth === k && <span className="truth">correct answer</span>}</span>
                    <span className="pct num">{pct(p)}</span>
                    <span className="track">
                      <span className="fill" style={{ width: `${p * 100}%`, background: color, opacity: k === top ? 1 : 0.55 }} />
                      {hd && hd[k] !== undefined && <span className="human" style={{ left: `calc(${hd[k] * 100}% - 1px)` }} title={`${pop}: ${pct(hd[k])}`} />}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
          {dist && q.primitive === "score" && (
            <div className="bands">
              {view.opts.map(([k, label], i) => {
                const p = dist[k] ?? 0;
                return (
                  <div key={k} className={`band ${k === top ? "modal" : ""}`}>
                    <span className="bg" style={{ width: `${p * 100}%`, background: color }} />
                    <span className="lvl num">{i + 1}</span>
                    <span className="d">{label}{truth === k && <span className="truth" style={{ color: "var(--gold)", fontSize: 11, marginLeft: 8 }}>correct</span>}</span>
                    <span className="pct num">{pct(p)}</span>
                    {hd && hd[k] !== undefined && <span className="human" style={{ width: `${hd[k] * 100}%` }} />}
                  </div>
                );
              })}
              <p className="hint">Score answers are shown as bands: the most likely level is outlined. No averaged number is shown.</p>
            </div>
          )}
          {d.human.length > 0 && (
            <div className="legendline">
              <span><i />Real people</span>
              <select className="pop" value={pop} onChange={(e) => setPop(e.target.value)} aria-label="Human population">
                {d.human.map((h) => <option key={h.population} value={h.population}>{h.population}{h.n ? ` (n=${h.n})` : ""}</option>)}
                <option value="">Hide</option>
              </select>
            </div>
          )}
          {view.main?.confidence != null && <p className="hint num">Jev&apos;s reported confidence: {pct(view.main.confidence)}</p>}
        </section>

        <section>
          <h4>
            Stability under reshuffling
            {typeof stability === "number" && <small className="num">{pct(stability)} agree</small>}
          </h4>
          {view.variants.length === 0 ? (
            <p className="note">Not measured yet for this frame.</p>
          ) : (
            <div className="stab">
              {view.variants.map((v, i) => {
                const t = argmax(v.distribution);
                const same = t === argmax(view.main?.distribution);
                const lab = view.opts.find(([k]) => k === t)?.[1] ?? t;
                return (
                  <div key={v.id} className={`cell ${same ? "agree" : "flip"}`} title={v.variant_params ? JSON.stringify(v.variant_params) : undefined}>
                    <div className="k">{v.variant_kind === "shuffle" ? `Shuffle ${i + 1}` : human(v.variant_kind)}</div>
                    <div>{same ? "Same top answer" : `Flipped to ${lab}`}</div>
                  </div>
                );
              })}
            </div>
          )}
          {fragile && <p className="err">The top answer changes when the options are reordered. Treat it as fragile.</p>}
        </section>

        {meta && (
          <section>
            <h4>Jev on the question itself <small>its own read, before answering</small></h4>
            <div className="meters">
              {([["objective", "Has one right answer"], ["ambiguous", "Ambiguous"], ["disagreement", "People disagree"], ["reveals_self", "Reveals the answerer"]] as const).map(([k, label]) =>
                meta[k] === null || meta[k] === undefined ? null : (
                  <div className="meterrow" key={k}>
                    <span>{label}</span>
                    <span className="t"><i style={{ width: `${(meta[k] as number) * 100}%` }} /></span>
                    <span className="v num">{pct(meta[k] as number)}</span>
                  </div>
                ),
              )}
            </div>
            <dl className="facts" style={{ marginTop: 14 }}>
              {meta.frame_gap != null && <><dt>Frame gap</dt><dd className="num">{(meta.frame_gap as number).toFixed(2)} (self vs most people)</dd></>}
              {meta.human_gap != null && <><dt>Human gap</dt><dd className="num">{(meta.human_gap as number).toFixed(2)} (vs real people)</dd></>}
              {meta.correct != null && <><dt>Matches truth</dt><dd>{meta.correct ? "Yes" : "No"}{meta.brier != null && <span className="num"> (Brier {(meta.brier as number).toFixed(3)})</span>}</dd></>}
            </dl>
          </section>
        )}

        <section>
          <h4>Thread <small className="num">asked {q.ask_count}×</small></h4>
          {d.links.length === 0 ? (
            <p className="note">No follow-ups or duplicates linked yet.</p>
          ) : (
            <div className="thread">
              {d.links.map((l) => (
                <button key={`${l.from_id}-${l.to_id}-${l.type}`} onClick={() => openQuestion(l.direction === "out" ? l.to_id : l.from_id)}>
                  <div className="cond">
                    {l.type === "follow_up" ? (l.direction === "out" ? "Follow-up" : "Follows from") : human(l.type)}
                    {l.condition ? ` if ${Object.entries(l.condition).map(([k, v]) => `${k} is ${v}`).join(", ")}` : ""}
                  </div>
                  <div className="t">{l.other_text}</div>
                </button>
              ))}
            </div>
          )}
        </section>

        <section>
          <h4>Where this comes from</h4>
          <dl className="facts">
            <dt>Topic</dt>
            <dd><button className="chip" onClick={() => selectNode(q.node_id)}>{d.ancestors[d.ancestors.length - 1]?.label ?? q.node_id}</button></dd>
            <dt>Origin</dt><dd>{q.origin}{q.source ? `, ${q.source}` : ""}{q.license ? ` (${q.license})` : ""}</dd>
            {d.placements.length > 0 && (
              <>
                <dt>Placed by</dt>
                <dd className="num">
                  {d.placements[d.placements.length - 1].method}
                  {d.placements[d.placements.length - 1].confidence != null && `, ${pct(d.placements[d.placements.length - 1].confidence)} sure`}
                  {d.placements[d.placements.length - 1].separation != null && `, separation ${d.placements[d.placements.length - 1].separation!.toFixed(2)}×`}
                </dd>
              </>
            )}
            <dt>Served model</dt><dd>{served.join(", ") || "n/a"}</dd>
            <dt>Raw calls</dt>
            <dd>
              {d.calls.length === 0 && "none yet"}
              {d.calls.map((c, i) => (
                <span key={c.request_hash}>
                  {i > 0 && ", "}
                  <a href={`/api/call/${c.request_hash}`} target="_blank" rel="noreferrer" className="num" data-testid="raw-call">
                    {c.request_hash.slice(0, 10)}
                  </a>
                </span>
              ))}
            </dd>
          </dl>
        </section>
      </div>
    </>
  );
}
