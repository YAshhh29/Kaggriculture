#!/bin/bash
# M5 on every real game we hold, two replays at a time (8 workers: the machine has 16 GB).
cd /c/Users/Oyash/Desktop/Kaggriculture
run() { PYTHONIOENCODING=utf-8 ./.conda/python.exe -u -m tools.eval.live_replay run --agent factory --package rl.l2_combo:m5 --submission $1 --label "$2" --workers 4 2>&1 | grep --line-buffered -v pyspiel > rl/data/l2/eval/replay_$1.m5.log; }
run 56601363 "M5 on L3 live" & run 56601249 "M5 on L2 live" & wait
run 56609589 "M5 on L4 live" & run 56582917 "M5 on L live 116" & wait
run 56571049 "M5 on A live 159"
echo all done
