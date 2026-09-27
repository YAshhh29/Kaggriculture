#!/bin/bash
# run_variant.sh <factory> <tag> [sets...]: a candidate on our real games, two replays at a time.
cd /c/Users/Oyash/Desktop/Kaggriculture
fac=$1; tag=$2; shift 2
sets=${*:-"56601363:L3 56601249:L2 56609589:L4"}
run() { PYTHONIOENCODING=utf-8 ./.conda/python.exe -u -m tools.eval.live_replay run --agent factory --package rl.l2_combo:$fac --submission $1 --label "$tag on $2 live" --workers 4 2>&1 | grep --line-buffered -v pyspiel > rl/data/l2/eval/replay_$1.$fac.log; }
n=0
for s in $sets; do run ${s%%:*} ${s##*:} & n=$((n+1)); if [ $n -eq 2 ]; then wait; n=0; fi; done
wait
echo "$tag done"
