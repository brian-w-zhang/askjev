import type { ReactNode } from "react";
import Link from "next/link";
import type { Claim, Row } from "./types";
import { int, optionLabel, pct, truthKey } from "./fmt";
import ThemeToggle from "./ThemeToggle";

export type Field = "paper" | "pink" | "teal" | "sage" | "magenta" | "ink";

export function Nav({ here }: { here: "portrait" | "atlas" }) {
  return (
    <nav className="pt-nav" aria-label="Portrait">
      <div className="grp">
        <Link className="pt-chipnav brand" href="/">askjev</Link>
      </div>
      <div className="grp">
        <Link className="pt-chipnav" href="/portrait" aria-current={here === "portrait" ? "page" : undefined}>Portrait</Link>
        <Link className="pt-chipnav" href="/portrait/atlas" aria-current={here === "atlas" ? "page" : undefined}>Atlas</Link>
        <Link className="pt-chipnav" href="/">Map</Link>
      </div>
      <div className="grp">
        <ThemeToggle />
      </div>
    </nav>
  );
}

// One chapter: a full-bleed color field opening with crop marks, a pixel tag and a giant grotesk headline.
export function Chapter({ id, n, field, tag, title, dek, small, children }: {
  id: string; n: number; field: Field; tag: string; title: ReactNode; dek?: ReactNode; small?: boolean; children: ReactNode;
}) {
  return (
    <section id={id} className="pt-field" data-f={field} aria-labelledby={`${id}-h`}>
      <header className="pt-open">
        <i className="pt-crop tl" /><i className="pt-crop tr" /><i className="pt-crop bl" /><i className="pt-crop br" />
        <span className="pt-tag">{tag}</span>
        <span className="pt-kicker">Chapter {String(n).padStart(2, "0")}</span>
        <h2 id={`${id}-h`} className={`pt-h1${small ? " sm" : ""}`}>{title}</h2>
        {dek && <p className="pt-dek">{dek}</p>}
      </header>
      {children}
    </section>
  );
}

export function Copy({ label, children }: { label?: string; children: ReactNode }) {
  return (
    <div className="pt-col">
      <div className="pt-copy">
        {label && <span className="pt-label">{label}</span>}
        {children}
      </div>
    </div>
  );
}

const TIER: Record<string, string> = {
  "1": "tier 1 · published instrument or real answers",
  "2": "tier 2 · audited authored items",
  "3": "tier 3 · embedding theme, precision audited",
  discovery: "discovery · node indicator",
  corpus: "corpus count",
  pipeline: "pipeline logs",
};

// A finding: its sentence title (the finding itself), an OS window holding the chart, the evidence line and the
// real rows behind it.
// `sum` adds the claims' n (they cover different questions); otherwise they describe the same questions and n is the
// largest.
export function Fig({ code, title, sub, win, claims, rows, wide, legend, children, note, sum }: {
  code: string; title: ReactNode; sub?: ReactNode; win: string; claims: Claim[]; rows?: Row[]; wide?: boolean;
  legend?: ReactNode; children: ReactNode; note?: ReactNode; sum?: boolean;
}) {
  const c0 = claims[0];
  const n = sum ? claims.reduce((s, c) => s + (c.n || 0), 0) : Math.max(...claims.map((c) => c.n || 0));
  return (
    <figure className="pt-find" id={code}>
      <span className="pt-id">{code} · {TIER[c0?.tier] ?? c0?.tier}</span>
      <h3 className="pt-h3">{title}</h3>
      {sub && <p className="pt-sub">{sub}</p>}
      <div className="pt-desk">
        <div className={`pt-win${wide ? " wide" : ""}`}>
          <div className="pt-bar"><span>{win}</span><span className="sp" /><span className="dots" aria-hidden>▪▪▪</span></div>
          <div className="pt-body">
            {legend && <div className="pt-legend">{legend}</div>}
            {children}
          </div>
          <figcaption className="pt-foot">
            <span>n = <b>{int(n)}</b></span>
            {claims.length === 1 && c0?.ci90 && typeof c0.effect === "number" && <span>90% CI <b>{fmtCi(c0)}</b></span>}
            {note && <span>{note}</span>}
            <span>ledger: {claims.map((c) => c.id).join(", ")}</span>
          </figcaption>
          {rows && rows.length > 0 && <Rows rows={rows} />}
        </div>
      </div>
    </figure>
  );
}

// a share is shown as percents (its sentence says "%"); a coefficient or percentile as plain numbers
function fmtCi(c: Claim) {
  const [a, b] = c.ci90!;
  if (String(c.sentence).includes("%") && a >= 0 && b <= 1) return `${pct(a)}–${pct(b)}`;
  const f = (x: number) => (Math.abs(x) > 2 ? x.toFixed(0) : x.toFixed(3));
  return `${f(a)} to ${f(b)}`;
}

export const Legend = {
  jev: <span key="j"><i className="k jev" />Jev, for itself</span>,
  guess: <span key="g"><i className="k guess" />Jev, for &lsquo;most people&rsquo;</span>,
  hum: <span key="h"><i className="k hum" />real people</span>,
  band: <span key="b"><i className="k band" />noise floor</span>,
};

// The drawer: real questions, Jev's distribution next to the human one (or Jev's guess for 'most people').
export function Rows({ rows, title = "Show the rows" }: { rows: Row[]; title?: string }) {
  return (
    <details className="pt-rows">
      <summary>{title} ({rows.length})</summary>
      <ol>
        {rows.map((r) => <QuestionRow key={r.id} row={r} />)}
      </ol>
    </details>
  );
}

export function QuestionRow({ row }: { row: Row }) {
  const human = row.human?.dist ?? null;
  const other = human ?? row.people;
  const keys = Object.keys(row.jev ?? {});
  const t = truthKey(row);
  // show every option for short lists; otherwise the six that matter most to either side, in the original order
  const shown = keys.length <= 6 ? keys
    : keys.filter((k) => [...keys].sort((a, b) => Math.max(row.jev?.[b] ?? 0, other?.[b] ?? 0) - Math.max(row.jev?.[a] ?? 0, other?.[a] ?? 0)).slice(0, 6).includes(k) || k === t);
  return (
    <li className="pt-q">
      <p className="qt">{row.text}</p>
      {row.state && <p className="qs">{row.state.replace(/^\{|\}$/g, "")}</p>}
      {shown.map((k) => (
        <div className="pt-opt" key={k}>
          <span className={`ol${t === k ? " truth" : ""}`}>{optionLabel(row, k)}</span>
          <span className="ob">
            <i className="j" style={{ width: `${(row.jev?.[k] ?? 0) * 100}%` }} title={`Jev ${pct(row.jev?.[k] ?? 0)}`} />
            {other && <i className={human ? "h" : "g"} style={{ width: `${(other[k] ?? 0) * 100}%` }} />}
            <em>Jev {pct(row.jev?.[k] ?? 0)}{other ? ` · ${human ? "people" : "Jev for most people"} ${pct(other[k] ?? 0)}` : ""}</em>
          </span>
        </div>
      ))}
      {keys.length > shown.length && <p className="qm">+ {keys.length - shown.length} more options near 0%</p>}
      <p className="qm">
        {row.node.replaceAll(".", " › ")} · {row.source}
        {row.human?.n ? ` · ${int(row.human.n)} people${row.human.population ? ` (${row.human.population})` : ""}` : ""}
      </p>
    </li>
  );
}

export function pick(rows: Record<string, Row>, ids: string[], k = 3): Row[] {
  return ids.map((i) => rows[i]).filter(Boolean).slice(0, k);
}
