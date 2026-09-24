"use client";
import { useEffect, useRef, useState } from "react";
import { openQuestion, travel } from "@/lib/actions";

type Prim = "noul" | "choice" | "score";
const PRIMS: { id: Prim; name: string; what: string; example: string }[] = [
  { id: "noul", name: "Noul", what: "A yes / no proposition", example: "Is a hot dog a sandwich?" },
  { id: "choice", name: "Choice", what: "Pick one of 2 to 20 options", example: "Best pizza topping?" },
  { id: "score", name: "Score", what: "2 to 10 ordered levels", example: "How spicy is too spicy?" },
];

const slug = (s: string) => s.trim().toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "").slice(0, 40) || "option";

interface AskResult { question_id?: string; duplicate_of?: string | null; node_id?: string; error?: string; flags?: string[]; display_ok?: boolean }

export function AskBox({ onClose, initial = "" }: { onClose: () => void; initial?: string }) {
  const [prim, setPrim] = useState<Prim>("noul");
  const [text, setText] = useState(initial);
  const [opts, setOpts] = useState<string[]>(["", ""]);
  const [levels, setLevels] = useState<string[]>(["", "", ""]);
  const [busy, setBusy] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [err, setErr] = useState<string | null>(null);
  const t0 = useRef(0);

  useEffect(() => {
    if (!busy) return;
    const h = setInterval(() => setElapsed((performance.now() - t0.current) / 1000), 200);
    return () => clearInterval(h);
  }, [busy]);

  const list = prim === "choice" ? opts : levels;
  const setList = prim === "choice" ? setOpts : setLevels;
  const max = prim === "choice" ? 20 : 10;
  const filled = list.map((o) => o.trim()).filter(Boolean);
  const ready = text.trim().length > 3 && (prim === "noul" || filled.length >= 2);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!ready || busy) return;
    setErr(null);
    let options: unknown = null;
    if (prim === "choice") {
      const o: Record<string, string | null> = {};
      for (const name of filled) {
        let k = slug(name);
        while (k in o) k += "_";
        o[k] = name;
      }
      options = o;
    } else if (prim === "score") options = filled;
    setBusy(true);
    t0.current = performance.now();
    try {
      const r = await fetch("/api/ask", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ text: text.trim(), primitive: prim, options, state: null }) });
      const d = (await r.json()) as AskResult;
      if (!r.ok || d.error || !d.question_id) throw new Error(d.error ?? `ask failed (${r.status})`);
      const note = d.duplicate_of
        ? "Someone already asked this. Here is the original question; its ask count went up by one."
        : d.display_ok === false
          ? "Jev answered, but the content filter flagged this question, so it stays off the public map."
          : "Asked and answered. Jev's answers are below.";
      openQuestion(d.question_id, note);
      const tree = await fetch(`/api/question/${encodeURIComponent(d.question_id)}`).then((x) => x.json());
      if (tree.ancestors) travel(tree.ancestors.map((a: { id: string }) => a.id));
    } catch (e2) {
      setErr((e2 as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <div className="panel-head">
        <span style={{ fontWeight: 600 }}>Ask Jev a question</span>
        <button className="iconbtn" onClick={onClose} aria-label="Close panel">✕</button>
      </div>
      <form className="panel-body ask" onSubmit={submit} data-testid="ask-box">
        <p className="note" style={{ marginTop: 0 }}>
          Your question is checked against existing ones, placed on the tree, then answered by Jev in both frames with three option shuffles. It stays private.
        </p>
        <label>Question type</label>
        <div className="prims" role="group" aria-label="Question type">
          {PRIMS.map((p) => (
            <button type="button" key={p.id} aria-pressed={prim === p.id} onClick={() => setPrim(p.id)} data-testid={`prim-${p.id}`}>
              <b>{p.name}</b>
              <span>{p.what}</span>
            </button>
          ))}
        </div>
        <label htmlFor="ask-text">{prim === "noul" ? "Proposition" : "Question"}</label>
        <textarea id="ask-text" data-testid="ask-text" value={text} onChange={(e) => setText(e.target.value)} placeholder={PRIMS.find((p) => p.id === prim)!.example} />
        {prim !== "noul" && (
          <>
            <label>{prim === "choice" ? "Options (Jev sees these names)" : "Levels, lowest to highest"}</label>
            {list.map((o, i) => (
              <div className="optrow" key={i}>
                <span className="n num">{i + 1}</span>
                <input
                  type="text"
                  data-testid={`opt-${i}`}
                  value={o}
                  onChange={(e) => setList(list.map((x, j) => (j === i ? e.target.value : x)))}
                  placeholder={prim === "choice" ? (i === 0 ? "Pepperoni" : i === 1 ? "Mushroom" : "Another option") : i === 0 ? "A little tingle on the tongue" : i === 1 ? "You reach for water after each bite" : "Describe a situation"}
                />
                {list.length > 2 && (
                  <button type="button" className="iconbtn" onClick={() => setList(list.filter((_, j) => j !== i))} aria-label={`Remove ${prim === "choice" ? "option" : "level"} ${i + 1}`}>✕</button>
                )}
              </div>
            ))}
            {list.length < max && <button type="button" className="addopt" onClick={() => setList([...list, ""])}>Add {prim === "choice" ? "option" : "level"}</button>}
            {prim === "score" && <p className="hint">Jev judges each level on its own, so describe situations, not degrees.</p>}
          </>
        )}
        <button className="primary" type="submit" disabled={!ready || busy} data-testid="ask-submit">
          {busy ? "Asking Jev" : "Ask Jev"}
        </button>
        {busy && (
          <div className="working num"><span className="spinner" />Checking for duplicates, placing it on the tree, then asking Jev ({elapsed.toFixed(1)} s)</div>
        )}
        {err && <p className="err" data-testid="ask-error">{err}</p>}
      </form>
    </>
  );
}
