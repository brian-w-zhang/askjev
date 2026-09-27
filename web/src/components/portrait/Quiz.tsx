"use client";

import { createContext, useContext, useSyncExternalStore, type ReactNode } from "react";
import type { QuizItem } from "./types";

// "Answer it yourself" (the NYT Upshot move): the reader answers five real questions before seeing Jev or the crowd,
// and the answers carry down to "You vs Jev" at the end. Kept in this browser only.
const KEY = "askjev.portrait.quiz";
type Answers = Record<string, string>;
const listeners = new Set<() => void>();
let raw: string | null = null;
const readRaw = () => {
  try { raw = localStorage.getItem(KEY); } catch {}
  return raw ?? "{}";
};
const subscribe = (cb: () => void) => { listeners.add(cb); return () => { listeners.delete(cb); }; };
const write = (a: Answers) => {
  try { localStorage.setItem(KEY, JSON.stringify(a)); } catch { raw = JSON.stringify(a); }
  listeners.forEach((l) => l());
};
const Ctx = createContext<{ items: QuizItem[]; answers: Answers; answer: (id: string, k: string) => void; reset: () => void } | null>(null);

export function QuizProvider({ items, children }: { items: QuizItem[]; children: ReactNode }) {
  const text = useSyncExternalStore(subscribe, readRaw, () => "{}");
  let answers: Answers = {};
  try { answers = JSON.parse(text) ?? {}; } catch {}
  return (
    <Ctx.Provider value={{ items, answers, answer: (id, k) => write({ ...answers, [id]: k }), reset: () => write({}) }}>
      {children}
    </Ctx.Provider>
  );
}

const top = (d: Record<string, number>) => Object.keys(d).reduce((a, b) => (d[b] > d[a] ? b : a));
const pct = (x: number) => `${Math.round(x * 100)}%`;

export function Quiz() {
  const q = useContext(Ctx)!;
  return (
    <div className="quiz">
      {q.items.map((it, i) => {
        const mine = q.answers[it.id];
        return (
          <div className="qz" key={it.id}>
            <h4><small>{String(i + 1).padStart(2, "0")} / {String(q.items.length).padStart(2, "0")} · {it.domain}</small>{it.text}</h4>
            {!mine ? (
              <div className="opts">
                {it.options.map((o) => (
                  <button key={o.key} type="button" className="o" onClick={() => q.answer(it.id, o.key)}>{o.label}</button>
                ))}
              </div>
            ) : (
              <>
                <div className="res">
                  {it.options.map((o) => (
                    <div key={o.key} className={`rr${o.key === mine ? " you" : ""}`}>
                      <span className="rl">{o.label}</span>
                      <span className="pt-opt" style={{ gridTemplateColumns: "1fr", padding: 0 }}>
                        <span className="ob">
                          <i className="j" style={{ width: `${(it.jev[o.key] ?? 0) * 100}%` }} />
                          <i className="h" style={{ width: `${(it.human[o.key] ?? 0) * 100}%` }} />
                          <em>Jev {pct(it.jev[o.key] ?? 0)} · people {pct(it.human[o.key] ?? 0)}</em>
                        </span>
                      </span>
                    </div>
                  ))}
                </div>
                <p className="note">
                  {mine === top(it.human) ? "You sided with most people" : "Most people answered differently"}
                  {" · "}
                  {mine === top(it.jev) ? "so did Jev's likeliest answer" : "Jev's likeliest answer differs from yours"}
                  {it.n ? ` · ${it.n.toLocaleString("en-US")} people answered` : ""}
                </p>
              </>
            )}
          </div>
        );
      })}
    </div>
  );
}

export function YouVsJev() {
  const q = useContext(Ctx)!;
  const done = q.items.filter((it) => q.answers[it.id]);
  if (!done.length) {
    return (
      <p style={{ margin: 0, fontSize: 16 }}>
        You have not answered the five questions yet. <a href="#quiz">Answer them</a> and this window compares you, Jev and the crowd.
      </p>
    );
  }
  const youCrowd = done.filter((it) => q.answers[it.id] === top(it.human)).length;
  const jevCrowd = q.items.filter((it) => top(it.jev) === top(it.human)).length;
  const youJev = done.filter((it) => q.answers[it.id] === top(it.jev)).length;
  return (
    <>
      <div className="youvs">
        <div><div className="n">{youCrowd}/{done.length}</div><div className="d">times you gave the crowd&rsquo;s most common answer</div></div>
        <div><div className="n" style={{ color: "var(--jev)" }}>{jevCrowd}/{q.items.length}</div><div className="d">times Jev&rsquo;s likeliest answer was the crowd&rsquo;s</div></div>
        <div><div className="n">{youJev}/{done.length}</div><div className="d">times you and Jev agreed</div></div>
      </div>
      <p style={{ margin: "12px 0 0", display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <span style={{ fontSize: 14, color: "var(--w-fg-2)" }}>Five questions are a coin toss, not a measurement: this is for fun.</span>
        <button type="button" className="pt-btn ghost" onClick={q.reset}>Answer again</button>
      </p>
    </>
  );
}
