import type { ReactNode } from "react";
import { DotRows, type DotRow } from "../portrait/charts";
import type { Chart as ChartData } from "./types";

// The experiments' chart library (docs/16 pass 3, step 5). Every experiment's result file carries a chart spec
// {type, ...data}; this turns each type into a plain HTML/SVG chart in the portrait's print language (Jev magenta,
// people ink). `mini` draws the same chart as a small thumbnail for the index cards: fewer rows, no labels.

type Obj = Record<string, unknown>;
const num = (x: unknown): number | null => (typeof x === "number" && Number.isFinite(x) ? x : null);
const arr = <T = Obj>(x: unknown): T[] => (Array.isArray(x) ? (x as T[]) : []);
const str = (x: unknown) => (x === null || x === undefined ? "" : String(x));
const pair = (x: unknown): [number, number] | undefined =>
  Array.isArray(x) && num(x[0]) !== null && num(x[1]) !== null ? [x[0] as number, x[1] as number] : undefined;
const pretty = (s: string) => s.replaceAll("_", " ");
const fmtPct = (v: number) => (v >= 0 && v <= 1 ? `${Math.round(v * 100)}%` : Number.isInteger(v) ? String(v) : v.toFixed(2));

function fmtFor(domain: [number, number]) {
  const span = Math.abs(domain[1] - domain[0]);
  if (domain[0] >= 0 && domain[1] <= 1 && span <= 1) return (v: number) => `${Math.round(v * 100)}%`;
  if (span >= 20) return (v: number) => String(Math.round(v));
  if (span >= 2) return (v: number) => v.toFixed(1).replace(/\.0$/, "");
  return (v: number) => v.toFixed(2);
}

function niceTicks(d: [number, number], n = 5): number[] {
  const [a, b] = d[0] <= d[1] ? d : [d[1], d[0]];
  const raw = (b - a) / (n - 1 || 1);
  const mag = 10 ** Math.floor(Math.log10(raw || 1));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= raw) ?? raw;
  const out: number[] = [];
  for (let v = Math.ceil(a / step) * step; v <= b + 1e-9; v += step) out.push(Number(v.toFixed(6)));
  return out.length >= 2 ? out : [a, b];
}

function extent(values: number[], zero: boolean, pad = 0.06): [number, number] {
  const v = values.filter((x) => Number.isFinite(x));
  if (!v.length) return [0, 1];
  let lo = Math.min(...v, ...(zero ? [0] : [])), hi = Math.max(...v, ...(zero ? [0] : []));
  if (lo >= 0 && hi <= 1 && hi - lo > 0.25) return [0, 1];
  if (hi === lo) { lo -= 1; hi += 1; }
  const p = (hi - lo) * pad;
  // round the ends outward to a readable step, so axes read 0 to 1 or -0.5 to 1, not -0.41 to 0.75
  const raw = (hi - lo + 2 * p) / 4;
  const mag = 10 ** Math.floor(Math.log10(raw || 1));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((x) => x >= raw) ?? raw;
  return [Math.floor((lo - p) / step) * step, Math.ceil((hi + p) / step) * step];
}

// ---- rows of dots: dots, effects, forest, strip, range, dumbbell, slope ------------------------------------------------
function rowsChart(c: ChartData, mini: boolean) {
  const t = c.type;
  const rows = arr(c.rows);
  const dr: DotRow[] = [];
  const vals: number[] = [];
  const push = (...xs: (number | null | undefined)[]) => xs.forEach((x) => { if (typeof x === "number" && Number.isFinite(x)) vals.push(x); });
  for (const [i, r] of rows.entries()) {
    const marks: DotRow["marks"] = [];
    let ci: [number, number] | undefined, ciP: [number, number] | undefined, value: ReactNode = null, sub: ReactNode = null, link = false;
    if (t === "forest") {
      const p = num(r.people), j = num(r.jev);
      if (p !== null) marks.push({ v: p, kind: "hum", title: `people ${p.toFixed(2)}` });
      if (j !== null) marks.push({ v: j, kind: "jev", title: `Jev ${j.toFixed(2)}` });
      push(p, j); link = true;
      value = j !== null && p !== null ? <><b>{j.toFixed(2)}</b> · {p.toFixed(2)}</> : null;
    } else if (t === "dumbbell" || t === "slope") {
      const a = num(r.a), b = num(r.b);
      if (a !== null) marks.push({ v: a, kind: "hum", title: `${str(c.a_label)} ${a}` });
      if (b !== null) marks.push({ v: b, kind: "jev", title: `${str(c.b_label)} ${b}` });
      push(a, b); link = true;
      value = t === "slope" && a !== null && b !== null ? <><b>{c.rank ? b : fmtPct(b)}</b> · {c.rank ? a : fmtPct(a)}</> : null;
    } else {
      const v = num(r.value), p = num(r.people), g = num(r.guess);
      if (p !== null) marks.push({ v: p, kind: "hum", title: `people ${p}` });
      if (g !== null) marks.push({ v: g, kind: "guess", title: `what Jev thinks most people would say: ${g}` });
      if (v !== null) marks.push({ v, kind: "jev", title: `Jev ${v}` });
      const others = r.others as Obj | undefined;
      if (others) for (const [k, x] of Object.entries(others)) if (num(x) !== null) { marks.push({ v: x as number, kind: "tick", title: `${k} ${x}` }); push(x as number); }
      ci = pair(r.ci); ciP = pair(r.people_ci);
      if (t === "range") {
        const lo = r.lo as Obj | undefined, hi = r.hi as Obj | undefined;
        if (lo && num(lo.value) !== null) { marks.push({ v: lo.value as number, kind: "tick", title: str(lo.name) }); push(lo.value as number); }
        if (hi && num(hi.value) !== null) { marks.push({ v: hi.value as number, kind: "tick", title: str(hi.name) }); push(hi.value as number); }
        sub = lo && hi ? `${str(lo.name)} → ${str(hi.name)}` : null;
      }
      push(v, p, g, ...(ci ?? []), ...(ciP ?? []));
      value = r.right !== undefined ? str(r.right) : r.note !== undefined ? str(r.note) : null;
      link = p !== null && v !== null;
    }
    dr.push({ key: `${i}`, label: pretty(str(r.label)), sub: mini ? null : sub, marks, ci, ciP, value: mini ? null : value, hi: r.hi === true, link });
  }
  const zero = c.zero !== undefined;
  let domain = pair(c.domain) ?? extent(vals, zero);
  const ranks = t === "slope" && Boolean(c.rank);
  if (ranks && vals.length) domain = [Math.max(...vals) + 0.5, Math.min(...vals) - 0.5]; // ranks: 1 on the right
  const shown = mini ? dr.slice(0, 7) : dr;
  const fmt = ranks ? (v: number) => String(Math.round(v)) : fmtFor(domain);
  const ticks = ranks ? [] : niceTicks(domain, mini ? 3 : 5);
  return (
    <div className={mini ? "ex-mini-rows" : undefined}>
      <DotRows rows={shown} domain={domain} ticks={ticks} fmt={fmt} refs={[...(zero ? [{ v: num(c.zero) ?? 0, zero: true }] : []), ...(num(c.ref) !== null ? [{ v: c.ref as number }] : [])]} />
      {!mini && <Legend c={c} />}
    </div>
  );
}

function Legend({ c }: { c: ChartData }) {
  const t = c.type;
  const rows = arr(c.rows);
  const hasP = t === "forest" || t === "dumbbell" || t === "slope" || rows.some((r) => num(r.people) !== null || pair(r.people_ci));
  const hasG = rows.some((r) => num(r.guess) !== null);
  const hasT = rows.some((r) => r.others || r.lo);
  const a = t === "dumbbell" || t === "slope" ? str(c.a_label) || "people" : "people";
  const b = t === "dumbbell" || t === "slope" ? str(c.b_label) || "Jev" : "Jev";
  return (
    <p className="ex-legend">
      <span><i className="k jev" />{b}</span>
      {hasP && <span><i className="k hum" />{a}</span>}
      {hasG && <span><i className="k guess" />what Jev thinks most people would say</span>}
      {hasT && <span><i className="k tick" />{rows.some((r) => r.lo) ? "weakest and strongest task" : "other settings"}</span>}
      {c.x ? <span className="ax">{str(c.x)}</span> : null}
    </p>
  );
}

// ---- bars: ranked, bars, bars2, mix --------------------------------------------------------------------------------------
function Bars({ rows, max, fmt, mini, labels, mark }: {
  rows: { label: string; a?: number | null; b: number; ci?: [number, number] }[]; max: number; fmt: (v: number) => string;
  mini: boolean; labels?: [string, string]; mark?: number | null;
}) {
  const w = (v: number) => `${Math.max(0, Math.min(1, v / (max || 1))) * 100}%`;
  const paired = rows.some((r) => r.a !== undefined && r.a !== null);
  return (
    <div className={`ex-bars${mini ? " mini" : ""}${paired ? " paired" : ""}`}>
      {rows.map((r, i) => (
        <div className="ex-bar" key={i}>
          <span className="l">{r.label}</span>
          <span className="t">
            {/* two bars stacked, not overlaid: Jev on top, the comparison under it */}
            <i className="j" style={{ width: w(r.b) }} />
            {r.a !== undefined && r.a !== null && <i className="p" style={{ width: w(r.a) }} />}
            {r.ci && <i className="ci" style={{ left: w(r.ci[0]), width: `calc(${w(r.ci[1])} - ${w(r.ci[0])})` }} />}
            {mark !== undefined && mark !== null && <i className="ref" style={{ left: w(mark) }} />}
          </span>
          {!mini && <span className="v"><b>{fmt(r.b)}</b>{r.a !== undefined && r.a !== null ? <> · <span className="pv">{fmt(r.a)}</span></> : ""}</span>}
        </div>
      ))}
      {!mini && labels && (
        <p className="ex-legend">
          <span><i className="k jev" />{labels[1]}</span><span><i className="k bar" />{labels[0]}</span>
          {mark !== undefined && mark !== null && <span><i className="k tick" />{fmt(mark)}</span>}
        </p>
      )}
    </div>
  );
}

function barsChart(c: ChartData, mini: boolean) {
  const t = c.type;
  if (t === "ranked") {
    const items = arr(c.items);
    const vals = items.map((x) => num(x.value) ?? 0);
    const max = num(c.max) ?? Math.max(...vals, 0);
    const fmt = max <= 1 ? (v: number) => `${Math.round(v * 100)}%` : (v: number) => (Number.isInteger(v) ? String(v) : v.toFixed(1));
    const rows = items.slice(0, mini ? 5 : 10).map((x, i) => ({ label: `${i + 1}. ${str(x.label)}`, b: num(x.value) ?? 0 }));
    return (
      <>
        <Bars rows={rows} max={max} fmt={fmt} mini={mini} />
        {!mini && arr(c.bottom).length > 0 && (
          <p className="ex-foot">At the bottom: {arr(c.bottom).map((x) => str(x.label)).join(" · ")}</p>
        )}
        {!mini && c.unit ? <p className="ex-foot">{str(c.unit)}</p> : null}
      </>
    );
  }
  if (t === "bars2" || t === "mix") {
    let labels: string[], a: number[], b: number[], la: string, lb: string;
    if (t === "mix") {
      const jm = new Map(arr(c.jev).map((x) => [str(x.jev), num(x.proportion) ?? 0]));
      const cm = new Map(arr(c.crowd).map((x) => [str(x.crowd), num(x.proportion) ?? 0]));
      labels = [...new Set([...cm.keys(), ...jm.keys()])];
      a = labels.map((k) => cm.get(k) ?? 0); b = labels.map((k) => jm.get(k) ?? 0); la = "the crowd"; lb = "Jev";
    } else {
      labels = arr<string>(c.labels).map(str); a = arr<number>(c.a); b = arr<number>(c.b); la = str(c.a_label) || "people"; lb = str(c.b_label) || "Jev";
    }
    const max = Math.max(...a, ...b, 0);
    const fmt = max <= 1 ? (v: number) => `${Math.round(v * 100)}%` : (v: number) => v.toFixed(1);
    const rows = labels.map((l, i) => ({ label: pretty(l), a: a[i] ?? 0, b: b[i] ?? 0 })).slice(0, mini ? 6 : 40);
    return <Bars rows={rows} max={max} fmt={fmt} mini={mini} labels={[la, lb]} mark={num(c.ref)} />;
  }
  // bars
  const rows = arr(c.rows).length
    ? arr(c.rows).map((r) => ({ label: pretty(str(r.label)), b: num(r.value) ?? 0, ci: pair(r.ci) }))
    : arr<string>(c.labels).map((l, i) => ({ label: pretty(str(l)), b: num(arr(c.values)[i]) ?? 0, ci: undefined as [number, number] | undefined }));
  const dom = pair(c.domain);
  const max = dom ? dom[1] : Math.max(...rows.map((r) => r.ci?.[1] ?? r.b), 0);
  const fmt = max <= 1 ? (v: number) => `${Math.round(v * 100)}%` : (v: number) => v.toFixed(2).replace(/\.?0+$/, "");
  return (
    <>
      <Bars rows={rows.slice(0, mini ? 6 : 40)} max={max} fmt={fmt} mini={mini} />
      {!mini && (c.unit || c.note) ? <p className="ex-foot">{[str(c.unit), str(c.note)].filter(Boolean).join(" · ")}</p> : null}
    </>
  );
}

// ---- x-y charts: scatter, rankscatter, binned, calibration, reliability ------------------------------------------------
type Series = { name: string; kind: "jev" | "hum" | "alt"; pts: [number, number][]; line: boolean };

function XY({ series, labels = [], xd, yd, xl, yl, diagonal, mini, xcats, links = [] }: {
  series: Series[]; labels?: { label: string; x: number; y: number }[]; xd: [number, number]; yd: [number, number];
  xl?: string; yl?: string; diagonal?: boolean; mini: boolean; xcats?: string[]; links?: [[number, number], [number, number]][];
}) {
  // a narrow canvas: at phone width it shrinks little, so its labels stay readable; on desktop it's capped in CSS
  const W = mini ? 220 : 480, H = mini ? 130 : 330, m = mini ? { l: 6, r: 6, t: 6, b: 6 } : { l: 44, r: 14, t: 12, b: 40 };
  // rounded: server and browser can differ in a float's last bit (log10), which breaks hydration
  const r2 = (v: number) => Math.round(v * 100) / 100;
  const sx = (v: number) => r2(m.l + ((v - xd[0]) / (xd[1] - xd[0] || 1)) * (W - m.l - m.r));
  const sy = (v: number) => r2(H - m.b - ((v - yd[0]) / (yd[1] - yd[0] || 1)) * (H - m.t - m.b));
  const fx = fmtFor(xd), fy = fmtFor(yd);
  const dense = series.reduce((a, s) => a + s.pts.length, 0) > 400;
  return (
    <figure className={`ex-xy${mini ? " mini" : ""}`}>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${yl ?? ""} against ${xl ?? ""}`}>
        {!mini && niceTicks(yd).map((t) => (
          <g key={`y${t}`}><line className="grid" x1={m.l} x2={W - m.r} y1={sy(t)} y2={sy(t)} /><text className="tk" x={m.l - 6} y={sy(t) + 3} textAnchor="end">{fy(t)}</text></g>
        ))}
        {!mini && !xcats && niceTicks(xd).map((t) => (
          <g key={`x${t}`}><line className="grid" x1={sx(t)} x2={sx(t)} y1={m.t} y2={H - m.b} /><text className="tk" x={sx(t)} y={H - m.b + 14} textAnchor="middle">{fx(t)}</text></g>
        ))}
        {!mini && xcats && xcats.map((t, i) => <text key={t} className="tk" x={sx(i)} y={H - m.b + 14} textAnchor="middle">{t}</text>)}
        {diagonal && <line className="diag" x1={sx(Math.max(xd[0], yd[0]))} y1={sy(Math.max(xd[0], yd[0]))} x2={sx(Math.min(xd[1], yd[1]))} y2={sy(Math.min(xd[1], yd[1]))} />}
        {links.map(([a, b], i) => <line key={`l${i}`} className="link" x1={sx(a[0])} y1={sy(a[1])} x2={sx(b[0])} y2={sy(b[1])} />)}
        {series.map((s) => {
          const r = dense ? (mini ? 1 : 1.6) : mini ? 2.5 : 4;
          return (
            <g key={s.name} className={`s ${s.kind}`}>
              {s.line && <polyline points={s.pts.map(([x, y]) => `${sx(x)},${sy(y)}`).join(" ")} />}
              {s.pts.map(([x, y], i) => s.kind === "hum" && !dense
                ? <rect key={i} x={sx(x) - r * 0.8} y={sy(y) - r * 0.8} width={r * 1.6} height={r * 1.6} transform={`rotate(45 ${sx(x)} ${sy(y)})`} />
                : <circle key={i} cx={sx(x)} cy={sy(y)} r={r} />)}
            </g>
          );
        })}
        {!mini && labels.map((l, i) => (
          <text key={i} className="lab" x={sx(l.x) + 6} y={sy(l.y) - 5}>{l.label.length > 28 ? `${l.label.slice(0, 27)}…` : l.label}</text>
        ))}
        {!mini && xl && <text className="axl" x={(W + m.l) / 2} y={H - 6} textAnchor="middle">{xl}</text>}
        {!mini && yl && <text className="axl" x={12} y={(H - m.b + m.t) / 2} textAnchor="middle" transform={`rotate(-90 12 ${(H - m.b + m.t) / 2})`}>{yl}</text>}
      </svg>
      {!mini && series.length > 1 && (
        <figcaption className="ex-legend">{series.map((s) => <span key={s.name}><i className={`k ${s.kind}`} />{s.name}</span>)}</figcaption>
      )}
    </figure>
  );
}

function xyChart(c: ChartData, mini: boolean) {
  const t = c.type;
  if (t === "scatter" || t === "rankscatter") {
    let pts = arr<[number, number]>(c.points).filter((p) => Array.isArray(p) && num(p[0]) !== null && num(p[1]) !== null);
    if (t === "rankscatter") pts = pts.map(([j, a]) => [a, j]); // stored as (Jev rank, audience rank)
    if (mini && pts.length > 600) pts = pts.filter((_, i) => i % Math.ceil(pts.length / 600) === 0);
    const d = pair(c.domain);
    const xd: [number, number] = d ?? extent(pts.map((p) => p[0]), false, 0.03), yd: [number, number] = d ?? extent(pts.map((p) => p[1]), false, 0.03);
    const pp = arr<[number, number]>(c.points_people).filter((p) => Array.isArray(p) && num(p[0]) !== null && num(p[1]) !== null);
    const lg = Boolean(c.log);
    const tf = (p: [number, number]): [number, number] => (lg ? [Math.log10(Math.max(p[0], 1e-9)), Math.log10(Math.max(p[1], 1e-9))] : p);
    const P = pts.map(tf), Q = pp.map(tf);
    const both = [...P, ...Q];
    const xd2 = d && !lg ? xd : extent(both.map((p) => p[0]), false, 0.03), yd2 = d && !lg ? yd : extent(both.map((p) => p[1]), false, 0.03);
    const labels = arr(c.labels).map((l) => { const [x, y] = tf([num(l.x) ?? 0, num(l.y) ?? 0]); return { label: str(l.label), x, y }; });
    const series: Series[] = [{ name: "Jev", kind: "jev", pts: P, line: false }];
    if (Q.length) series.push({ name: "people", kind: "hum", pts: Q, line: false });
    return <XY series={series} labels={labels} xd={xd2} yd={yd2} xl={`${str(c.x)}${lg ? " (log10)" : ""}`} yl={`${str(c.y)}${lg ? " (log10)" : ""}`} diagonal={Boolean(c.diagonal) || t === "rankscatter"} mini={mini} />;
  }
  if (t === "binned") {
    const rows = arr(c.rows);
    const xcats = rows.map((r) => str(r.label));
    const series: Series[] = [{ name: str(c.y) || "Jev", kind: "jev", pts: rows.map((r, i) => [i, num(r.value) ?? 0] as [number, number]), line: true }];
    if (rows.some((r) => num(r.people) !== null)) series.push({ name: "people", kind: "hum", pts: rows.map((r, i) => [i, num(r.people) ?? 0] as [number, number]), line: true });
    if (rows.some((r) => num(r.agree) !== null)) series.push({ name: "agrees with the majority", kind: "alt", pts: rows.map((r, i) => [i, num(r.agree) ?? 0] as [number, number]), line: true });
    const ys = series.flatMap((s) => s.pts.map((p) => p[1]));
    const yd: [number, number] = ys.every((y) => y >= 0 && y <= 1) ? [0, 1] : extent(ys, false);
    return <XY series={series} xd={[-0.5, rows.length - 0.5]} yd={yd} xl={str(c.x)} yl={str(c.y)} mini={mini} xcats={xcats} />;
  }
  // calibration {series: {name: [{p, hit}]}} and reliability {lines: {name: [{conf, acc}]}}
  const src = (t === "calibration" ? c.series : c.lines) as Record<string, Obj[]> | undefined;
  const series: Series[] = Object.entries(src ?? {}).map(([name, pts], i) => ({
    name: name === "noul" ? "yes/no" : name === "choice" ? "pick from a list" : name, kind: i === 0 ? "jev" : name === "market" ? "hum" : "alt",
    pts: pts.map((p) => [num(p.p ?? p.conf) ?? 0, num(p.hit ?? p.acc) ?? 0] as [number, number]), line: true,
  }));
  const all = series.flatMap((s) => s.pts.flat());
  const lo = Math.min(0.5, ...all);
  const d: [number, number] = [lo < 0.4 ? 0 : 0.4, 1];
  return <XY series={series} xd={d} yd={d} xl={str(c.x)} yl={str(c.y)} diagonal mini={mini} />;
}

// ---- heat ---------------------------------------------------------------------------------------------------------------
function heat(c: ChartData, mini: boolean) {
  const cells = arr(c.cells);
  if (!cells.length) return null;
  const keys = Object.keys(cells[0]);
  const count = keys.find((k) => ["len", "n", "count"].includes(k)) ?? keys[2];
  const [yk, xk] = keys.includes("x") && keys.includes("y") ? ["y", "x"] : keys.filter((k) => k !== count);
  const order = (vals: unknown[]) => [...new Set(vals.map(str))].sort((a, b) => (Number.isNaN(Number(a)) || Number.isNaN(Number(b)) ? 0 : Number(a) - Number(b)));
  const xs = order(cells.map((r) => r[xk])), ys = order(cells.map((r) => r[yk]));
  const m = new Map(cells.map((r) => [`${str(r[yk])}|${str(r[xk])}`, num(r[count]) ?? 0]));
  const rowTot = new Map(ys.map((y) => [y, xs.reduce((a, x) => a + (m.get(`${y}|${x}`) ?? 0), 0)]));
  return (
    <div className={`ex-heat${mini ? " mini" : ""}`}>
      <table>
        {!mini && <caption>rows: {str(c.y)} · columns: {str(c.x)} · shade = share of the row</caption>}
        {!mini && <thead><tr><th />{xs.map((x) => <th key={x}>{pretty(x)}</th>)}</tr></thead>}
        <tbody>
          {ys.map((y) => (
            <tr key={y}>
              {!mini && <th>{pretty(y)}</th>}
              {xs.map((x) => {
                const v = m.get(`${y}|${x}`) ?? 0, s = v / (rowTot.get(y) || 1);
                return <td key={x} style={{ ["--s" as string]: s }} title={`${pretty(y)} → ${pretty(x)}: ${v}`}>{mini ? "" : v ? `${Math.round(s * 100)}%` : ""}</td>;
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---- ridge: one row per item, people's and Jev's distributions over ordered bins ------------------------------------------
function ridge(c: ChartData, mini: boolean) {
  const bins = arr<string | number>(c.bins).map(str);
  const rows = arr(c.rows).slice(0, mini ? 6 : 60);
  const W = 100, H = mini ? 10 : 14;
  const path = (v: number[]) => {
    const max = Math.max(...v, 1e-9);
    const pts = v.map((y, i) => `${Math.round((i / (v.length - 1 || 1)) * W * 100) / 100},${Math.round((H - (y / max) * (H - 1)) * 100) / 100}`);
    return `M0,${H} L${pts.join(" L")} L${W},${H} Z`;
  };
  return (
    <div className={`ex-ridge${mini ? " mini" : ""}`}>
      {rows.map((r, i) => (
        <div className="rr" key={i}>
          {!mini && <span className="l">{str(r.label)}</span>}
          <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" aria-hidden>
            <path className="hum" d={path(arr<number>(r.people))} />
            <path className="jev" d={path(arr<number>(r.jev))} />
          </svg>
        </div>
      ))}
      {!mini && (
        <div className="rr axis"><span className="l" /><div className="ticks">{bins.filter((_, i) => i % Math.ceil(bins.length / 6) === 0 || i === bins.length - 1).map((b) => <span key={b}>{b}</span>)}</div></div>
      )}
      {!mini && <p className="ex-legend"><span><i className="k jev" />Jev</span><span><i className="k hum" />people</span></p>}
    </div>
  );
}

// ---- one-offs -------------------------------------------------------------------------------------------------------------
function special(c: ChartData, mini: boolean): ReactNode {
  switch (c.type) {
    case "map": {
      const top = arr(c.ranked).slice(0, mini ? 5 : 10), bottom = arr(c.bottom).slice(0, mini ? 0 : 5);
      const rows = [...top.map((x) => ({ label: str(x.label), b: num(x.value) ?? 0 })), ...bottom.map((x) => ({ label: `… ${str(x.label)}`, b: num(x.value) ?? 0 }))];
      return <Bars rows={rows} max={Math.max(...rows.map((r) => r.b), 0)} fmt={(v) => v.toFixed(2)} mini={mini} />;
    }
    case "splits": {
      const rows = arr(c.rows);
      const agree = rows.filter((r) => r.agree).length;
      if (mini) return <Bars rows={[{ label: "sides with the majority", b: agree / (rows.length || 1) }]} max={1} fmt={(v) => `${Math.round(v * 100)}%`} mini />;
      // Jev's breaks from the majority first; the full list is in the questions below the case study
      const sorted = [...rows].sort((x, y) => Number(Boolean(x.agree)) - Number(Boolean(y.agree))).slice(0, 24);
      return (
        <>
        <p className="ex-foot">{rows.length} questions; Jev breaks from the most common answer on {rows.length - agree}. {rows.length > 24 ? "The first 24 are shown, breaks first." : ""}</p>
        <ol className="ex-splits">
          {sorted.map((r, i) => (
            <li key={i} className={r.agree ? "ok" : "no"}>
              <span className="q">{str(r.label)}</span>
              <span className="a">Jev: <b>{pretty(str(r.jev))}</b>{r.agree ? "" : <> · most: {pretty(str(r.human_top))}</>}</span>
            </li>
          ))}
        </ol>
        </>
      );
    }
    case "wordstrip": {
      const vals = arr(c.values);
      const names = [...new Set(vals.map((v) => str(v.phrase)))];
      return (
        <div className={`ex-wordstrip${mini ? " mini" : ""}`}>
          <div className="strip">{vals.map((v, i) => <span key={i} style={{ ["--h" as string]: names.indexOf(str(v.phrase)) / (names.length || 1) }} title={`${v.p}%: ${str(v.phrase)}`}>{mini ? "" : `${v.p}`}</span>)}</div>
          {!mini && <ol className="names">{names.map((n, i) => <li key={n} style={{ ["--h" as string]: i / (names.length || 1) }}>{n}</li>)}</ol>}
        </div>
      );
    }
    case "grid": {
      const rows = arr(c.rows);
      const cols = [...new Set(rows.flatMap((r) => Object.keys((r.cells as Obj) ?? {})))];
      return (
        <div className={`ex-heat${mini ? " mini" : ""}`}><table>
          {!mini && <thead><tr><th />{cols.map((k) => <th key={k}>{k}</th>)}</tr></thead>}
          <tbody>{rows.map((r, i) => <tr key={i}><th>{str(r.label)}</th>{cols.map((k) => <td key={k} className="txt">{str(((r.cells as Obj) ?? {})[k])}</td>)}</tr>)}</tbody>
        </table></div>
      );
    }
    case "type": {
      const axes = (c.axes ?? {}) as Record<string, Obj>;
      const rows = Object.values(axes).map((a) => {
        const letters = arr<string>(a.letters);
        const pk = Object.keys(a).find((k) => /^p_[A-Z]$/.test(k));
        const p = pk ? num(a[pk]) ?? 0.5 : 0.5, pp = pk ? num(a[`people_${pk}`]) : null;
        return { label: `${letters[0]} ← → ${letters[1]}`, p, pp, ci: pair(a.ci90) };
      });
      return (
        <>
          {!mini && <p className="ex-big">{str(c.letters)}</p>}
          <DotRows rows={rows.map((r, i) => ({ key: `${i}`, label: r.label, marks: [...(r.pp !== null ? [{ v: 1 - r.pp, kind: "hum" as const }] : []), { v: 1 - r.p, kind: "jev" as const }], ci: r.ci ? [1 - r.ci[1], 1 - r.ci[0]] : undefined, link: r.pp !== null }))}
            domain={[0, 1]} ticks={mini ? [] : [0, 0.5, 1]} fmt={(v) => `${Math.round(v * 100)}%`} refs={[{ v: 0.5 }]} />
        </>
      );
    }
    case "match": {
      const best = arr(c.best).slice(0, mini ? 3 : 6);
      return <Bars rows={best.map((b) => ({ label: `${str(b.name)} (${str(b.work)})`, b: num(b.r) ?? 0 }))} max={1} fmt={(v) => `r ${v.toFixed(2)}`} mini={mini} />;
    }
    case "map2d": {
      // rows of {label, jev: [x, y], people: [x, y], hi}: two positions per character, linked
      const rows = arr(c.rows);
      const series: Series[] = [
        { name: "Jev", kind: "jev", pts: rows.map((r) => pair(r.jev)).filter(Boolean) as [number, number][], line: false },
        { name: "people", kind: "hum", pts: rows.map((r) => pair(r.people)).filter(Boolean) as [number, number][], line: false },
      ];
      const all = series.flatMap((x) => x.pts);
      const labels = mini ? [] : rows.map((r) => { const j = pair(r.jev); return j ? { label: str(r.label), x: j[0], y: j[1] } : null; }).filter(Boolean) as { label: string; x: number; y: number }[];
      const links = rows.map((r) => [pair(r.jev), pair(r.people)]).filter(([a, b]) => a && b) as [[number, number], [number, number]][];
      return <XY series={series} labels={labels} links={links} xd={pair(c.xdomain) ?? extent(all.map((p) => p[0]), false)} yd={pair(c.ydomain) ?? extent(all.map((p) => p[1]), false)} xl={str(c.x) || "agency"} yl={str(c.y) || "experience"} mini={mini} />;
    }
    case "colorgrid": {
      // rows of {label, people: {color: share}, jev: {color: share} or a color, jev_p}
      const rows = arr(c.rows).slice(0, mini ? 6 : 40);
      const topOf = (d: unknown) => (d && typeof d === "object" ? Object.entries(d as Record<string, number>).sort((a, b) => b[1] - a[1])[0]?.[0] : str(d));
      return (
        <div className={`ex-heat${mini ? " mini" : ""}`}><table>
          {!mini && <thead><tr><th /><th>people&rsquo;s top color</th><th>Jev&rsquo;s</th></tr></thead>}
          <tbody>{rows.map((r, i) => {
            const pc = topOf(r.people) ?? "", jc = topOf(r.jev) ?? "";
            return (
              <tr key={i}>
                {!mini && <th>{str(r.label)}</th>}
                <td className="txt"><i className="sw" style={{ background: pc }} />{mini ? "" : pc}</td>
                <td className="txt"><i className="sw" style={{ background: jc }} />{mini ? "" : `${jc}${pc === jc ? " ✓" : ""}`}</td>
              </tr>
            );
          })}</tbody>
        </table></div>
      );
    }
    default:
      return null;
  }
}

export default function Chart({ chart, mini = false }: { chart: ChartData; mini?: boolean }) {
  const t = chart?.type;
  let body: ReactNode = null;
  if (["dots", "effects", "forest", "strip", "range", "dumbbell", "slope"].includes(t)) body = rowsChart(chart, mini);
  else if (["ranked", "bars", "bars2", "mix"].includes(t)) body = barsChart(chart, mini);
  else if (["scatter", "rankscatter", "binned", "calibration", "reliability"].includes(t)) body = xyChart(chart, mini);
  else if (t === "heat") body = heat(chart, mini);
  else if (t === "ridge") body = ridge(chart, mini);
  else body = special(chart, mini);
  if (!body) return mini ? null : <p className="ex-foot">No chart for this experiment.</p>;
  return <div className={`ex-chart t-${t}${mini ? " mini" : ""}`}>{body}</div>;
}
