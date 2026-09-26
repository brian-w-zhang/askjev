"use client";
import { useEffect, useState } from "react";

// Panel data, stale-while-revalidate style (docs/07-ui.md, Side panel): every topic and question the panel
// fetches is kept, so Back / Forward and revisits render instantly, and hovering a link fetches ahead.

interface Entry { data?: unknown; error?: string; p?: Promise<unknown> }
const entries = new Map<string, Entry>();
const MAX = 300;

/** Fetch `url` once; later calls share the same promise or the cached result. */
export function load<T>(url: string): Promise<T> {
  const e = entries.get(url);
  if (e?.data !== undefined) return Promise.resolve(e.data as T);
  if (e?.p) return e.p as Promise<T>;
  const p = fetch(url)
    .then((r) => r.json())
    .then((d) => {
      if (d?.error) throw new Error(d.error);
      entries.set(url, { data: d });
      if (entries.size > MAX) entries.delete(entries.keys().next().value!);
      return d as T;
    })
    .catch((err: Error) => {
      entries.set(url, { error: err.message });
      throw err;
    });
  entries.set(url, { p });
  return p;
}

export function peek<T>(url: string): T | undefined {
  return entries.get(url)?.data as T | undefined;
}

/** Warm the cache (on hover), ignoring errors. */
export function prefetch(url: string) {
  load(url).catch(() => {});
}

/** The cached value for `url` right away when there is one; otherwise it arrives when loaded. */
export function useResource<T>(url: string): { data: T | undefined; error: string | undefined } {
  const [state, setState] = useState<{ url: string; data?: T; error?: string }>(() => ({ url, data: peek<T>(url) }));
  const cur = state.url === url ? state : { url, data: peek<T>(url) };
  useEffect(() => {
    if (peek(url) !== undefined) return;
    let live = true;
    load<T>(url)
      .then((data) => live && setState({ url, data }))
      .catch((e: Error) => live && setState({ url, error: e.message }));
    return () => { live = false; };
  }, [url]);
  return { data: cur.data, error: cur.error };
}
