#!/bin/bash
cd /c/Users/Oyash/Desktop/Kaggriculture
run() { PYTHONIOENCODING=utf-8 ./.conda/python.exe -u -m tools.eval.live_replay run --agent factory --package rl.l2_combo:$1 --submission $2 --label "$3" --workers 4 2>&1 | grep --line-buffered -v pyspiel > "rl/data/l2/eval/replay_$2.$1.log"; }
run n2m 56618602 "N2m on M live" & run m11 56618602 "M2 on M live" & wait
run n2m 56613410 "N2m on L5 live 125" & run m11 56613410 "M2 on L5 live 125" & wait
run n2 56618602 "N2 on M live" & run n2 56613410 "N2 on L5 live 125" & wait
echo all done
