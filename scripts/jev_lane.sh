#!/usr/bin/env bash
# Jev lane for the expansion (docs/10-expansion.md §2): loop the pipeline over whatever is pending.
# One process only; ASKJEV_RPS leaves headroom for the web app's rerank and ask box.
cd "$(dirname "$0")/.."
export ASKJEV_RPS="${ASKJEV_RPS:-16}"
export ASKJEV_WORKERS="${ASKJEV_WORKERS:-40}"
mkdir -p data/logs
while true; do
  # unanswered, plus unplaced (rows ingested after a pass's place stage get answered but still need a node)
  pending=$(psql "$(grep DATABASE_URL .env | cut -d= -f2-)" -Atc "select (select count(*) from questions q where not exists (select 1 from probes p join answers a on a.probe_id=p.id where p.question_id=q.id)) + (select count(*) from questions where node_id is null)")
  if [ "${pending:-0}" -gt 5 ]; then
    echo "[$(date +%H:%M:%S)] pipeline start, $pending unanswered"
    uv run askjev pipeline 2>&1 | grep --line-buffered -E "^\[|Error|Traceback"
    echo "[$(date +%H:%M:%S)] pipeline done"
  fi
  [ -f data/logs/jev_lane.stop ] && exit 0
  sleep 60
done
