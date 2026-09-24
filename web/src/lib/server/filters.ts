import "server-only";

/** Question-level filters shared by the tree and node APIs. Returns SQL fragment + params. */
export function questionFilters(sp: URLSearchParams, alias: string, startIdx: number): { sql: string; params: unknown[]; active: boolean } {
  const parts: string[] = [];
  const params: unknown[] = [];
  const add = (col: string, key: string) => {
    const v = sp.get(key);
    if (!v) return;
    params.push(v.split(","));
    parts.push(`${alias}.${col} = any($${startIdx + params.length - 1})`);
  };
  add("primitive", "primitive");
  add("origin", "origin");
  const kind = sp.get("kind");
  if (kind) {
    params.push(kind.split(","));
    const i = startIdx + params.length - 1;
    parts.push(`(${alias}.kind = any($${i}) or ${alias}.shape = any($${i}))`);
  }
  const active = parts.length > 0;
  if (sp.get("hidden") !== "1") parts.push(`${alias}.display_ok`);
  return { sql: parts.length ? parts.join(" and ") : "true", params, active };
}
