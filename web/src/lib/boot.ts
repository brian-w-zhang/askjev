// The map page starts its data downloads in an inline script, before any bundle loads (app/page.tsx). Whoever asks
// for one of those URLs first gets that request; every other fetch goes out as usual.
export function bootFetch(url: string): Promise<Response> {
  const boot = typeof window !== "undefined" ? (window as unknown as { __boot?: Record<string, Promise<Response>> }).__boot : undefined;
  const p = boot?.[url];
  if (!p) return fetch(url);
  delete boot[url];
  return p.catch(() => fetch(url));
}
