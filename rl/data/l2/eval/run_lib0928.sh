#!/bin/bash
cd /c/Users/Oyash/Desktop/Kaggriculture
run() { PYTHONIOENCODING=utf-8 ./.conda/python.exe -u -m tools.eval.live_replay run --agent factory --package rl.l2_combo:$1 --submission $2 --label "$3" --workers 4 2>&1 | grep --line-buffered -v pyspiel > "rl/data/l2/eval/replay_$2.$1.log"; }
run l5h 56609589 "L5 on L4 live 80" & run l6 56609589 "L6 on L4 live 80" & wait
run m8 56609589 "M8 on L4 live 80" & run m10 56609589 "M10 on L4 live 80" & wait
run l5h 56613410 "L5 on L5 live 47" & run l6 56613410 "L6 on L5 live 47" & wait
run m8 56613410 "M8 on L5 live 47" & run m10 56613410 "M10 on L5 live 47" & wait
echo all done
