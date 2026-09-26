#!/bin/bash
cd /c/Users/Oyash/Desktop/Kaggriculture
( PYTHONIOENCODING=utf-8 ./.conda/python.exe -u -m tools.eval.live_replay run --agent factory --package rl.l2_combo:ship --submission 56582917 --label "L2 final on L live games" --workers 2 2>&1 | grep -v pyspiel | head -3 > rl/data/l2/eval/final-live-L.log
  PYTHONIOENCODING=utf-8 ./.conda/python.exe -m tools.eval.live_replay compare "L on L live games" "L2 final on L live games" 2>&1 | grep -v pyspiel | head -4 >> rl/data/l2/eval/final-live-L.log ) &
( PYTHONIOENCODING=utf-8 ./.conda/python.exe -u -m tools.eval.live_replay run --agent factory --package rl.l2_combo:ship --submission 56571049 --label "L2 final on A live games 103" --workers 3 2>&1 | grep -v pyspiel | head -3 > rl/data/l2/eval/final-live-A.log
  PYTHONIOENCODING=utf-8 ./.conda/python.exe -m tools.eval.live_replay compare "L on A live games 103" "L2 final on A live games 103" 2>&1 | grep -v pyspiel | head -4 >> rl/data/l2/eval/final-live-A.log ) &
PYTHONIOENCODING=utf-8 ./.conda/python.exe -u -m tools.eval.paired rl.l2_combo:ship --label final-field --opponents nb_haideptry_shepherds nb_haideptry_2965 nb_leoprovorov_forecast nb_dmitrii_herdsafe_2700 nb_ahmed_v55 live_H2 A --seeds 11 29 53 97 --workers 3 2>&1 | grep -v pyspiel > rl/data/l2/eval/final-field.log &
PYTHONIOENCODING=utf-8 ./.conda/python.exe -u -m tools.eval.paired rl.l2_combo:ship --label final-vsL-fresh --opponents L --seeds $(seq 160 189) --workers 3 2>&1 | grep -v pyspiel > rl/data/l2/eval/final-vsL-fresh.log &
wait
echo FINAL DONE
