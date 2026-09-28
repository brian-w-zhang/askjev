import type { Row } from "./types";
import { int, optionLabel, pct, truthKey } from "./fmt";

// One real question: Jev's own answer next to real people's (or to what Jev thinks most people would say).
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
            <em>Jev {pct(row.jev?.[k] ?? 0)}{other ? ` · ${human ? "real people" : "what Jev thinks most people would say"} ${pct(other[k] ?? 0)}` : ""}</em>
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

