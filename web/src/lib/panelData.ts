import { filterQuery, useStore, type PanelView } from "./store";
import type { Filters } from "./types";

// URLs for what the side panel shows, shared by the views, the panel's preloading and hover prefetch.
export const nodeUrl = (
  id: string,
  scope: "subtree" | "direct" = "subtree",
  filters: Filters = useStore.getState().filters,
  showHidden: boolean = useStore.getState().showHidden,
) => `/api/node/${encodeURIComponent(id)}?scope=${scope}${filterQuery(filters, showHidden)}`;
export const questionUrl = (id: string) => `/api/question/${encodeURIComponent(id)}`;

/** The main data a panel view needs before it can draw (none for the ask box). */
export function viewUrl(v: PanelView): string | null {
  if (v.kind === "node") return nodeUrl(v.id);
  if (v.kind === "question") return questionUrl(v.id);
  return null;
}
