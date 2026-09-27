import "server-only";
import { qWith } from "./db";

export type Hit = { id: string; text: string; primitive: string; node_id: string; hemisphere: string; sim: number };

// Search (docs/07-ui.md, Search): the 20 nearest questions by meaning; Jev reorders them after (/api/rerank).
// Two index setups, same results within a few percent (measured on 200 queries against exact search):
// - "vector" (local): full-precision embeddings with an HNSW index, 1.85 GB.
// - "binary" (production copy, EMBED_STORE=binary): half-precision embeddings in a narrow table (qvec) with a
//   1-bit HNSW index (292 MB) that finds 400 candidates, re-ranked exactly: #1 matches exact search 97% of the
//   time, twice as fast; only the top 20 read their full question rows.
// A trigram leg used to run beside it; it never changed the #1 result on 30 test queries and cost ~0.6 s.
const STORE = process.env.EMBED_STORE === "binary" ? "binary" : "vector";

export function nearest(vec: string, hidden: boolean): Promise<Hit[]> {
  const cols = "id, text, primitive, node_id, hemisphere";
  if (STORE === "binary")
    // candidates from the 1-bit index, exact re-rank on the narrow vector table, full rows for the top 20 only
    return qWith<Hit>(
      "set local hnsw.ef_search = 400",
      `with c as (
         select id, embedding <=> $1::halfvec as d from (
           select id, embedding from qvec
            order by binary_quantize(embedding)::bit(384) <~> binary_quantize($1::halfvec) limit 400) x
          order by d limit 20)
       select ${cols.split(", ").map((k) => "q." + k).join(", ")}, 1 - c.d as sim from c join questions q using (id) order by c.d`,
      [vec],
    );
  return qWith<Hit>(
    "set local hnsw.ef_search = 100",
    `select ${cols}, 1 - (embedding <=> $1::vector) as sim from questions
      where embedding is not null and ${hidden ? "true" : "display_ok"}
      order by embedding <=> $1::vector limit 20`,
    [vec],
  );
}

