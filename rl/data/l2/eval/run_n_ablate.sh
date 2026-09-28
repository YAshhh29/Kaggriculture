#!/bin/bash
cd /c/Users/Oyash/Desktop/Kaggriculture
run() { PYTHONIOENCODING=utf-8 ./.conda/python.exe -u -m tools.eval.live_replay run --agent factory --package rl.l2_combo:$1 --submission 56618602 --label "$1 on M live" --workers 4 2>&1 | grep --line-buffered -v pyspiel > "rl/data/l2/eval/replay_M.$1.log"; }
run n_no_lot & run n_no_rt & wait
run n_no_feed & run n_no_labour & wait
run n_no_msell
echo all done
