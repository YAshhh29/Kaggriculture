#!/bin/bash
cd /c/Users/Oyash/Desktop/Kaggriculture
run() {  # factory label opponents...
  f=$1; l=$2; shift 2
  PYTHONIOENCODING=utf-8 ./.conda/python.exe -u -m tools.eval.paired "$f" --label "$l" --opponents "$@" --seeds $(seq 100 129) --workers 1 2>&1 | grep -v pyspiel > "rl/data/l2/eval/$l.log"
}
runf() {
  PYTHONIOENCODING=utf-8 ./.conda/python.exe -u -m tools.eval.paired "$1" --label "$2" --opponents nb_haideptry_shepherds nb_haideptry_2965 nb_leoprovorov_forecast nb_dmitrii_herdsafe_2700 nb_ahmed_v55 live_H2 A --seeds 11 29 53 97 --workers 2 2>&1 | grep -v pyspiel > "rl/data/l2/eval/$2.log"
}
run rl.l2_combo:lot_dump    r2-lot-dump    L &
run rl.l2_combo:lot_rt      r2-lot-rt      L &
run rl.l2_combo:lot_dump_rt r2-lot-dump-rt L &
run rl.l2_combo:core        r2-core        L &
run rl.l2_combo:core_lot    r2-core-lot    L &
run rl.l2_combo:full        r2-full        L &
run rl.l2_combo:full        r2-full-vsA    A &
runf rl.l2_combo:full       r2-full-field &
wait
echo ROUND2 DONE
