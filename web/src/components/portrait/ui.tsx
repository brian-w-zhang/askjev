import type { ReactNode } from "react";
import Link from "next/link";
import type { Claim, Row } from "./types";
import type { CardCopy } from "./copy";
import { int, pct } from "./fmt";
import Receipts from "./Receipts";
import ThemeToggle from "./ThemeToggle";

export type Field = "paper" | "pink" | "teal" | "sage" | "magenta" | "ink";

export function Nav({ here }: { here: "portrait" | "atlas" }) {
  return (
    <nav className="pt-nav" aria-label="Portrait">
      <div className="grp"><Link className="pt-chipnav brand" href="/" prefetch={false}>askjev</Link></div>
      <div className="grp">
        <Link className="pt-chipnav" href="/" prefetch={false}>Map</Link>
        <Link className="pt-chipnav" href="/portrait" prefetch={false} aria-current={here === "portrait" ? "page" : undefined}>Portrait</Link>
        <Link className="pt-chipnav" href="/portrait/atlas" prefetch={false} aria-current={here === "atlas" ? "page" : undefined}>Atlas</Link>
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
              <Receipts rows={rows} meta={<>
                {TIER[c0.tier] ?? c0.tier} · n = {int(claims.length === 1 ? c0.n : Math.max(...claims.map((x) => x.n)))}
                {claims.length === 1 && c0.ci90 && typeof c0.effect === "number" ? ` · 90% interval ${fmtCi(c0)}` : ""}
                {note ? <> · {note}</> : null}
                <br />ledger: {claims.map((x) => x.id).join(", ")}
              </>} />
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

export function pick(rows: Record<string, Row>, ids: string[], k = 3): Row[] {
  return ids.map((i) => rows[i]).filter(Boolean).slice(0, k);
}
