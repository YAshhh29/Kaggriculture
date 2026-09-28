#!/bin/bash
cd /c/Users/Oyash/Desktop/Kaggriculture
until [ -f rl/data/l2/shadow/sync_all_N.json ] && [ -f rl/data/l2/shadow/sync_all_N2.json ]; do sleep 30; done
run() { PYTHONIOENCODING=utf-8 ./.conda/python.exe -u -m tools.eval.live_replay run --agent factory --package rl.l2_combo:$1 --submission $2 --label "$3" --workers 3 2>&1 | grep --line-buffered -v pyspiel > "rl/data/l2/eval/replay_$2.$1.log"; }
run n2m 56633668 "N on N live" & run n2m 56634151 "N on N2 live" & wait
run n3r7 56633668 "N3r7 on N live" & run n3r7 56634151 "N3r7 on N2 live" & wait
run n3r7 56618602 "N3r7 on M live" & run n3r5 56618602 "N3r5 on M live" & wait
run n3r5 56633668 "N3r5 on N live" & run n3r5 56634151 "N3r5 on N2 live" & wait
echo all done
