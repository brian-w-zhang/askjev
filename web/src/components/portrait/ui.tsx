import type { ReactNode } from "react";
import Link from "next/link";
import type { Claim, Row } from "./types";
import type { CardCopy } from "./copy";
import { int, optionLabel, pct, truthKey } from "./fmt";
import ThemeToggle from "./ThemeToggle";

export type Field = "paper" | "pink" | "teal" | "sage" | "magenta" | "ink";

export function Nav({ here }: { here: "portrait" | "atlas" }) {
  return (
    <nav className="pt-nav" aria-label="Portrait">
      <div className="grp"><Link className="pt-chipnav brand" href="/">askjev</Link></div>
      <div className="grp">
        <Link className="pt-chipnav" href="/portrait" aria-current={here === "portrait" ? "page" : undefined}>Portrait</Link>
        <Link className="pt-chipnav" href="/portrait/atlas" aria-current={here === "atlas" ? "page" : undefined}>Atlas</Link>
        <Link className="pt-chipnav" href="/">Map</Link>
      </div>
      <div className="grp"><ThemeToggle /></div>
    </nav>
  );
}

// Fill a copy template: {name} from vars, *text* highlighted. A missing value shows as ⟨name⟩ so it can't hide.
export function fill(t: string | undefined, vars: Record<string, string | number> = {}): ReactNode {
  if (!t) return null;
  const s = t.replace(/\{(\w+)\}/g, (_, k) => (vars[k] !== undefined ? String(vars[k]) : `⟨${k}⟩`));
  return s.split(/(\*[^*]+\*)/g).map((p, i) => (p.startsWith("*") && p.endsWith("*") ? <mark key={i}>{p.slice(1, -1)}</mark> : p));
}

const TIER: Record<string, string> = {
  "1": "published instrument or real answers", "2": "audited questions I wrote", "3": "embedding theme",
  discovery: "topic indicator", corpus: "corpus count", pipeline: "pipeline logs",
};

// One card: a full screen with a color field, the words from copy.ts, a visual, an optional aside (usually a meme),
// the fine print, and the receipts (real rows, n, interval, ledger ids) behind a toggle.
export function Card({ id, field = "paper", c, vars, big, children, aside, asideAt = "right", claims = [], rows, note, showId, wide }: {
  id: string; field?: Field; c: CardCopy; vars?: Record<string, string | number>; big?: ReactNode; children?: ReactNode;
  aside?: ReactNode; asideAt?: "right" | "below" | "left"; claims?: Claim[]; rows?: Row[]; note?: ReactNode; showId?: boolean; wide?: boolean;
}) {
  const c0 = claims[0];
  return (
    <section id={id} className="card" data-f={field}>
      {showId && <span className="card-id">{id}</span>}
      <div className={`card-in${aside ? ` has-aside at-${asideAt}` : ""}${wide ? " wide" : ""}`}>
        <div className="card-main">
          {c.kicker && <span className="pt-tag">{c.kicker}</span>}
          {big && <div className="big">{big}</div>}
          <h2 className="card-t">{fill(c.title, vars)}</h2>
          {c.body && <p className="card-b">{fill(c.body, vars)}</p>}
          {children && <div className="card-v">{children}</div>}
        </div>
        {aside && <div className="card-aside">{aside}</div>}
        {(c.fine || claims.length > 0) && (
          <div className="card-foot">
            {c.fine && <p className="fine">{fill(c.fine, vars)}</p>}
            {claims.length > 0 && (
              <details className="receipts">
                <summary>receipts</summary>
                <p className="rc-meta">
                  {TIER[c0.tier] ?? c0.tier} · n = {int(claims.length === 1 ? c0.n : Math.max(...claims.map((x) => x.n)))}
                  {claims.length === 1 && c0.ci90 && typeof c0.effect === "number" ? ` · 90% interval ${fmtCi(c0)}` : ""}
                  {note ? <> · {note}</> : null}
                  <br />ledger: {claims.map((x) => x.id).join(", ")}
                </p>
                {rows && rows.length > 0 && <ol className="rc-rows">{rows.map((r) => <QuestionRow key={r.id} row={r} />)}</ol>}
              </details>
            )}
          </div>
        )}
      </div>
    </section>
  );
}

// a share is shown as percents (its sentence says "%"); a coefficient or percentile as plain numbers
function fmtCi(c: Claim) {
  const [a, b] = c.ci90!;
  if (String(c.sentence).includes("%") && a >= 0 && b <= 1) return `${pct(a)}–${pct(b)}`;
  const f = (x: number) => (Math.abs(x) > 2 ? x.toFixed(0) : x.toFixed(3));
  return `${f(a)} to ${f(b)}`;
}

// A plain OS window around a visual
export function Win({ title, children, className = "" }: { title: string; children: ReactNode; className?: string }) {
  return (
    <div className={`pt-win ${className}`}>
      <div className="pt-bar"><span>{title}</span><span className="sp" /><span className="dots" aria-hidden>▪▪▪</span></div>
      <div className="pt-body">{children}</div>
    </div>
  );
}

export const Legend = {
  jev: <span key="j"><i className="k jev" />Jev</span>,
  guess: <span key="g"><i className="k guess" />Jev, for &lsquo;most people&rsquo;</span>,
  hum: <span key="h"><i className="k hum" />real people</span>,
};

// One real question: Jev's distribution next to the human one (or Jev's guess for 'most people').
export function QuestionRow({ row }: { row: Row }) {
  const human = row.human?.dist ?? null;
  const other = human ?? row.people;
  const keys = Object.keys(row.jev ?? {});
  const t = truthKey(row);
  const score = (k: string) => Math.max(row.jev?.[k] ?? 0, other?.[k] ?? 0);
  const keep = new Set([...keys].sort((a, b) => score(b) - score(a)).slice(0, 6));
  const shown = keys.length <= 6 ? keys : keys.filter((k) => keep.has(k) || k === t);
  return (
    <li className="pt-q">
      <p className="qt">{row.text}</p>
      {row.state && <p className="qs">{row.state.replace(/^\{|\}$/g, "")}</p>}
      {shown.map((k) => (
        <div className="pt-opt" key={k}>
          <span className={`ol${t === k ? " truth" : ""}`}>{optionLabel(row, k)}</span>
          <span className="ob">
            <i className="j" style={{ width: `${(row.jev?.[k] ?? 0) * 100}%` }} />
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
