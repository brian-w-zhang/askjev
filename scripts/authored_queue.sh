#!/usr/bin/env bash
# Round-trip queue for synthetic banks (docs/10-expansion.md §7): runs `askjev authored` on each file listed in
# data/logs/authored_queue.txt, one at a time, skipping files already recorded in data/logs/authored_queue.done.
# Waits while any other round trip is running. Append lines to the queue file to add work; runs until stopped.
cd "$(dirname "$0")/.."
Q=data/logs/authored_queue.txt; D=data/logs/authored_queue.done
touch "$Q" "$D"
while true; do
  next=""
  for f in $(grep -vxF -f "$D" "$Q"); do [ -s "$f" ] && { next=$f; break; }; done  # only files that exist (banks still being written wait)
  if [ -n "$next" ] && ! pgrep -f "[a]skjev authored " >/dev/null; then
    echo "[$(date +%H:%M:%S)] round trip: $next"
    ASKJEV_RPS="${RT_RPS:-4}" ASKJEV_WORKERS="${RT_WORKERS:-10}" uv run askjev authored "$next" 2>&1 | tail -1
    echo "$next" >> "$D"
  fi
  [ -f data/logs/authored_queue.stop ] && exit 0
  sleep 60
done
