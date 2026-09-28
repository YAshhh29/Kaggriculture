#!/bin/bash
cd /c/Users/Oyash/Desktop/Kaggriculture
t() { PYTHONIOENCODING=utf-8 ./.conda/python.exe -u -m tools.arena.arena tourney "$@" --seeds 11 105 211 307 --workers 6 2>&1 | grep --line-buffered " vs "; }
t N2 N2m M2 --vs A
t N2 N2m M2 --vs nb_haodou092_harvest_ledger
t N2 N2m M2 --vs nb_haideptry_the_2965_master_hybrid_engine
t N2 N2m --vs M2
echo all done
