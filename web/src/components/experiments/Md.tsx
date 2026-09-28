import type { ReactNode } from "react";

// The little markdown the case studies use (docs/17): paragraphs, "- " bullet lists, "> " quotes, **bold**, *italics*
// and `code`. Rendered as React elements, never as raw HTML.
function inline(text: string, key = ""): ReactNode[] {
  const out: ReactNode[] = [];
  const rx = /(\*\*[^*]+\*\*|\*[^*\s][^*]*\*|`[^`]+`)/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let i = 0;
  while ((m = rx.exec(text))) {
    if (m.index > last) out.push(text.slice(last, m.index));
    const t = m[0];
    const k = `${key}-${i++}`;
    if (t.startsWith("**")) out.push(<strong key={k}>{t.slice(2, -2)}</strong>);
    else if (t.startsWith("`")) out.push(<code key={k}>{t.slice(1, -1)}</code>);
    else out.push(<em key={k}>{t.slice(1, -1)}</em>);
    last = m.index + t.length;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

type Block = { kind: "p" | "ul" | "quote"; lines: string[] };

// Line by line: "- " starts a list item (indented lines continue it), "> " a quote, blank lines end a block.
function blocks(text: string): Block[] {
  const out: Block[] = [];
  let cur: Block | null = null;
  for (const raw of text.trim().split("\n")) {
    const line = raw.trimEnd();
    if (!line.trim()) { cur = null; continue; }
    if (line.startsWith("- ")) {
      if (cur?.kind !== "ul") out.push((cur = { kind: "ul", lines: [] }));
      cur.lines.push(line.slice(2));
    } else if (line.startsWith(">")) {
      if (cur?.kind !== "quote") out.push((cur = { kind: "quote", lines: [] }));
      cur.lines.push(line.replace(/^>\s?/, ""));
    } else if (cur?.kind === "ul" && /^\s+\S/.test(raw)) {
      cur.lines[cur.lines.length - 1] += " " + line.trim();
    } else {
      if (cur?.kind !== "p") out.push((cur = { kind: "p", lines: [] }));
      cur.lines.push(line.trim());
    }
  }
  return out;
}

export default function Md({ text }: { text: string }) {
  return (
    <>
      {blocks(text).map((b, i) => {
        if (b.kind === "ul") return <ul key={i}>{b.lines.map((x, j) => <li key={j}>{inline(x, `${i}-${j}`)}</li>)}</ul>;
        if (b.kind === "quote") {
          // a quoted question: a new paragraph starts wherever a line opens with emphasis (the answer options)
          const parts: string[] = [];
          for (const l of b.lines) {
            if (!parts.length || l.startsWith("*")) parts.push(l);
            else parts[parts.length - 1] += " " + l;
          }
          return <blockquote key={i}>{parts.map((x, j) => <p key={j}>{inline(x, `${i}-${j}`)}</p>)}</blockquote>;
        }
        return <p key={i}>{inline(b.lines.join(" "), `${i}`)}</p>;
      })}
    </>
  );
}
