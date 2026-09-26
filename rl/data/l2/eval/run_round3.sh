#!/bin/bash
cd /c/Users/Oyash/Desktop/Kaggriculture
run() { f=$1; l=$2; o=$3
  PYTHONIOENCODING=utf-8 ./.conda/python.exe -u -m tools.eval.paired "$f" --label "$l" --opponents "$o" --seeds $(seq 130 159) --workers 1 2>&1 | grep -v pyspiel > "rl/data/l2/eval/$l.log"; }
run rl.l2_combo:ship       r3-ship-vsA     A &
run rl.l2_ablate:no_fert   r3-nofert-vsA   A &
run rl.l2_ablate:no_rt     r3-nort-vsA     A &
run rl.l2_combo:ship       r3-ship-vsL     L &
run rl.l2_ablate:no_fert   r3-nofert-vsL   L &
run rl.l2_ablate:no_rt     r3-nort-vsL     L &
wait
echo ROUND3 DONE
