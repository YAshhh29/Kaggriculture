#!/bin/bash
# Round 1: every L2 candidate vs L, seeds 100-129, both seats, one worker each, all in parallel.
cd /c/Users/Oyash/Desktop/Kaggriculture
run() {
  PYTHONIOENCODING=utf-8 ./.conda/python.exe -u -m tools.eval.paired "$1" --label "$2" --seeds $(seq 100 129) --workers 1 2>&1 | grep -v pyspiel > "rl/data/l2/eval/$2.log"
}
run rl.l2_endgame:build        r1-endgame &
run rl.l2_endgame:build_gated  r1-endgame-gated &
run rl.l2_outfarm:lot          r1-lot &
run rl.l2_outfarm:fgate        r1-fgate &
run rl.l2_outfarm:fgate_lot    r1-fgate-lot &
run rl.l2_shadow:build_early   r1-shadow-early &
run rl.l2_shadow:build_both    r1-shadow-both &
run rl.l2_wheat_fert:build     r1-wheat-fert &
run rl.l2_wheat_rt:build       r1-wheat-rt &
run rl.l2_labour:build         r1-labour &
run rl.l2_animals:build        r1-animals &
wait
echo ROUND1 DONE
