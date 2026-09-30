"""Raw public programs as seat agents, for scoring them on the same games as ours.

Each factory returns a fresh instance of a public program (rl/public/nb_*.py, or
Agent A) with no layer of ours on top, so the corpus and live test beds can say
how much our stacks add over the public code they are built on or meet.

    python -m tools.analysis.corpus_pin run --factory rl.pub_agents:p_2965 --label t901-p2965
"""

from rl.l2_shadow import sh_program_factory

PUBLIC = {
    "p_a": "A",
    "p_2965": "nb_haideptry_the_2965_master_hybrid_engine",
    "p_2965old": "nb_haideptry_2965",
    "p_hl": "nb_haodou092_harvest_ledger",
    "p_hl0928": "nb_haodou092_harvest_ledger_r0928",
    "p_hosen": "nb_hosen42_v11_hc1_vs_h5_validation",
    "p_tsch2945": "nb_tschinkel_2945",
    "p_salem2900": "nb_salemali7_2900",
    "p_hak2887": "nb_hakdevelopme_2887_score_fieldcraft_agent",
    "p_seyit2820": "nb_seyitkaangun_2820_score",
    "p_jaxa2802": "nb_jaxa623_2802_two_identical_agents_90_points_apar",
    "p_dmitrii2800": "nb_dmitriigluzd_7_turn_rescue_historical_lb_2800",
    "p_avioon": "nb_avioon_apex_v7_god_emperor",
    "p_melon2749": "nb_goodpjw2008_melon_threshold_squeeze_2749",
}


def _make(program):
    def factory():
        _, entry = sh_program_factory(program)()
        return entry
    factory.__name__ = program
    return factory


for _alias, _program in PUBLIC.items():
    globals()[_alias] = _make(_program)

PUBLIC["p_flex0930"] = "nb_flexonafft_multi_route_farming_agent_r0930"
p_flex0930 = _make(PUBLIC["p_flex0930"])
PUBLIC["p_hl0930"] = "nb_haodou092_harvest_ledger_r0930"
p_hl0930 = _make(PUBLIC["p_hl0930"])
