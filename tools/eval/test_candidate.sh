#!/bin/bash
# test_candidate.sh <factory> [baseline_factory]: a candidate against N on N's
# and N2's own live games (submissions 56633668, 56634151), 3 workers per run
# (16 GB machine), then a game-by-game comparison with the baseline's replay.
cd /c/Users/Oyash/Desktop/Kaggriculture
cand=$1; base=${2:-n2m}
run() { PYTHONIOENCODING=utf-8 ./.conda/python.exe -u -m tools.eval.live_replay run --agent factory --package rl.l2_combo:$1 --submission $2 --label "$1 on $3 now" --workers 3 2>&1 | grep --line-buffered -v pyspiel > "rl/data/l2/eval/replay_$2.$1.now.log"; }
for f in $cand $base; do
  if [ "$f" = "$base" ] && [ -f "rl/data/live_replays/$base-on-n-now.json" ] && [ -f "rl/data/live_replays/$base-on-n2-now.json" ]; then continue; fi
  run $f 56633668 n & run $f 56634151 n2 & wait
done
for s in n n2; do
  PYTHONIOENCODING=utf-8 ./.conda/python.exe -m tools.analysis.replay_diff $base-on-$s-now $cand-on-$s-now 2>&1 | grep -v pyspiel | head -9
done
echo "$cand done"
