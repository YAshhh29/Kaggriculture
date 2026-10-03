"""Candidate I -- a route-replay clone driven by frozen top-of-ladder tapes.

WHAT THIS AGENT IS
==================
Agent I does not plan. It plays back *recorded action tapes* that real teams
at the top of the Kaggriculture leaderboard produced in real games, which this
repository captured into ``kaggle_cache/top200_tapes/``. Every farmer move,
every hand instruction, every hire, land purchase and market order it issues
was chosen by somebody else's agent, in somebody else's game. This is a
deliberate clone, built to sit beside the from-scratch agent and to measure
how far a pure recording carries on its own.

WHOSE TAPES
-----------
The portfolio is listed, with the reason each tape was taken, in
``tools/packaging/prepare_candidate_i_submission.py`` (``SELECTION``), and the
same provenance travels inside the agent as ``ROUTE_META`` -- source team,
leaderboard rank at capture time, episode id, the recorded final scores, and
the exact eight shops the town unlocked in that game. Tapes were taken only
from games the recording team **won**, and were preferred when the team ranked
high, when the recorded final score was high, and when the winning margin over
a strong opponent was large. Selection was then confirmed by direct
measurement: each candidate tape was played, guarded exactly as it ships here,
against the packaged Candidate H2 on a development seed panel, and the
portfolio is the top of that measured ordering, not the top of the paper one.

WHY THERE IS MORE THAN ONE TAPE
-------------------------------
A tape reproduces its own game only on its own seed. Off-seed it drifts,
because the town unlocks a different set of shops and so a different pattern
of demand, and because weeds land on different tiles. The engine draws a shop
every three days from an RNG that weed spawning shares, so the draw is not even
a pure function of the seed -- it moves with how many tiles both farms leave
empty.

So Agent I keeps a portfolio and routes by what the town actually did. Days 0
to 5 run a fixed opening (no shop is unlocked before the end of day 2, so
there is nothing to route on). At the start of day 6, when exactly two shops
are known, it reads ``observation["town"]["unlocked_shops"]``, looks the
ordered pair up in a table built by grouping the tapes on the shops *their*
games unlocked, and commits to that route for the rest of the game. It commits
once and never switches again: the tapes come from different teams, so a later
switch would apply one team's day-20 plan to another team's day-20 farm.

THE GUARDS
----------
Invalid actions are silent no-ops in the engine, so a drifting tape degrades
instead of crashing. Two cheap guards stop the obvious waste, and nothing else
is reactive:

1. ``dead SELL suppression`` -- a SELL for a good the shed does not hold cannot
   fill, but it still burns one of the ten market-order slots the engine
   processes each turn. Agent I projects the shed forward through this turn's
   own DROP / PLACE / PICKUP instructions and through any earlier BUY_PRODUCT
   in the same queue, and drops SELL orders that have nothing behind them,
   which promotes the tape's later real orders into the window. It never lowers
   a quantity: the engine already stops a SELL when the shed runs dry, so an
   over-large quantity costs nothing.

2. ``terminal liquidation`` -- the day-29 nightly tip happens after the last
   market tick, so a good still in the shed when the game ends is worth zero.
   From ``LIQUIDATE_FROM`` Agent I appends SELL orders for whatever the shed
   still holds into the slots the tape left unused, and on the final acting
   step (718) it replaces the market queue outright with a full liquidation,
   most valuable good first.

Nothing else is re-decided. See ``recorded_fraction()`` for the split between
recorded and reactive play.

This module imports nothing from this repository: it is the file that gets
packaged, unchanged apart from a licence header, by
``tools/packaging/prepare_candidate_i_submission.py``.
"""

from __future__ import annotations

import base64
import json
import zlib

# --------------------------------------------------------------------------- engine facts
# Mirrors kaggle_environments/envs/kaggriculture/kaggriculture.py. Kept as plain
# literals so the packaged file needs no imports beyond the standard library.

PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
            "EGG", "MILK", "WOOL", "FERTILIZER")
ANIMALS = {"GOOSE": "COOP", "COW": "PASTURE", "SHEEP": "PASTURE"}
PASS_ACTION = {"farmer": ["PASS"], "hands": [], "market": []}

# The framework calls agents for steps 0..episodeSteps-2; the interpreter runs
# the market for step 718 and only then freezes reward = money.
LAST_ACT_STEP = 718
# Spare-slot top-up starts here; the outright replacement happens at LAST_ACT_STEP.
LIQUIDATE_FROM = 708
# Two mechanisms measured on our own agent and ported here as switches, so
# they can be judged on this baseline rather than assumed.
#
# PREMIUM_SELL_CAP: the glut curves differ hugely per good -- wool reaches the
# price floor after 59 units from equilibrium, strawberry 62, milk 76, melon
# 158, while wheat and egg absorb thousands. A burst sale of the fragile four
# collapses the book for the rest of the game. None disables the cap; the
# closing liquidation ignores it, since unsold stock is worth nothing.
#
# ORDER_MICROSTRUCTURE: `_process_market` walks both players' orders by index
# and quotes each side at the same pre-commit inventory, and a unit that fails
# on cash or shed room aborts its whole order. Sales therefore belong first,
# inventory-priced purchases next, fixed-price orders last.
# MEASURED, AND BOTH MUST STAY OFF. Turning them on together (cap 3, sorted
# queue) against the published aurax7 v7 agent: 0 wins of 16, own score
# 66,891 against 82,946 with them off, margin -84,732. They are worth +1,750
# a game on our own scheduler and they wreck a replayed route, for two
# reasons that the engine makes plain. Capping the tape's sales leaves stock
# in a shed the recorded plan expected to be empty, and a full shed makes
# BUY_PRODUCT fail, which aborts the whole order and spills at dusk. Sorting
# the queue destroys index microstructure that the recorded agent tuned on
# purpose. A route's market queue is part of the route.
PREMIUM_SELL_CAP = None
PREMIUM_GOODS = ("WOOL", "STRAWBERRY", "MILK", "MELON")
ORDER_MICROSTRUCTURE = False
# Two shops are unlocked at the start of day 6 (end of day 2 and end of day 5).
DECIDE_STEP = 144

_DEFAULTS = {"board_size": 10, "shed_capacity": 100, "max_orders": 10}


# --------------------------------------------------------------------------- payload
# Rewritten in place by tools/packaging/prepare_candidate_i_submission.py.
_PAYLOAD_B85 = "c-ri}ZI2vhaxD5+41OLM?3a0=zj39uR<I;4DC#zBgAjDi>RuZ@t2K7l$2c&~f4?MWy1S|}G9ohTX^L9wlSadyuBxY=m(0k>i2r)_r$7G3Uw-`av%mZ2fBvs$|L+ff`ooWZdiV3Q-@W|y+h=cYp8d-YKmGpwKfe3%4?q0r-+uhd`=9^sjr-Ame)gO1{_*?Yy?*uicb~m^cJu7`+r!Iu|Gj<w_U50TeS7%otJ&`sU;NFh*KdBCfAjp$H@o*=iLdtlUw-@L>%%kmhxcFe@|!Qee);|apS?OhyV-_cfBW0R;dk%<VR6^rzWQ!{*Y8H?%g_GdyWc&1)%!1c8nVkHPJfzznhpHvgO9f|yX55S*tLH1-Irf|{{6d;y!r0^qdOOS9Msvx7T+Qt@T-@f9gOD-?|<>9_&UeKw{JfD@Yzf8NKc=1NA3K@%W;nr{@cUh^LPLL_2H{m-+(Ey94~$c@1FUaH|K9lezSNx>XtUkTRIIam`dPkr&~L|d~<lc{OQ9mkzxP)_jfY8!sU-I-+UTuYpz<4_&6VC*FC?{e5@~@nU7HUrN`N34Q%|-<M?&n@a&7s@xT0ATu-y>p7!DJ+)rOHx!!4u1OtECU8Z*sCX{#GFy8TX$6;PxUk&rFFwE?I$KhUldc?Sc_squq@zdoCFXMsh47_n!GT!J$KK!Z>=iu=K=f)Msk-W#J8&H?s`r~-{ZaR+hPY)Z=<)unrOulaMLn{QD4{{b*>hK1fdf+wcgJpT6@K=q4`f^)O|7LtkJa*52`}9xFm%RGwtHWn+zW@8f>o;G1_2oY;cee94!4FpAToAq|-+2lM7Qcq;?kQK9eDvLV&+?UUrW{@_-|*!GUB;(I_LT;I+34~oO)d={+1YDOt1;#j={{;aV1Au2lD&Q9@-^4FO|X7f-S2s)d7N8=@Ak4gtl6uRb+=-klWV=qXIbNPS@muPpLFpJ|9UI+)Ba|!fT*y!OQcDjw-iRvb1WXcEWc(4R~9U)bD3RF9{LFXVc#d`1sUK)wz+zE5ila}&mPUEfS@#*AWU3$x7KteS^Ub;TpKddo0SibP+oAmr!V~N%h&%;55^#)e4YiJ<jWfF^KGw4W9|1aL4}-TR>sIHr#A?CXJ<ejOy%zzoD_RpZ#ZWM3M8197WmfIm?m@&2C$(VR`!Je{C=7g#(N?I5bsk4B4l}dBt)VRn(WF@gp5U4ZN&PiRscw&5pg1iDqsQhuU@OTuZ_A6f{Ee*ll{<p4PeWtoV;<&;|*WNVs^;%4oUScLUyhoXmr-iXWH&<<vqn`#OG`ot&PXtv|xoFYgvpnj{;V=yZl6ky0_hi0Dm!@;Di_(m!M~}rc5DZ<P%gMg5GyS)UXu@?fgrzjRQtRyDTDFA6TNisq_3I9$$h<@Jvr|1Ak$hFV~15SQK{o-juc?zu$g0r@;mFM{>2su@9m)<3gP<E~BWF!@Ap_0dZOz+ZE%jD~DOF=<2+BEfhmSWO0o1;!Q8QT9nbo!X$aj+5?@y_bqXZQVaq>kVafpK3vXY4nh$gRSgbkV<eK5O*#PzI>u?m%q_)`<m3ECX-%!WO#m=}%o6Y*H)H3|>`kI7E1gPC2ocv{GD83@Yeg}W0GHrG2F~LYU)lG$H(p2K3r|5{%J_9FMxR{g^VhF_SB*?S3UJ$pvp5jCu1?;)yj(WxA~5}W7Qx?E)srumcq`(_EoR>=h|<jpAlO|_Uk4v4*?R_|hO4S~=Rb}^v_4MFNKe-3Mg|$dBddeH^Hvl`qJ{9+GGk3-y*xCZPRa70oZsKRdHwSEo5SnZ{|M$bN)FWZ);$;iC`1jeKoyIK=j7?Va6aDg`83Hf<NDs~RaY;eKacUJ@3<1CxKHF>$||{n7e54N$%(qtNzjX27`ojAEwdTw?{QBPb7g@W;*$-UUGhBZIDD<Tw%1iRr)^gI=c=_u7%8yhJ*6{SV|sb(ux=vR(~J8%ACd;|y0pN~U!3AZH!u=FyFzUpPS-^m4c#;e>v3hq_y9b5{5SQSm*Dl)t9SpoGotVl9R2hM_y#6DQ8*k}X7}W#^0a3g{{`~L-|Z})r(LV^i7!K+Jc<f<&R>w!4LU@48XS<^>4dq1iVp}I2pgox*mokwNN5Ll8IyF-TMLr$?bu`M0udybRL*>I+aI<r!3nh^%?d0ze{cG$IF5zh=Wq{Tdva(Vtob=@2D$MQmUyG!bXbz}jW8v)oXQJ>g-7cYvdvVt$-tYZD^P8I=$$V1J2MryvDh3eBjgdJO>OaKecWf$o}4tMMt9d}0sv_-UG;+0p1h@<yCsQvmb@v($018`5=+(+HrfD86HcGTvxEm<y!GED*dY*qq_f^u9WLIxqjkrR_3rSZ%M(OnSKU_7WD?hICkiiho<bvs%<{LJ`$S%48fKeaFqbDIQZbcUXQuiB(=HZcX_A0{!lBwE8MG2^9g*e9PIKU=v7Ps6h!2OgmoDNEsi?nTi5_i%jc-bV+uckp2BCT4Eb`7?-Pyerm=Rf3Dmv7(kZ_({@qEfpr8s6{D_~=CshceloJ%&A67uW});MRxDg<l8==1bZa*#R;2J7iQ@^O+OCp~Y`MX6GhI_#@?f-^>RMLq7<s9!8?D=z@z+miGQ58;>l?IOu9_DQfb1l`eP3HnvTO*_^^caU~=sw};?*oelAt`>sZUsonBq_{bg+n2s6y(0Lu;CB`WPy_I&%E`uimEr=!&A_ktNnA*vfs~+^XoZs}muN9xK{?^FW=0`29z^gS-0BD5Ly<}GQkkvYQC1q5CBW=d1OIqlJUOh}q+D=#czVxZq~lPQ?&2H{p-W$CmQM%m*I$114^I^@&2h<D@Q+`!*`}qEJF}`Kbyi~)F%}2`_8df0(-h?L$4GI}s<2QZo{Fy(I34S4mq%Kz;0~OQ4(PacINO{dd9sjN3m#ZS5-f!Ud1yoxaHoNvm}RoM<WiKCqv&ghNT9S0hAQUbIw39<wCXf^pN<!w0&EjPTb14`0lV;)@2L&<7qHpSA;Wu0I9iRxU2X}GvD7Fn!Nbll#nmt^f9E_&JVqWL*Te?>-YoED(tZL2X^oolv6}(ERm>ec|MTM;7)Bxh(Y;BCyrF8v*}Tv}BjrA_^=ACzYLO+-&qkD|bbIdhZIeriOKa(w$nMF%11UufgS5i6EoLhE2{AWTcbJ#!dqb(A1uZ;H`AmCG*xL$PI;BDgN>z+_%eav(BfKu!gFJQ6wc)JY;sQcPmSQhHv_gsjcIB!(OKAu5Tx#8rl9(|jC@K#;hb`SgDY+X^3cl>X3F9Z(EU%kkEn^6y#OPC82@o)0^Y(N-Vz?GdI+Kgg+6I}Zr?1d_3KrYC2v>CivI;HW+l!*Sr(RW_gYLG^#xyPtwaoLnS$9A+7{YPxL7<Ws<yCHW^$b%-LRqe9@bE+!39x7`zmn%F7!|yyvy;6-=B?MaJ@%yB5#r$3O(bx8m_Nv_R0*f7R*9<?2(_@^$*qYKi9t)8GpqEO<xB<$5tN|7uvQu8dGeeC3I^iIspEAaWkpavZ!JfdW@|D}O)KEV(B{N(Wzh!Jl>ERJP{p$&DB}sY!Y^LE`u1SyG&ssx@+Y8KRu-3s;(x%!@#8!Z*m`_ekMZf;8z5*?O5A!J_Z50fxFweLC-Cz_wn&l=(|)U}svu;a#Tz<Mtx)$z`YV$<$AOScml2$iw00CCDACny&R`ImBV<s#E8MCQu@hn4^yDRXhY0DI-Z1$Cys-A1-*B6GFI~PlY5oc~Oa}=40sRu7DQ?o+PllHn_HpaOImGdGdedNu@+bH9d7kXCXWwiq<O!72qPwPKXVw?L9G~7)er}x+9@pwIDv=LmbI&7v>GU-6S!YBgr)I9J49ULt*e?0mtEE7WjNv0$>1q6oll{3_66G2gi(BXOG$$wnik-}Gxs`D;c|~6>d#i$^k+<?8BqB~w-WcyKyg5hjh1=8|$n>W<uX*t9@?&BBnF>gsX0wIc{bi3lKh9!KQg18(vZ!a$kMg3;^pCUQ^qiNCk=37Jn<wa?qwbfFBR7B)57Lp#e#|wNfLd*U=CU#3ZVWfWJardMAnvPCO^b^k2D}HymsdL;!$)8IFy6%1`JvY5D6yq*2#AO-spRcI5U~bcVtq>p_G6`q5_O@3jO9W@Pk_^=q*FqP(V(sqe#1oCi{fD2`d?37aJn0UlUi$!?Q%MZY@f>6Bqh!mZAl_}P?y6_Zkr2*q0vG)wg74-7Uk4w!J_4YzJ1!|MTIkNzEOF0nmzFu!|!*t3*L=cF{U^mZ?;Wj@fgY7RzC7488g`Ofl^B5k+tXodwj_2BW~}UJpv^c%<arO3WxL?03=?~=c$dg5Rj1qy{&iV#mXRQF0@-Ptp|h#f#Hy}1(w!xN3yslO7iz|H*dU!RANU6N?{o}zBpJjoZA0O>#0y_H)+mt!H~LGr-B5z=N?X}0L!E6p4(Cs5Yr|i-0i)Jc_rq#{YouJXG$4dzZ<2N-;z<bT~(y28r!idolgCx`=c~4!drFfBDvmP^F_b2$MT|-|C+y+^$togyP!(X`5j+Zd4bIa>gZ6}BlMuIkY+HJ<l23p!C1Qg87NDTFTzM9n&pE&Nc##)6)2`UPStlSu3=!k#>fzpL#Q%FWf&s!L9vfP#mfIAJ4cd2&AIEKk_mV%3smliof03u^`WGT1$ytpWQ+eq<N=)d3=$36=M{N0$1%<t_N0;_EioT&E_ykc*k*vuN8GrZXi3jyQRp5;D`G|g**X>j-qzX7j1!TE)Vj+-MQn%merJ1K@(rdLJE81D+%U+!S<IYDU6t|>z#5FZ3b?bDIW`y+d(vh6%0lPXRpuLjDUwfq{^b{1@_fV{+lHN%9jy{0Zw@r!K1Y54>#}!}wVF5(IELd(jyIV*$JdsGJ>yu($jna~lI*gT#9k1jn%|K92X!dv-p=lO7>%JraTuFJMk?dowUSAo84|11`AWgi5v*#Lit}YM1#8Vgb%^X%_vH$@>c8V64{WfF<hYh5P^PiyWylK6%><lvKOlae*kdJ=i3kb;f+rXYTd>b=IZa5)VDaeP+}HJ{I5ekzuGOwaadJ%lfY61{;&iEkv=y6>D_Hq~miSAmY0&ROUB@n4G078sI@C#$Oyd`1+l}&Mxzf*90j(2cR?p>o^y=GGD%zfd-Q^5-@TYIqO5Nab3^3^Y^(^k)+`cVn4{|;{ZPWC-7lGwCsR`Ldj>XQi!Y)`9MrxgubQdZ?8mu;jTn$=~8&eT!=I!DY9*S>T!>f#P#yU-T5rdD6NH^J}um1#aD?KWuY45c3(=w1RI`8=ntSoj`ikU31oWJy|mM`Nh2HS4hxw;kQ6Zm=9qYRVJduD8wQ|`A`10I}-?BTomC`k<=bc%_?QmNV>8J#Ltl`BaQk?lRA(<mZG48?Ksh=Q+19?XLI8FCAmAIM;qaY>@S4Zz(<Ly&UWHVvK5SNHltpGwN{6&AXN$W!EW=)QCY>q`Ns2gLNXJ>l+cQ*t}jhL90p?7D3Bv$43q;Tsj`@QVi;yO0z=pRPR>E)R`CS-p)bsL-^%R*6CHM@BBBm=3Ve2Ao3eDvnlVe4h1cj<_KwXP8CuLwRveYQ>mVoJNS$23wSQw3#z?$q6zjW2$NZvSf7yIZcZyi0NxzH)}<DM`2RYo8&T)e7A|!F6*2Q;Z>*&N-No=6$W#jTUz+a*a$CgKl74I_gm~->ccE#vLzArcqVZDj|$oIUiO+_WF?+{bNJ$mr^xo>(1O>J0lE4Q>){od^@o9&_TZ;s`Sct1tJECPdBeM}gL0u)G-VPuP0c0FDrMryPJg+!dIGQWMavG$6}$JU`7%N!R#-7bk6IoS8w^|Jip0Y<V~!FY%6y9Idiyeca)+(Sd0=9J{wxRbPH~@W9K?{wf`BAz%k)UC!>o{OE=n%pHIEr9RvU%TBrZ%Ehk;A@jP~4WO-}#$SO7E4bv+t>Iz9^JHI0Y!IRH`~7r>$fjcvuZmUP%5gS7bC7#5`p(8;L#NiawxX}b|Gv3K~g1Phe=yq&`LI%>e0Hw|mCCtjnyCY}nuD9nj6o{%J%u2CbHp{tpJ2~tz8*DY!5?#zeBwOki_kMK+#Ue}*L1OU<5yXX>fI9IF;X23Q`K|t?@A#|%%+yq%aBFG&N8mHO}4`!G(g7q-SQvnP$DIab2SMN^d>TfGZ(7qu(%HTzprjhS1;0wp<ysQmKsc6JJP8bbd(h&z+s9V{x<_^A-8>kGfR4>M$nQOQ<Im|Y|!!iaDm_RQPVA2;XhlpZfHFjgF5lloG+&0iOcK35%`rBbM0;;WRIH}k(wjU<yQpN_%2hu=M!e>}ty+rm64<xD#b~JGp*w#F}=FY3!&d>`QhJY<}y$Rf*Dl>@|pSY6QG#emxe3U)@IBc~_;EviuGwkCfP&`xZod!%Zog|901Uqq)HAo|pV8S{LruU+n5I#FsmVfIjspxj+td(Ord)VL1^-k_e3^{P)6_CYc@i;W+axp#Ldr=;Yb*a;Du%2L!`^T=?ZK;ElCHrWC-{~X|l}icBK76}{2*4_Te#68BR=8#4X2b&e?K~F~9N_I+6x#M9x-LY6$_RkeVY5F@m?GPyomeuHh9lc3u-vMUK~k8{F3I?+ELR|ibVwshih}?f6>;QK(2-+kLu}Isgbm%IajOxBhrkt~eq@1W(l=>v1oO5sP@>hG4x@}oO2$=ds1e+9FZh~PDk*coEslLIb$1@5L&myk9rg8I3b%}1?n~exIN>_=XTP%61B7Be=`@yRb(NHQ)^EWEgA6lX)=p}j=Q$!)(~fL(MZ|3Z;wG!fH#3dv=ca=?R|#bXIm?Xf2Cy}%a&j`JY06Sz0!2Y?p9^OcrWD>7*>*=Ua3)5_Y_Pi%U8!wn3>MR1Ni;({V@Yjv-MT|b*f?30U2%udxX7|%-eL|n9I~R?z7<)7fKSRSD~a_8OWVBdtHBcSqw8~>yWaGDwz)RB)i3WJRHaQpgE3TrKZeE1d)hznTu_5x1JQyi#eccVaSFK^rKaT}4q*b%=L4WhM6uLG#Wvf%kxd+7LKv&pc_meYd8Qa7klC*!ALjHY7l>Zn9wTo2tT;tnG$0iZY-#A5ZgxZXu6(4vaZ)i)1SPhxF{te77_1wgcAz(}zJB@U)hQIO4lvt;7zdkdRMjyRdGowEr!Zq^7(<Ao7_S)b4?sI!Kp@LtVX%e7Z0BjFpkMV>FClBwR{;|`36g}|VMY5jbDD&iqI<C1-s4PbGXajL6&1ch37|KD$fjd*RvQ)uk`7gwLrB1nlUNF~g!-X?)lBBlnBI71lqS+y$j!-}h0OWXWOq}t0K@PKq`IncT+@?`qcqGPO}3eHT2OP2k<JQ^b*0LxPziyRJ-VBh#Oo;~{Gfr5o;pjhm2zY=2fkajx>zCcoTjh{ht9t!mu}Syx9xs3MrdL11H<SGjXCR1U$g7QjDjOJkTf}V_Pqq{fuO4kp6kA4fQd_GxnVF7m0i(YGnf<xwnd~_#<)x9F<bk-aA$=4tE^!;vc_X6DrwrPzQ1>0R@nAydb&BKiWYlHRupPapVo7DEsbq{e!FDcHzFcOUQM=F+nRmoCxcztp%wWrX_*-Ptk_$mYS+mx5c%PyBl6M%CYJT_L7<3*1(&w2RUK||Dr-R*aBiAbCBl%(>E2?c>l|NYdY4FA5>0}V+;2&0IVJ<PU<CCBPYa|q6&exKn-yc0-;8S+I35hO1=ix^!AhJUy{@*#8t{o{nGo4o%(0>DBbobxL$pR9@cL0oItj*Q3n4fuDuDJtr3Ap6OIVL+78JDtxs*3nZp~23HsiurPTq16;}t=Pj*kuK(-Sx$g_S*oJpWC6`#|+eIumc!wPr{y3AWKzEMBQY4R4g8Dw+qwr;DuKS}SUYDH3nhXUuZz9iuJD@lc&D$b(Qt5t91`6}3jQnQjmvpWfEwfSBJKGb@K-{kAA~#&{kGWsXs+$J@nNL6V!?zAd}~Ore84oN8W6XfaMRvITDYU0ft0xBO#Cdu)fWC%}S&$`AS}n%OaJmn50>d$}atF%lf|^qYAE)HXayWim%nSwIvtbDB)2%_q>2wN(ozk-pI+r-H<elJ`py7KnutvEMQqs!DH)*h=UngTMvFcBDETwVaJ0(JG0*{Ckrq#M0npy*M4;2qdE%jB?nW#W3D1y-T?4PD7%3_fp(Q>0rjlJyE(~w8K*~yi9SCXrS0+^CxwPLzT9ME(%mBTf6-(z9UxZ8(a=R@F*V}Nx95>0Xk4yy;52uW`%K4gB6^q{x-$F3QR;TEfiO3eZQ$vuykjn%CTh<P+s?@7t8i-!OJq4MdTn5N>Mq@XuPv9;W|L2Y`DBB573cBp=mQ|CogEkqUEGG2(3O?kWfHhs1m3mT+;M2w>qLrGBT+=k)^KVxGEWh6+icc8?B`*g+}E;mb%LD(cS<j{3XgzP^fCjWXRe3h>2BD&T1B$s^nDBiN;<r2bc7Fq0~AEkP^lacMu&0A_>_a(IP=C4-)ESkDS$02Fi+Jz-82Kf3?6SQ$B7BaEL2u3jzE}wUUg7ux=HEH3Ls}c)UJN^By-d5&|`vN>h~?ifwwatvH)mDPyR?tBOG_ZMvr2NW4FdfCpH$DkfF11VM#}k^3Z5%B8%fs=X2s2oM|(QzWiw=}^%rYKn+3(5y^LsB0E=6+7TNU@k8OjDWPExR<3THi}iii7-HZ7G%WncBJ@{I-nV;LIaVvuBU>#h%3u8%l^FH4YRcr9vt`m0Gz5=@VjIBEd@xD>G{hpF`QYmzMec^9O^sHUO#OfYw_x+U2)eq$EUGi>#|6a24TcmaMa(ud@q$MSsx>N{3ro|2q6??|5V4-n9e=o#RsN171*r;It5#FL0{x}t4-fzieSyf9T!GVYMmvxLRecOH=_<f{JLD8BSYeX!my$O^>n&Kqt>0C<T(?a55r<d)7&jzeA~0*0*p?RIy|8gJw1fCU$vGKFMg7H^3fin{r;*oUm$6%qA+rH@IJ;yKa+01QhF$Y9hmGQM2CvpdxD7U->xNG%@*VC>b$F}6BlRj%sQM{1*62Qy0e*88(^k!lbf0e4%YO=?(|S{g&Ny%z0e)T8qxCe&og|>$L1j&0ebS$AeGS8`8RO3*F$IHAtu87UQ%tpjuNWTxNy_mN#Xw2%k=<41V6XNw2qZYL;@N!?&_$oIB;bU-jOKB<DB+H^mWX#(&9vWdY>P*gz7E|{-ji~*L04I@+At{2XA#|n^Q?{#A_y13yT7>a$pM?GGVZ>E<dKD7_fl>0eorU`9f+g)yJ6113DXduGd4h70d+pfzG_g2KAY{0KNf6F9~IFmT;*JXZmHk*tuyC%cv6flyZS@9_gMqve~BXT)kt{lUK70P&nVQ&SnB}Cq%{M;p%tVP{$OqO4<fseD@)5<hV+_rLddrO6dSK39yj;69SWMfgKY`I`V|MjeMaD<sd2oSQz@crX`Y2$nA-3$F`-Kivoui&E-Bp%l0^tz1K<0c<Q~fe5sda9VgPF6HE&*jp#2iDOi>O)r)vE?hTy-%M5Oo)CNE%qb=<|dSjv?=WYGTK7n+6FNWw9_YeTFTR4yc30psC4A+SP0w;TUuEqi$EOcDnRRAv}&gbYw;eed|DP|L1Rxtv^?)rmN@}uGYXDa&g1eaGL9qK$_^s)1Y0O{9(5WJM5rTnCMLEzX{t)pCKG(&Mq<mJ%f+$B&5#VYU;1(Wm0T6lWq(!z#F#VjgKu?>?{%+&OoJP#cT(c=O;eX79iMAJ}*oST)MB*gEN#P(_-`k)S5a{B4>J{tX)DrBTD+BDPR4M;<hXrI^V`{dOc9V!kfV3)Z3d8De58k%mE#``+QWcajlH*u&El`aj=q}gX`)dUH&`UlMb6XrfQ{fwRPP9g?jn!jfoN(F!O-Yn~{DsyFG(Lt2{2oQ6usP<J_a*=9X%|uOhAr?z!_l8bzQKO3=<`rf)?d#2y=O|I6a0VEdi6}<Ek2YUgFKFZxU?8nr10{1|oK7Pvq9vaGix;&yQ~ImpL1U1hi_aKC8=ge1u-r?mqZ9w4RAEq*xtgYbQ4(IZT3OiP<IBALIYi=t-JEXS1dCSdYnddv8F7Cb0Kq%h)tS-4A`Q=i4mInL_r?M>^)Q(5U-l_dwrCT9{JO=vY-$5#9pj*JH@tjoHE>Bg7x-X2R0yO=H0GYKqma57rSvK<RYAmxyEE19=KoUFx6OTxQi&*A=G@i#X~H(B0Ep+S=uy(|C-ncUvx6(uzf7ZgZZno~%dUl30GdI1;Tz<w9e<<QTkKqZSd-T(yjko25WPT^afvVIeq2&8gz^R}$w#f!i)FK#GjrP)3{i=FHu%1CQu0-aj(kUwlR}aOlSU?BhRRs$guw&>n*pvITgesh%n7!n&J8K<xYU`7p}koSDfofDyW;CtOnd0*1Cr~-C6m<Zk)n=;J<)qUk^j$m<PTDFi-`(@Ibj@<6cy-L=~BZ;%v`ewVfokin;hLP5>9OoFlQF?4K2#c{8|xhDCt^LYXZzcr`y0ecdL&{0ufLn40}z-W{Wkg6yO}U93u7)dNA{{Bwksuo!5D&Qw6NCU#LI{!GR_87QA)vE87)xJ&$qBPqANDPdZ?|6#YyC)ygtP*cxEjQ)lo^qL%Y9{S)wpC2T4o5=q;%gyA#>owj41n>ZXmXp!oxI*NUD+ex#xozcvB-5`5(=U(YMx-GmKVE#y?h6E83f-pq+Fx+%SNnPo2;jR131@!4z=q(Dg?|3lKKH0{^eBjfVUN#kg!&5O3Mj#$7;i;qFs=voTn!6Y|VPP2**E_cu37J?6sP-Aaf3#JT&8&D^Bf-cHj$~avJ!qlWK)pxSq{XqC+<d6Ol$peIe#aMHym{1Le_%TyGacVq`kzT2u77QmdO_A0YkoI#EB*?&;AHo$L?}H<<WV;t4?g6+$Fq=f=RO&IQ!V?=WQ|GG5#?XeAbtKDn#4S>3C@U0mNKxWxmW5cNm8Z#+lDd%%Vx1dq=j`Ll7^p7-maL8W^I9O90aQ9pci)dM^k>&HAL;|bfuwI%Mxf&FDXbB0=AsMEVgges}BH%UwPM}dUy6n52*?W+6S2C2*NW`3PiW^9;tx!O~zevf5}<l;dtJ!vRLV_6!+Uo<fVaPt+D6qFbq>zQfUEOQhm7t=eFQN!dZo|wU1zc8Af4SPgH#S4yjQ#H~-WYvilN5Xg1wavRw$zE<8a%1?LpQMLU9_qt|-jEejFPh|yMlK%fm82-RB61kma_gv2ILdd;bXCXEwynbU$D>4O2GdYT>QR2GZVrhU6sK*31&C1>0v)}RXOq2XrCg6d%zT2H*W(bi9EGHry_88dVMdGn2jKGN1MoC%a1YdE8H6g3RHFM>^s0Ee&@cbUv+!$6Msml{^8d?{uO(rRE6C|8vbR-1h2Pz&U}M&1D?n52C7DPcqruwYOOrX3ZfU{+6ZUe@wg+UV|Yc_Jmo{w8l;ef{#yt5e|Z7=+ILq6uet)dwd0C&0T(mnPWcWS=6%iy_ySR`V$4A|4e4WdL+)DMFhEU<^4G{-v}ns#dXCfndoSz06%PwF@Rm^xa8q5_jK(`;h59;4D%Vv2x6Sd%98AS@{wplt<Pj5H?~gP0x23ykXH&1!iFLz3@JIA460BPDQ25k5lkeW=Db3WX}E`Y`>FQk=QbF2n&0DmV2Y?KUF0dT}PE^feKMa9sm(?(<MTVZLH3)o_Hn!=ndjF5~1^;z0_($i-+822QqjMp$&WMBc-R~?!iS7iJvAnABHr@KI4+-f(2e;sbRTpn#<56tO7#*(&$t7dfRu!z}ASRVSnpF%#D!C(grD=7&oQzBJvkmI0<wU;5Xr90oQxa4=w^Nwi;!{1GYqnvsqH5-WwS=D-p6uuhiU@r{-LM!UeK=9<S<~+qn*f$Q1+rDf{MLhq7o|vTW*DD++NPOy=5%He|SYc??4EDbm(QOuDsSc)*|wdj%k>#sdn=?1qmi(iiNT97Oso!se`<tF)DLR#gnB)&3A<`K0%_=RYjdYf=C?iJtl}9+2B(i+_@;dF^WQX)0#%O`;kVYN-E2F_GaG4zfx?`&N0Oo0c1D$I!7vOLfOO?(Z5xl$wF}#_XZobY4{e+5-yF=N7~Tzj_$hW?FtaFc8*oS|cmo>$zoWrD~)*l~O-D8&Af-%3a_;*@PZ2-5B{-df!s<1g;EXlD%d<ubHOkiSzCIwE9}xsrWTFXrZyUhd!ES#xGvnhX;J|V%idXKD(Yjf4)L&$LoUE8jYA9Fk2Z9X|a(E%IR|(AdI|C8DsCqB+QTbFWLAl!Kb^5<?_$sxJ)QcDWrDiee7114j+-qZ5;8eU39Yn?_rB9@&*siQZqI_JQT@c{cUhiEpicem-d3W<3S7U0uU?Ua3*U}_rzMvJf3R)=DRPy`uzLPUOk=b%;!ec)U_O2h$qO1+WeklgGH&h9X!dr^cFDp@~4HWwFGE@1mbX#bgG82LQ}oKad}H9SOu|Hj7cQdCYIf_N(mw@R|t@(nzJa8KsO046`v;7g9~1QX@gCd#%5Q>m;_==Wk0~2GW#VtHakJEA6k<Oh52#DoUSz6SRhhb-k~I`p(6NjG?G$qB-ZCsfn1`B3dga6vKDv@L*Ew<`x?iDwm0IcNx_lHH<hvw*FwA>83Jk!`rgt?h&ukWLrAwDjnUOI{^3MdakEvVde-%kSb(=DEP6mbW3}aDV)sM95JCqZ^h_X!VXuG#un^+`Uk7SEBcG|RHye$b7FTtj%$J`T`M~B@iZ;;G^CC=xNuU!?yO!wK&Dc4NW@l3M`SAE3NKB_oG7SkFPa%vyfAS!)H{_Ais{V97?`cE%qLX{_hsm&nAnuHzJx_j1k+&JJg9l}fTs|y$XfIyeRmFWz&vJqHLmz7V;rwAt?-5RzE_QtvGU}ZNL*lW!O!AgX&6C{X-PJ+Iqa}NBC`94TesoS7II<D^yeBUvK3~0ge51#QDz$K-H%~~CX2|hq(OtEh$}47plpAm{LFa<=2raLAagtjfi$@Je0;({O<m8uGVp?9_thx(`4QD_{ha2P9?fF!$u$@fBdqt^{Je<-H(`v0X93lv0A1aNln7n#oxKmUJfY#Fftr3;kfjEy?!JkG2*V2%CiJz@9McRwqEqyJRr`nFz0DC&Q=ZJ7EV-xe*_q^mkI1qhiy}G$KUI?kjrKj=CYyC9E&p+rh-xNs-IanqSldbiqTk<)}io{CDS2MQqdD+91%V?qApd|A)M6|a$3|=#SqQ#JnAJxK%xmqS@w+4lor=FLQoqc$^US2%R(u%`Zuf8GqnIM!r0j7CoTt`VL@ql!A!(n9r!#d!rH0H~p`~?g;qyKeBoDypO`i5L|_QW$q#s$j?<>`h9ER^GEE*9p!5;T<fotEFyxHkeaCo)j5+1ea`08Cbt7*`MSs1-79?B{j-$3I3=OYGPLUy&9{7^19xVB9rl^nZqJtM^WFM-{TAu)Sr_SjR9KvAre{-Minqf~CACiCIBUJzSTzuIjjDhu-rD&`x=%B^>+x*S!4Z%dcO47_?W%Ne}q>*Wdp3aQL0qG<>FdzW=JE^bLriA3iP7*leoi+~mhQPhe1bYmW@ecOQB4-Rr|u?hQ1LE-osE?{vJ39X+f%a=DTqG(4VQ#_bf4b#}ew%k~Ch(i--(X@=>&d>j1EPOS}(-<JGF`pD03X_Fm_U|xf(F&3Ly-!^DKh!7GZ|JHgkMud>5$*Tzw8k{@E9LaUb>3fJDdK}kb!?L`9`M#D+m-77-j3!a$r~F>W-A~>oKwj7KzPhh#S9o1)J^@bF{L|Nbe@I42wjvL^A<~ub5niC<HJHCQy&=@vF)Tf+pW_9PiNUZP<8}%!0Q4y88B#wOYwv|Q`m9O13f3nzBUUex9MggpV%-tJWJRcKL|BBn*;U<}2!<_~r}aCu<+u_Km=nNF^Hb-ZeDy5A_N>g04V$qrlQzn>xh1Rt3Z$WZ_I~&XT*oFi=A)@vh#o+4oiLKU?JzJA{L=;8{!Mq^zwE)Ogktacjy6YPDs_RrX(_PLyB|swZ+_*=e4;hZ#Z|-YxCXYT#@O@UpYK20Ey_9T$2opf^BxlJ>Z)pmREEvznWqk9hNd``(Y{J4yRux|2t8!qCnpyf_+vvJhdpkt?=j*%rlhhF;jJT5(i`NIxzvb3i(`LSX(3OaL5>M3Z;+NZi+Q;>vupA`0JD)Kubnqgk%!A3z<xDMR7kJp7?rPF&8V$xZ-rweq2)cUy=`3ZWnO0Ed*cd><0htdmF+%l6<r50thgmmxS;~$$tC9XF!R}E1Vk2R{K498)>ZJ!(bjH&ihZl!#*Dz+DYZ3dpu{+kb_8`Il=e4|fri#!z6uO+tGq*}OHS@0dSfB4-0<D*4b08DT0WCDu#^ie9?HsCfa_1DO4(OsJczclqOx)6IP(e~q-&w2EnYfC7z=>g&5aBIy19laTynjb7Y$KunrAPD<t%)exkj_qsXXL{A=Lh{W)eyXcK#igIX631tXSp@>r<~>9iss$szOHYpUr*QN_8E7Hy~X$=3SIBkjv##s-(7_@^?XZE&$bxq@3SNV1k@zeUNX)WH%X=v7GJPUJ+X^r#9<yi1ldo%C842hFK#@WRQ7mcD^r;C$s%n4O~)P_+#A{fH`Zq8-4kl@mltW5t8C7hi#~7#5FwJW3e4qSL}*85XmTql2A!_bD8%m;tv2+OXg9+xfqkLf;QfSol!+x9esYKZF?20)gw*Z7RnglhW!+z!wFe`nR=zKri4R^8L9iWG3^Zj(^ViaNRMvQ{`jmJ%&V9TnWdY;^hr6Kh2z)DV$4txygO*5%6h2NF9%<RxQMCT{Ln%+d@e4KTM7t|+Jt9Bg_}sCu8+DidZ-mjkg?DE`d8d+)RHgUEK~il@Pmp#nv`MI8TvBTm^SS?@=FCJ=+3hWSy25x7#%iZ_mijhGMISB=Yu0Jwba8akK(at>`xPgx%X0s#>Ah<y;K8-7G}|nLN%WRy(oy4VwyyrY=-*VUer@sc;orJ8VCkA_`%6Tts@_|=rmqmyHZqsadn+m*GfHefYQ-}7m9KRBi+NYxbe(yUNs}jC7J3*3pXOPHTAVN(~!z$&C0bLgADNKz!hCQ=R&#S&It2oo&$H%4M&;TQQFhx8gSa4B_iJKGoLFN39KS)2n#A}8yO-+sXit+!S40OYo#H{*{R$BYHlFVpsfeVE737!Z0BKSPUnCNs8WEGe>?Up3u=LxBzbC+<efCFPS<4(DW?}te-+1(^wi0FpuTi;8zizJc`KBg%ETK5rvP$}7qLs!M_6Btpd}otgkW~Op+}+XQEhqX4KH>%GiC5dMl5sWL8eXS^4CDzUDN(VLtndKWEJN$NT2B*AXur%TiUrBl$dA9n_@IEvM?tRWG%6y8WPI*&E%5#Z_f1T>a4C+2aETnXl?aly(!@bP<l}WdG0dF{p>IG^}Xjtwp(Lu6Q#9Hi&Gv#%9sVQP)HLS{G$gILdg)7uxREys?4h90F0fB(fkD9cQ`VQD%e47s*{t^#3Q~%31)Ybsu)M+<2oRv^7=oLfsIK`xnkugA%Vb_sl;>VYh#;WV-np-pLU5$LY49kT~i!K97?QEur{o=dlv$y^3{|ImXDK+6X~&uE=mOs)tOxl?wv8BE9xfmxy*Gg*3@R`XnLkgNuFLSGjg$WW=&loF|T}=Onu6;Wu^&uZxJ%*cv&JuKIp5;#U}=Go&s`T=rTXh4)3|=JMuL18@{PAIateJv{#A6(3BF{kJ1CWkPHKPU1q{{w7n4Rp$8k7nR3(ZrB3Wvoj|SX(gpaR$f$Tt%j}{lSH)*JEIZM_Kc1IJj><N<6dc`!F4=5!OLqaxi$JJ5SJ}VwY|NE=(<Z0y-R1h^wTe?L_Qg6L0E>gTc$$7({@7Ia-PH(rDz;W=ax9Bo9%;FL4gCAoX@iPuhg0E&VI!}1)&c}pI0Q=}Gcz+r>Ry8jF_UCv!lf=ahqnt%BGUH4;>(zC>!cU(mT$&!o(g=r_!M9}Kr7n4R|0n7t=$vC?-#1frV<&xQnFBSfwB%RY?DYwX$c;7_OrMerd8^k=!nPYDjZv$qo!R12%qx$l>2j@cT2EVpV>b@zJg)JeiXEOl*St>X`f9D9UW5kB3p3AKd#ov16_4Q?oM9R<$mI#S9%1FxdZ7=0AsJhwPQf)urCunMZJ~2U6RX|+ch#xP=?V=%(R<?y{({a<<>U#u1-T(Va9E284GpM`{U^kbA37;JlH)dAWmd?^WsCb4m8~dtdb|Cht3lu2J`A6B>`g0I#hCZj#295)M9HYsC9)RN<zj-_Rmf*%e09UtI+3Pk=Yqs>HKw%%Rm#}?_S!klG&Kt&yg6|(@2_QQ^k0n)>Q$aU6j&Y9kwJtPavjEW$falR%<q|YIO%r!xbEF?kqqq-WLM4NTSuZT4zXj(@Smo4GAr;CEFachzbEx%;i_|<OHLlJm5hWXMr?ZFG+hP6S*D4!O^E+yy0D`NKILy687W>o^wLOW+JzWO;k1w#oXIUS<WjyGQh_K0i4&T^33y;f;QY%i!i+<*!h#OKlyC79Jrbd#5^Ib02KZ1!6Er&gC$CSVC$#i5)^PY;oSSht5@G1Ec%=y)FpocQfRCEyY{}M%$1%9>@z+@#|Uul4G=6TWm-LsyC14;y>?SZ+2F^AY(FI3oBcLWRSw8Li#Ki{E1~X>^e!evivwYWF5@>NFYV|xP-d#x6u|&AM@XP}SGXZ0Vk5#t?#aaS4zbHICt>mjxR3jua}RDak<`mKCoNXthUoyIKcHU%6#Pv-`pF43(`CB#;Vxo0KD}wMMER3@`#ewe*t2h@S_O~1m2HIsf!G%4IVfM5b)hdutT(y$)~Vr9rXJ%I`A{}}JhG5ZPs5+pU`fgvLbC5YHYI-cYAIJEWA(@|dKxXAM(13qlD@>^*7>Z=nZtk=C-YvWMv+cc(Y?yvs$g8?Ep!Nnh|`fbqkEC=oLKk5Z5<Bm_s75A8N_vWv9YlJiNCkyPqW#=?f$YOo*!p1C#mTkfL_!yxlVd5zIU7srw6_4gRHy^`zt{|9JTCy9J=c~AV^UzJ2E#G1Dd!2tjmUN02Lqbz2|Kk?yE^#5SNurRw!Eg9vrW8D$y1G4b(wjmNhCY2XyC$TC<{~&ZmwFcK+OE)|$Ijh!g8QLWm!$RjdHYa$TP%kZGfM))l!BN^l1CpYR(d6F)|ztHg7Q)#vG^2M%d1>9xz59#VoMCyF#0DDt{BB?HG~^K$yheRQGoGg_|3R*lJ|nVe!SShG~0cLk~PqLLZ6-Y6D3&7Sx~;`cib{nBjYekEa)t1l$afJEpRhuzj6@+TSdjq{;XO5c&SX`38=N1*tdHJt+>7ep8UR825<xl&1YT{{85<`p|W!)_0Tl#3M5P2Smy0lmc_jV^RkFu4YV27%#_GzOOFb33}YCrWDfayRcAPi(6~PFT#1FAmnzruKhd#q#Mnfq3g}Uuw)`Kg)GR3ToQqa<i?7M&k;F#i}s32YRm~mb;pS5kYV7e9YrB#|g~NaA$@Ybio@Xi|^?ogICqHdXchdZ0mD7q89GQz<sScpIAdavq}O-Luz8$F^=su1z9eq@?Y~;wcY|MrY=;pIltqP5)AD15}p$Yx2!Eg4{Dj>RH8aGwhI_YJiJ}4ufDk(#+d5MtKTXzi)I_457HjSQYDNji&N!Yx_b0Nj`1iasZddk$}mI*hT=ej%9;O3cIYGpqjTd!CI9fcCa4|~JHtPG>qALU3pDhH$rk^qt}Wnkyg=SV8_goo=QzfQ!=7z2P6mgnLs)(Ut!}MRlhclE8`!*rPB(*q9@JOpZbs{MM#<YcSr<d=kS*d38iy(m-gQ@o3i=N1ozeFD<Xh3WXjR=Xzy?^1o$6<m6kY+(F>W*9&b*=0gJMs*j1gLFGaEkN06vm@@}zx7rO-#*v29LjS@J58^5#GjwsvGMu&#e6->Yd5fpZzW<nV8R4BKL@+cOTV-IY#JfLx+lTI}ghm<0{-e^3<z7F<66Vi={OL$?^}-StR=zD7z3)JS6CJYNMEMuLTQBH~`)Yp{kORO`rYY3~&8J(jiV2IQI&Y_yFWxt0`AnzLxF$g14UJe)OSAiAO0KqZNah!TPW0E~q#`ezq+PRw?j&kxp>-qwA^aEfYkj_O)fY!n{HoDV2&tW~w8{o#b+!KxXQXHZgRgZ3ZlI(7w&DXr*ZqE6jp>cAkSZnTk?=>~kx(|ST?5naAVugFftrR_P`T_$iRpL&5%p>Oaw2I6!6`lgs6=j78?QNM!{_>z-CkzM&%Y%?o_3stqG*3C(`oDxXE3RcJpp#`FGd6QNqE?(iG_@;Fsfsx!;w<|ATu#qWD@%m2ychX}}n&gg%04?|sCHh6|wtw5x>0eg>UE}|?tE8PTu3piMlN;>DX;bZ16i(phVf!?E{5#Ia_X<LAYO;sy>aiq6fzYfb&Pt_*e`GAISWqUnx+};4AJJhH!663JbWGaGUP5#&V%o6UWR=oMqH+#E(nz}zvZtO?lAbqhpw2hsHK#t+ljBP)v?;ZGw>NG54%P_+unq{*`@YIeDeqYHK?Z}d0aS4F)1-?83=S8mz{6iW(AX8G8UyH}R8jNLP?QzYxR?t~)oUdd^nPRnL#pHe2W>zo)b8SFmAn_OmzDxw)iWio8GblxC(cZO#+{UHBt_Xmn>kXKULd0|rq~A1M^;rJt;Z8_0H+7ADA1Trgf;WH0*#8MD3^2OyI8EYRp&ehuk>utUCA!3pqTTN(;8gH#0xv)<>hC_l<5YHZBTvqMb5SHEaCbe6|(5PY-qoDc4dj>#~}!>W&d&YA=X2jDYfIq_)PJ?BT|^l`prAOgBGM$6txs}=C8Y{^Tes6OxM|Ibyx0D9V;zYJKrng%X=a=S}{M5${`dO47=Zo;K(*>j_M%FxQZ%^`>KF)7p*CUVB&!OEC=TfUwq-WM=@xzAXdp5K0P|>m<SdTN^)7Sd8k*h=O}as$JIvzDsTy(gnn=%i8#mSV*y+>*Y#WYd9@iSJk9a~j%ykZ=aT~DI4(dn$#a|loy=>}SBIR|;(KH$Q&LV=DwBTJ3o=LAOT-K29f~VK`Q+|y=j=r9^25BnEh4GD8_+RFGtI6Ky1wFZ;p@<xSl|gIf+;CALL9o<8E7DN?Ro@bTk2;%Jgz0X*qg|NTtaczs`byG3lJOG>*+FbI9aTWY{0fiqm#B1%Fx|e@fBoAiJ*H)bh)ym;r=wpy8#R-?WMeS37;#?tsp)77WOEk7d@CVX}_;x6*a;uJJ(p244?m!kT@7Z4K>V@D85-6aE$0sGt@KQ7BUjopNAP1c(4Z5a9hD_0woD>*c3dGh=O9>Uk7gWOlX41JcFkJs>^a`=aXBwU-<pdw&kTF*VvAns4E%UJs(I<MG4Yj9ruJ&!jbTec4?vtW=9jnf$h!1OZ2=b?z|Gg+7RFf>lvRaRyhI-s#qnOgyO<yvvP!Zv%{11XjE2h-BXg7rkp$TK|Csem^}XG1!kyDN?mJWu@zAOKDPaw)$Av8c`t@Od^R)Hp3geNK8}<^S%XVfk7s`~S6#W|F0?nxX{Vp00uQ;&B8QW08*qpv6CbH4X~sI`={HypCN$D%zbgYC(0aJji70BZBl~dpc55?+Y=iuUiFdAW6v@4s1#;baE+%ond&wv=@5hu~xCoU+&>rp5QcjR3+tj6l_qHH#M|NA_Q&wTAq_E^+1$$)}D`i;YNP)B@lfUbuN~Y8ugGyrCNN~o~EhD$w@u9GjI|6)L84J+@Qiq<#v@7GnGGq;Ill;ANbF6X#w<Y$u)U&!OW>^3QBF&!SAB_aB0y=^-s8jLwOLej@lxyh0%qIIetHNk2+7Wp^OmkU7s&(S#s98;Uve8fxHvx#D^f^6-1|OFaW!62*gy{y*K&nb|GL~p6Qeh%S!3n^L?5&xDcRRL+QP`a6&@s>M?tE7I-5C?cw0^2}O~bLIp1*FXq9lvlFL^TY9xpxRz36aXp{>_VOO5Q<#|L7T4aCxfC4=6!{9qaJ(KY4H4SD*e;9S|<YPEOIBiea?BZx-?6G~wSs`?+JVP&Pwt5O~Ofu!-#KPyFcxma?Fg&B3JnJ>okB!TzbM*slCip3^?wRzrm;fW(0&C7_7o)ovu-4zpdBC~ceNG7viNnXwAPcCS@VyZA^h+5iL1sCEf0x5Yc5FlT8v(Lh}9weoVS>bfQnx8_t0cg!tim5Znj@>BJMD`A8EJ9eL7)b~}m10%e-~u8~2B?BG&9GU%EA|&a>ZLE-1x8x5TM&eJGqh4o(<4(P&tYkBDhw|PreIZ3lB>}uL1oJPB#9L=IVGv+M8{bmg*QtrNW7)?G+S@F<YU>j&aBQvz6kj)L}9MUmZoKJhH@1cYsaz>9eg3nTK^)KxT{dZDO?Zm4!J9GLRgavL)W$(_C#cWl?57-qGCbE`PGm#sq`jRY)yJHjBLrU($+Z!PXh>g@7-Q4#*JVJGlQ4irj(}U0y~U^0~FBYk2pw$>zlw15Fd1LUfrMz;M+qnX?D>Gsu-esJTP|%Y%)l6ive6Y>8rJu3hP10)5#ijBfohGq2NX%`OfYuEi5$=*qmo$7arg(@2Z>XG}Yk69kz4%eSUFkkW5KiNDlpE5bH*2g)TD!%6u5yL=>bK>(mGcHSih)f!yYN>1Oj&01OT75leUq3MXoKf|Vh2;EQP-A|XNa9vm^(lK4mrLTxbt>L0yE`ddYwW~q<m5eB_<|F$cA=-HOR_}M@tnz;-qd9V&^Cep#RRXl;e5-CI`Sm2DQ6?~hjeqdecixr|z0uh6LE?6%swD@K5Kr4``HpFerv`VeUjHO^XG|RQ=w#*H4aq)}~@huYl<h*CM&rX-E{cL}%_-b|t#f&-T$iH^F{+j49$^Q!s=L|2edQr~S&_PI12&MD%CFEUSdxMuSUD+WA+}4y@n8B9YAGj@6j95J!fs8R`EEt}!@xz=Vq`57pq{OBA%qq6Jfs~(Pm`R%Xd=iJqRWs6@$>)gXT`n&0P-qj8jIPMk$P+^_SGyXf%uCXg4Qb<}J`dw(Zt2*n6_DtBXu?H7PsBq*YbvJ0h#3(8n10i3ntoFNLUn&|@63fLMA^iEDVgPPNph}R0;6e1fV}y=tQ4}R0b3@KP-WE9cJ*^#laWfcPS%!#=$_#R1!ViJ@kjzqY?%22I<yL#d_CN&(5JWa><dS`%UN2E6Y!88tJ$cN3_8w$UQ>0Zo}cSkfW=6u6r9fFp&7j_lcb(2octtFMfYK;R8)rEwS`@F5nxIp$;=`9xKO6C7|f5e=hhVvv8`?_k=|rMQ~H!Fj&G+&X|gy-vuZ)q5-lTDbFM7u=SF%5t!zrbgfMpE&tBP)GQ~z;Xd;z0vD7wl+N%+m`*|YuucrbvXe=IN0jDj^gtP_hHOjC;DA1RRDl2WTW`V>u*0TC>=zDXD3t+G*!wJHLgzdp``jtqH5cCkVZX(V;BDn1-dt?P2V037=(J@2^F3H=;Ni`$qyuFeP2mpo@$9)(!bX$=D*#N@x?Z<1{;r1w8pu!+x*qR_hY3!tRv&I!ShLyDElD0gUoh^-IT(q?3q9B4YUFpD)RxG3)SP%nDZKhgxdqrWSsT9DlrCPl^A-4J_d!;QO4n4Dk(82m$VWqj3r>7~39!9E=gS<1|gp^THXQye6J|H#aYN1wl0;3sNRD}xd9}?;?{$aN7Gp;-}#~fgP1Zv00mP0nt<9LOA_DX3pN{d1@(DA}&Kwy)ikYl2Q{Vc_&c9@LWYCvM5G>kDWzS)DgfK<5s+=wYiGrlLEKR}4dpD)anSn$y}o@le~y0Vd^;IdM7m?e8eI(GPpgWrV9P-Bo$kjNaW#UmO=?zHD}&ids~|KYi`(8j*qUn3B6j;7ExdwL}_jDduxu5>pq%8^_2kqt|SXm|w@h_0%TpKR~ErAlXgpnn9hz6!LkWM9bSRYuC7%t5AWi=k9)YB(EY*7Lyt@scmiLuMcGyh6bNU+|*lVq*IVyDcxGyN2Ni>~ZhYw@ptH8k`Y+FaHJzwcT?K`-1r;zj&$?RZ!kLl%0`bQq{{wz@MApksrzdLatDJiwR(B<SGY_3@tmFwRlijGFxLtX9c2(IO#q=g9t0QFvv$!S47qj4~6Ao^K_2+ZcDq+)ViSfoDL{h%0_5HtdEGPYbiq96WOpEg_hQlukYhhD_j?bQ7u$Ff9WBg3gWQHNArrxi&#C|XSK#{MUrOPW0wg~<2z@hfKcBu%}il=Og@beX}x5s_}-8V0o5h(l@+$-b}~;G$P&9hI@)QpN(~}F2<6DLQ?ijQJ$$)Vf~%3SV_3c|bjxBd>ex_UK(da80y+)XsfM(LGoQeQY<rZisWQxjON&f93=NOmQ)i4(v5-<Gww1Pzj^|6iFVJahWqa8X8aTtOWDee!(ubw9MQfj|X6QTXRzHN}oip3ArgC#n1@-N+ujJvQ_g*PQT35?;pI{oEL+ef6cGG@RhF8P`mXl~4o3}#i*IfmtL7GvHG7FAj*`L}b+Y2kgf*3#dcu^6DDTe92Bd^%0Hc3XZIe!T77Cq9CNirMYm#Bu`R!@{};ML~4&6--Z@J9geN^sabX&&Qth24TWrPVvIjUoINf)W`Sg_v>CoIX`xwNYoWal*XBl#B$V>Sg%|1z0a$%Ct?*ZuJwYsEEE)(-(yEuvdC<GRBa4NmMGgLgc9(jhDfSgdS3R(e0GW<Vu=t&wq9A%Ecn_m2|pu`oca*vst?k`?m_b<MI}`Syo&tG3zxgVZlK(?5t#M8D-i*M8QQBi6r}Nya656HndIrT=G_=5*Ljhg9X+!@2i_kwk~cX0z%e1PL4Caxekk<Ou`}Kra0z}>xUV6Dxdy~mytOG7=+PvSaAl)hM!PB8aE*!PDvGHNpXB?63BT27X~^GU%mRqD1eZ_?)v7-giR%kl6DD9C?$NDC$g@{Y?H9XU<TbAd??;%CYUZeZb1#dd%*_BAIWV=3Q`zZhvhLRq6lT?OM0|GnAVe**n{AAB*n`>z-9nZVinxc82h0TIa7w@LcPS6mUXj(QpAhWQyf4gz6)}wbJ6wa=+ez`{oZMSCUc7s*O=hNikhZZXwBtI$PY`bY)pww!B<*Lg2+s%aNmpCoYr+pggPGFLR+b#CAxQeDSPb}GBp#ROly0_r}MPydY_x9*Y=;3gW>F*ey#Ih)Dd{5U9T_40_1KC*iO^EL|nPK9GHOF>`~r*|La#wqvGiUk}bj&HPqCXnq7{BRr)L<)tpmMAEed_lZVWm->H^W$4`!0IALmw#Tu!sn5X4YS>Fk(t_5XMZ&MZ-eHixTvcAlp6`-e*7BoAb!5oujp(`GR9P5~9INuvOZXPLBUB-mB{g_bHXrNRxDDU9KvglST@w{!M2uyTV-ytg=yhZS<0bDm9E2{rg_1*Sdw;x-nbdS}w<)3kKD7>8@s^k?(oabSEWqvz@fGWsQn|mv5JESB-@DkEJ7;lrKx!I$?P2|V(0l(GF4one3kfLzk*1;6tHk8DwawvF1JkyAj)G>cQ0uM4-NOytGn00I3rNPIFwlIJXsUm8hL|V{wI{ICtdn^g=E-q4StuYWB@JBJm0YA#uDhG38TPwRa5th?a6;NWWW$w)MSYvBGK`6^l;u*hR0WT~=9B%vIu5CMma4bbdJ_?1Q>Mx1bm&saTU7Pi+V8Gx;U^J=-QAz(Y%CvfTi+E&6p{L70LQp6@Sm*TW773KkB9#f%;G@xF%W@=at7K)w%R_m{^f0kqw*KODUw@}GBh=I$OZ1q|>q!jZWUzJYRyK{Y`Mj8FM#Y5#vB)U5y8fvs&ou#9QFjKhEP`E(NY+KecRnCH8B@ulBRi@G#(2MiXZ|k(yjfC%cFR)CUeR+{V0N42V!MiP&HzSH3P~xMKud0DFAS{7pkE~HmlOgzF57hqOT?d(H967FFE}W6Z%u`26Ku_6VNyU=re%mRLGRwSjDPIrSI0npzQPNPpnyj9&^k&IDrtX!CquAGU2BM^KzZ?7^H40`vt8eXIdZ}gP6BPDRMK8~f`_<8ZFX+bjn)KjZm~6Bnnik>^qm4hl>3hZ)sn0_Cv!0!4$DyoY#ao+ftD}J%#HiPtd6%a1CeQQ+6@lJYLT}#8<<lztMIBxToID7at5O5Q*eU=^MLl>S`A_}S`f(&?FjUD3XwmJ2BAD8m8rA~xWw+PsloVy=0<z7Xxc0ur@eM#K%;O5)m~fmy{hyFZtg15^>jcDi6ud$PQkAF3Q!RdPt&;f1@+6So>t5N{%CDE9<Jv1(Do`lnq8whm8i;4U4Abm8TF$~wudqR*(zs&O>IEm<6yw2p)f?W&n`NUFjK_8e|Xy@2#swr^WClhxB-)I%l2J^C#eoIqp<?w^eNZ8U%s$yu?3Cz{BScf$O`Hckho@(172+0DOtDeVw7aualBSlyQJ2X5>Ddr7_?F%*1>Q!hBN8iykI$D*)FGWO(vDfIvLD-<i7t*F~hcno+=hqf_LJnLwe<Y8B{90*9mieF1oHoaLN0ce2WuHJl=$F3Sws|NQD{xtr_U;N?jz}6x>V0BKJ87T5Gdw>%JP1?E8Fk@+l+i8)2dY7+y)rWuk$kuc5q))mT38zErYsR+^~n6bA7}E#{z!BP|L&<FoZRqK5-fWqR;=*0`YHrLi0Y)1$KS(@LK%PM<0iuDF0Fcc)uzSzvZP(!@P20FxZ?-qa+gq)P5J7oqb^rmmTJ3yc!5xy;kFVjmo(PtIifmEuh1gs4fCl@^ges3HG|_JVT4c`n#4e$Rx=3bhlWH5+xGa>}PqFl*0zzm8MUE~1#Aq{Qq5X!JfCcGQaQe+~mPLMTW<kh_9=JPYa0GxQ<FK2|-_QY9?jGVDud<~?yJnp$xLa{@TPInj&^6M;cl?zE%^WRL=W^WB$Ueg6Gtubwu4&z}DAA4|sz89Pwecku>S;G%Y`>{J6G5Q)zz_q|r`q&+KCaTc=fI&yP%PYW%`b~!b<0sZ>AamnPDbmD+fRnrj?G6kzkX2t?VqP@42Z*D}EGdS&`HCIqrre@9Qx);C-q8Rin+v#d%rRnl$#Pr|<sqJ5^Of3D%S4x28!Xf)wU6}S@U_?Dr{Gu<Y<b-F66dO=;$(2#=X^e+q7%^_Pl%dF|u%-xo>D4oOEKBKF>PD9O<F+(Y(wyaI&x6^-)`(i!XmTh9W~1Qi<gBPGZ$)kL6KM7P`SZ%X*<080V7qJX5@>HYJ;Pkn<MBaKam8f4y7J@B)Zpfk@g02FK2JBEc0m%PI-UBD-<(YR7b##-;aH#V@{A@SZQS_7Z2lz=&a3nnu6VzUvsecE<VNBT=ck1$CNACFLkXC7a6K+ZPx&0)Tpy%3T8);6LOA58zMS0SqR;3Sl8X2<l)b|#{6JNmtdeq3h=(eTxmYqoTRI|;ykNiz-hyttu5Vp356h)^a7J~=&AL9wY+h{=!P8G&2NzQrQWZFPRkSwIX!!xYC>9)~AL>su{bsG{bi?I=Y9g|Bki~-;@TUt2Cwe?J18uv1A3kM@i3~`&K@qwN53IVY!t^4ZAF{|$8z}-;GYk2Ph1zLG0h2*lKc0pNmuVMhtV>?U<CT1Z6AsN0I2c+eXT+ut*QIObzR164_ey(#W6-;Jh}w>0R%}Xyop_63yBc_tOaL9+lLWPU=L*<qVKPE-p>rwkDeEK&j<b#5E*F$TQHxrC0C7kXwfw#pIhgkVFWyo}`|)b1$CcbV`ija6$bMj){adiv-OG1FOmWD(Ag?c*MAe><(<9sx0fBe_<SK}i#70)8%I}FCFTeTn>z5y%<JED}gLMA&x4%6ceiw-#PiiTfl&0|E>o&Nr<n(VNel@+n1yU?Ya1RCdYD#QsgdmRv?sqr(=DSp^Vfh*QPnJt|vV*)I*F<b&_6Y<G#($|0zT$|JhX#)rKYd~bJ<d?dM!ocz_{KH)W0M;{n{0lVtku$`H7g6RqckKH&q^i>Zh6C||7P5%L%*%5{<k~=ibi0pb(S~!t}`BU>=m2u$Dc23fN3G5Gy1d;MW~6PA91Y*X-p?U%@D-+{*aSvg1QINId6<_DL?~@4JfimrTxk!b;V@Z!&Rc=UoZ6Qg-j=j_uQdwB2aDme)7$%-?OD$M{1D1+8X$_8bt}*>ZQ>;(_ib|>(Qvb`d#QIj>EoO^m|7na0y=3YBQ+Ga#>|xB+X@#1C!K`k0B54h_0$0W&34#s!nm6v2D|}#Bca+5|t3VxA*{Q0cM3yHfb3up;N_+eB=Y<*Khmv+uGk24!YqeV#vnt8ou5;tE^W7xY!Xt_DZO)EbkjxRZ#^G<$Bb1fT0SDrr_*Ky6Q?;7>J5!YeB_Ch`rN~|D?9jVa6q?Ju2<8mycShaRM8jXyU?<p#rJNw)}~BSV04{!>!_U78E7#Y-U#?Lf^ZoEZ&@kbzLb_Bml8ECN}ontjk%5;5zwD<7g*I=hzq`W<giFP&O>XFXYsB+gZT&?XOVQFCH`7e$=pc-vruFkKvkN)T$VUD_Pq9{-qR5BBP1IZ4eJtZc*8YzauhddQ%`p33)Mr)TQDQwE=Eb6B$>T7cX1oI#>zJCvm|efMgX%qRFDCZRatO9$R=y5Er*zp$#cIiq5s?gxzv+>ZXD3G9#$RyD=A__r$v18hM9^Yn`aGaaEKw4Y?G9-y31tkksKy0dFh~c<qE&grlz-2%pJ+U%mY1^Jl+C#lO4@@hIYBz`;fOD5!WVz!(N$feh#e(M~zHVyD$Cnlq?4LzsJkve!+pGG?S59zwjfQ-TNau@cZ35Z1*M0X`#d+bHRTNCkJlLZEeLm8)q+$)xjvnTj(iVw4sr_&UJ`6s{@R=_|5DW$<_x*&Ve1RJ8Ac4XxM1jGig$lzFHbzAUZz3SqtB<PBl>3qf3IWW`g?R5_kr=eE`)YKr!szr4`*M4=LZ!jA<08I}-Fb|w@0^r>3<5+y#e2?PW>z~8WUvd@~k77jD$_OL&EXm6qxRZhAbACuk<DFQ6&MJ0cebindh+PS4Mv}5N=@h$bP#Y$k{Lj&2S-W%Gz7@+2YdeOFN)^KSCLs<i96}zFlQq~W+*!kz}berrznE%>v0lRA!7NU^u<;F-)y*%<g4BX%(SYf?y7tDV;9S4&EzedAa;nK#@R!Vnbr<r_auHxUxbx=(rZwSj9uR1M!Wn)E_)UyVq^iy5Nc|Jl+lS03rI7vWi9Van@!dDf^(0R3JT1@6@K0_8C)TDa1n#RdE=%+L%)>D-5pQN1>qbap$FJ1Lxb|X6Wz(pQDd%D;5qTRUB$4J^o-G^v4O38wuMFw^QtE&t#!U->cbjV)|j$a&}zvKddyZ8L{Gk`W%H&{)y1UxVZNDLVMs7u<=(ec~VeMw1Dvc*Zswql&Y^&e>;{F?Gft(H+y$oI=dE^!;&L?aP{_H&%^lya-r6dagr7sK(^zY1VRBxSBTSyCzy&~q=F>!IJOR3sEfCPhv`8z<66nT*lyZLhY6G4(X7vYp-;W^%4B!(D5icv>wtxi_!Ae);AVQ9zl^6~R0t^(*x7xp!!RKjtZC#5Hi4M_Eofgku(c!QySEXh{XG6|akEe;B)gWkONmHWKgz`RK}9?R3P1?wjH&KK<L%5*pi>6A%+*9!Cus^x?)zh>V{Zk@&@$?zRM(I*nXf1-uqCeM-?rO3!3!GTv)qWixs-sn8@B;vAKOuxjF!sd|Mwxl#i5GhDL5Z-d~=&6Tsk7Xz4X{S=UveocWG-LmZU+g`Q0Bx)J<4UmQa<PYprP>LY}>HbaINb0w;wxh;O;PYOP(j=g>i&|TBPzAeI03tRp9MmG=Fd#-_I^HyTxr*R`X*pQ_wQma<C$MQINJ|YwvAIwIV_uk1yjX^T-5P_M;>vtm_CZ7bQTJ{^3r$9IaUGrtB`OxxG}}Lh7Rc7#jH9JaEq@5Wzb54UxT;N`X0_wjOaFRlmwA1i5?3|5nfVIbjmvFVlYm7UKiyF&9dr3*>8)r&aG_@b#NoPSqa~KZvJg)hAGL@t=SJs!!IlG>qa9Li|KvvUBr6soU^65M)IsFUoUa=iLt)So0`0z3FEQe<W7(UWHv2%rt`?x4z0O-#^o?3><sCX?+;0VOev9V^NF#Y)4z(W8EeBh1n;VN3_A>K2fU7DgNi8U=dWi4RqiE|om}Jc`oJ=lf`sK06EKXjsJMmp^4{OOUnVsg2Q$=ne03YaNw?5Z%Sy5Y+<HCXfCNe;aiTTB=SKl7u#GKn4!%2Jp)@QB(41=w`qiA#@W!bJIG^<Hd1JBfceT}clsrqe96~353k*Q&eNrh7^+Y07L5A1W20j$j0o!RXVW(9k<%zT?*RIwvsEn`3yW2uY`w~KGgheDGHnH`t1`soy!zUc~771Ck)3c;_=$3z=DENPKDYK7V4LSyAa)ZowkqUFQY)B1h0XgM7W7}Hn~z@}Zx)Q>833S4^(Pr%wL(WadXPM*%R*<!>;6ODLhpjJ^Z#bCDvPDVgpgY8EuIc`O)!Xi7u3pxp~sE(-6vlxf^ju+=Jn1|rq;%0aJTS7YGLsKf774)asJdX56Pvs7(uVgu9O$r3yRM6zunniG@&25w$PeVu{5yjx?T&`beDDg<e7chs!SAvDW8bdwsQ??@#@zkRZYh81`+Rh0=L^QG1OVXHh68e+S)fuB>tEIi{b<4VQjt5G3Pi-!97(9gqs}0#`=yT`Q$ssV`6`EjC3J~gvl6s3HCsw*O3~8dZ;BSG09dd?oaZOUfF&354O(<y3p_-$GHEQ}3u=!gD8C43{)k1q*KcBtIr9{tRA@?bb0|_F_h(5$6X^P-Kt)Ryw4=7<gJrY&LiIxWxBRKyMH=WMvTs{K5)u<tx>2g7v)5UJnXoDc4yv$Y))YS+9X_b;NyD?@sYu%Y{saq#p^n4_Y0=d*Mt@HtfmA_0i+Jsizhi<@qMV^UC9&JqIWnMi@@TJRzNIA;|5SS*|K~&fs2OXLrC}laO{L=8W^llFjoAVkW)N>VV(S}GZ>W>S#Cmu~&*Uy~`dOg>%9<I9Bczbkw$aoBmZPLc1A?kZp0B9I;h_{n&Z#Tg0n8K)hG_d=u@&;z_nD&_9SxzlTjBb8{x<%kjfhbl7G=2`bcVu)3aj^I@VE$w-c3MNQLNAEArgGe_!3&Wc99GY73Za&t1AvRE_%hx<xmO7}@Ec-grn(BeW0**wV<4-}mo(?(#Am^VdL~i;z<um<xwo}*=15ehvuM}fV{T|Ce8F7Me+5*3E}OU&EZ17E1-|DJqdUj#=8YF=9+g;}_VDBJy1*qFM;Yg+QOW}10uU;4Fc)Sxllis7e*$qTgS^}h{QE(43lO?o=+m;$Yt9?ry|N$|t?UEfe2}0Exi`{M1+Qgs7RjBNG@E6R%z>CEaNsV{9D2AGA~UM_9#U3T{`p9LixNVTAsAti5DE)}B~#D9rW^oeS9%RZ6oc;6a0z1s;21y$>0scZtL5ofb2GF>q3mq}KuZ`c_9f>4i#)?^mW~Hj^E7EJ^pewmOj8<K4jLhtr;DZd*ErLuN9K!Ws+I0tVDBL6TS#6H1uXu+G`BqT{s{m{8E0T)X*14ztJ*`p^Kff5QW~UM1@({{ED5&#=@tQ}hMx0}^%}0Xx_G^u6dxdW>^JN^!T}tM0}Ip<Rw4Jds^VGI1x25-bQ&7r2PGA9t^?T4ik$c+#m8#7bUPWe;>I<7^sJs7gsl#_{iEf>M!81L;%VI)>tu>SFbfkJ!X|Y+6H5a!wzWSN&hG}?II|tPT%-zuDNP>`Bru=%f%+}C1;HP7OIN(z$5AfX)*9g1<t?7Hi0`h2d>~VYkHtiRy7qtzVX9M~a>r4O94fHEXquU{#ZExpa-KPw+nP~)Bh-ae&Xod&13GDxR!OYC91l4Rzd$P1mgAW*vhBu`GulQZg)9Lqws}z$Y_(WoWG!`S>I`lokX2V_Q@mrD^BJArPSfssBMOp6v4(5i-bO3#hZQQXgcD;5H3A^4LMrW)&25boGabx@MY|+<yhwx+22ai+Hdh&DVIA%13G?Jj0CPfbyv1CJ7&H@$<vSgi$IGYe8PSs;I46;b+*f9*P01P}99tf5V!7QTOE^E6O*5l*2G;Y%mOqs|jypo6Mc6uCcLfj}Quo5<8>g?FF%3Pz85*!p9)jrw7LH-kAyNR4Bguq0v{)ih0QVpn5-U7R+7T8hl4(~IsT73U1)di)V}V#Ma{SzC%GS7H5swx*V~lK51<$tQ5s|AZo8<bR3tNa!1}DjGF#Q*bE8Gl|N@4V4#(J=D3n!K8)qp{o3F>>+-L`IxwUF4=x|md(V@Qj=hWLMs6KTgn<B7)It6+)Ho(pOsxl)=CW<GV8#Iz$h9;|lmMrT$r3U_rl=yMf~J)o`M=4}U#0NrOQ>Bo&b+Bju=k#eS%7Y174S}{6OqCwr(c+vx{c1fDTa^<~fjwU3#y=g^=cXqQN&t0kHPF8!aH&Bt~p*C5j|IEy4auUi2-<~3|@%(*NI=XK=MbyJ3@39(3dGp-@nQZGuiw-p(=lTDs9fxq>>&-=xuK-U`Q?zLLSj$N$2`vM*QM$5dL>`HzP+JE+L1)jrj1|6pt^hU7H}Lc+NctA6X2Fy>;|3`33jV0R3_zkGaH#2|?hQBkSirWX48cS!-R8oLF?pOL*(8910%_Rk-5i{s7cePj`m3@$=_dZjaLrI5THdeoSA)*j{vA)hIehVjr^d4M?!cbr`<`%#S8=0)8|jwOXOqAU5EWA3lF8JZ(!#h=x;T@Sl<p_%JMeq<0d9R@1s6oB>ZLLOJ@bAwKbP&db}k>B8V6-tA$TsM-N?|DH$LL)1Y`D-t<`yoBZg*0X#Nq~O20}~LCF~U$l(nCeoUCJxlgINK`ZQ#1J7lo@(j<ex$azz-}x%0LOP2D&v^V<_rwTEkveK;IvX4PGNp0=ex(w1s2IU%HQNz{KZHF@Wh2r~8O|;tsT7;{mcbcoqG*y*s%=6nFlg2mSmVD+D~Y1+G3)EB?dtQ;=^+V)yfBFqM&pFheq&DAGsGtN=;X(jsulo}W}vt(!n=nlY2q9=**j&^zT0*LP@#|6`CVS*qyo!KN2mn6v(@o=*KH!F9bLQ;P%ZRA0A%-(PwF|-uwaFbTC5N)-x(DkxLLX*?zSc<IaR=(>|l?&vP!ewj2}!Q-D2UtyM+Qi8N0pU4n)=l<53+fJ(+!c4`ZRKTeKH`OwelgX@FLn6q?$Re=!@gEUb!vRy!AuIOeL#;gPKT)|us&)8ncdaD+{2tf>lPrcu?km2Ev%QtP%^+YTiqDPBz}e~MdrE#?(gK>nLB%^J`cbz-Sa&5b**I9p@*=n36+XiFZ7WT1S7SSI|g*16F`89@gXi#1pe)(FYzxbxX+qacG7sz`O%)H``%Y29LnNFt=fcW6lkV@553PpZN}6-Kg(dk*wXG9uPJ*sW0@vKOL%=ByLfjjA%{h2=e)SjF~Oo+}M(@b%kA;VprsO;l527&IBB^6AC;qR0={gr-|9b$_tSjCZM|3M{edsVz*PvPhT;mB?NrAfIB&c!vahYDK-x!;PehL6o(L{7Sf{qi+&hd}0!=LcgR0bN(VE_>dMkWd3}oAA$K?ds<>R?rs=L`1i{C1ubq9Z+Vjw>Ir4uzHQyIb8uK~U(AHq*p{4|rF9`D=CjHmxeOYelykSga+^Bbrb<uR<7WCI*-WFx)n*Ab?XJ?r1|LD0PFX)_IhOTpLofh@cmr$O?c5;4y5w1QVv5Et;Zk=%>4urA4$l~P-pvL!Cp@hP!9i$aw~>LdERZ`|JRbWd3+b^pCB^_p@@~0YC_n$2iW*J}n?N1m=M=$&^9^fAC?`sKB|_$}d#v?^Y+D`AteF_a!;<0y{k?1xAZEW^Sbi8RVNG4Vc}&EY)frNd%|PfCc$S#^RwVl>oInngb5dZkZEF$Q0j5jLNdRCXR04_mxfB?6V8&-;M6Gp?Y6Y&FWMyZBlZ8UQt$ib@Sb%Jem_$#4anILvHv1&g(d#SVZgr?t2GON@&46s%iv?R<%ww~NhR_w>8d<!MXAc5!4hqgsZ#cb{V^UoZ6tA1yeBc0BKne3@iBoHlc`4DAr{A2a7k8<8QQ*P6a8PR|#)X8X0w<CCm(j|9^(}HY%owe8OKQ>?{aViAFCy1y^YGshMcRzRil)fWW?uz@C?aHXj=-`jKH5gn6?5o_$y***1{d_4ZQh(O813ohi9(L(iDqoxRgeJ8Sn<7ryQV6^Afje2lBeNo7?uO8w|G#PiZ2qX8S9(Hbg&8{&1)GuHv1XnIQ}`7M_2&$V6&!#EGN|@O3?CraNLZ2gflkPEj`-G$h0s`Sb065QOtoO-({w+&DEfwCCippP$4@7Q_7k0Y_h?>8Ezr3>KthDk#)p+PAW|qU>PuupE_+pP+)Y&R7(TdtZl7GaLf4F!10EU*+fOuwY?DSc66{m|MH7uzArc*bpt;~FB81$gh)df&8Zs8SlvEfhYA4p!Q6bBeeBXK+4e_+S<SBQs)$*~`JUPIwYX>kpJrg)QxDZnyiQKiTojl#(_Y|)lOhxTs)2q$`iS_wNwD>W5#h`L|9MK4U@m}%9d(h&ELZ)f`?nP%xYJ#KNa(kT+^q_$)eJrkShP<!crC=}sfF+ESK84q!02I#7j4JmMcXd3NZ>^@$Y(f>mV4-K*YW!>CLkCCy8Et=X~m5=?$Mys!JCb8psZ;)1~49i%FrqpjUt=G5np*UX{E{=E4(yz1z3b<WELd3%0WCwEASi`LLn(J3<zU=mT}OV`b$W<)#Q|L3QYFsX-8w3!;|##`%D0dXF%@*UbnP6OS=_oU&V$mY1+5K@Qt32HKjesT#p`;Ovkq@^cA?2;Al~>x!R=avMNgUqQ&@8(?+xq>7~vfrS<KbO3H)SByu?t(z8Z2e_fUNRIw^9c0AJprg6$F70xJ#ap3LtOw#;lL$yGGIhg85mF|^-{>M5_&FFKb)@y40h<-YHIy9tYP!xqCj^>Xud#^D`suU(#9QtzLhs-)ck>eIxTr%)R?4^CFO&%PaWYRH{XyXxY0j=p#`)K}RHwo2gU&T9Pi=;g;wD;^tHcQqXS?DTe4)wPCisiRQzvNnkr~R+uN&>!WiYq;2jmFOhsxGZkS91E^cs(em0ya_yz-1x3T-+Z#*V{EWM)5q;hj$gUCpnqKy0{~0tRQ(B?X8s7;)5qD-^4-FlEWe0g+5Q9fK54l-s@Rdi9B&$O2R3hRhU$Bq?2#>HoFG<fHm1rT0do%J#Nx3zxnd(m+$xY&t4t<b_--ljw4@^>K5Fv&L_j=E*Ep5xkM7$8Ph%WOpbi6*?J+IqpKh$ITfS|zD_ichQ^j-TD+rZeI!H3oe@Q6ga>xA%T+E#-0T8zrA<R%G&TZ)R_brQ`|_*LzkhezZ@zndDAF{j8%)(Gl{Yh<(%ttPN9`u1Nf;?qB-JSp6rArTrQEORq+}4iu0{A|DqEwQ1Upz=NfzC=){0&pJw$)C(Stc-Bv08T1!6~5F+yUkS&5Ssrdg9&^7>3~_L8yTY=Ab_+0SIEBfrLRs7vgxO2TasCQ=G)&=fY@zcQ9w{Q?3;MAm|L%Z@wTX^XlWN@&^*gMWUBIMA+z0~HaXKyWJh!_^qfmWPPje08YHu`r(^(fx%wLL)<xCJ&6sR3Si8A2n6Qh7Z?}ATp7J0j5Q+;0)T$7(zI}KBLqSj`<H<F2{+HR|6L!Ux?|Ov;nc`A*K5UIi!-8N5h>5SF%%WmDe0|X7XV?Wp>TjS`GIzPI7RZ1B65vJs8$Dkx>N~*>bDj4xA;1gK%-$^R0vwA!_Y!1!){{#@m{4{-IN8=ol(3xb|H2os(i4M1f)p)+Abr5ViH#wFREW8thXVKbkh@P|1W4CQTlwlR?r38a91Jrter;tn8whjnyKJj~K`#%O>nL+hzb@nK``T)-mFSI=xH;nCD%Pc&DW5rrG;7&BG{`4XI2^?IM6#5ubZO!Ru|atR6#fkVK!vC9H~TXeF|{gnlCY#O$ta(mf`as}_PI50E1{vsr&3Gi@h#Hs-|W3U7lq_Yk||cB#_-&jl`RM^cCQcWUVUc|=g#=$qA45%#xn(&5d2AzIxlJGv|xOpoSMytg%RGUe!4Yz$Yec)8n@4jhle!}UY8m754zt|k8=+|LRnK%fEf)SKUj4M0dN$UZhf3`CcfBv%nh*meRhIqII9q1lStRiJ4wWi+eFG*ioy__1sm;u{DcH7P>M#B6nhb+9y-xw-f8ka`p|8}Eus71Pit8r54q#0pxd(>4;*pNPNG3JoeD*qagTc32BkGP=Idl{P7D1r>OvEiD?i0UM0B!cj-bj+kC;gQH&TmwycBCGH#Ql93E&lIR?6!IkcGB6;)Va=jKqn*gQ=dp<vt9?o4FUJjco)Yom&_0sG5{PNq0iGnKw{owJsPC}`GXETL4L{GK+>?R$rbAVy@)^Ae{z5Gk0I71&#8xDIk5=B%HVh)~8Zs~-WGSzU7cY91#ql0WMeDpXJ_X#fa*RH0tt<jLmYD#NWw(qX3j+7`<<ZL8EkZ6TphhuDJ^{Od+<JhGLlvIgmi>!CkrvbR=WwraLK$vDEyOmu_^$MV*P#e<_;SfSHiRU-dE}=m{S=huD`=DrDMQR2IAj{R$gFugksh}Ja2@=Pwn-~T65w&lDK?FI8yNs>r9#8&(BJNU|Waly5TygSl{B29%7?VoDq&kO!Q@C($)oK?+j1EB*0D`iFyLygMb?*UJoDKoL1=($o0%5QLC&wK%I!7e3mLq#2Wj<ogSxx3`H$xk)>L|~t)62^eyAb1@LY#ed=8$rj6a}oBFECr($&(IorA1z7LQ;-w;5PH92rOodO+G8Ac3(2x7k}H^3n@(R%?3+iQGU(|;+czHyI?_UZ=NIRhd1G>9G$$ppr4yYkcb-q;|kiA0Y}5DG*v4mh!@ayC<OH2jew<dFv8?i)NfU%+QX;csg}2ijbapyY**V51Zlq>IAX{})1%CG3F(~RTq$t55eP1NXr6yWJ$K4@Wr33J%*szs3kH^PL413Z*^=YcyUK2+A=$ywXm9s!8sjWS4YzICEgBU6y!;dn$V%(fO1O=)QjQWbGK=H3J))3_%8QAzZLqCLgXDg44Jis_G1?LYZz)l}1!Lg~Q=r&LdC%I;;h3Lw8G)KyCNgMKWjpC+YW1xVk9K=SvoqNQhI^KI7M&yAG)|EzbHA$BE5@Kwu%?u;4FE(xZg$rl9Bt<<S97E^rNzE27=Eqx!9p{AykDZuW3?9Juq^NoGMX19-9{=!zabfc^Q0M;On1iWH4QqtgujwmqwQPi>g4wn1b9U(6%6EEXzAY5goTpbkH1(Z{T`bnAG4u5DR}*e`#{0#`_P+omuU8GZi|vDRDwTgm4h5AcsRn4&Uj-vQ(6+TBe$qf!-?X8wqe`+5e=E9dhc4$tvc->+b};eiqiIqXw!aB>za=#ZSW`i&`=3A+F4628>)f-vemn!r$8YsX~QEk#iXRvkrR|>ONe6;oW`zq7*@Y4IQ{talR`1R?`@ywx>*t{Kz=Yue8^#JYRixY*!!l2zS^Wk_T-%zqEfGHfo;}O`&j)DN$Gk;_oVMo9JB_DqpU^W*03hPl~BkRn!5z(t0nm{nN39XG412H#2`$$)A1r`!gVY@r?R&r`7CRM(%qi(rTy-^UcWLMTNeO#Nhq2_a%c{o2H@!q3B|&DApdA5IWwp0(xQgjchTE-(Wq+iE76AIKn)!ebILAA+NTv%MpVBjd8}Gdntlb^bpkLxnZHM?hnQ};%@~lz%iQ#o#TB^+{eZ#-T31Ys2(Ckq@8j4%8vRaAXB-4uq)MY)2#fThuV)vxcEB*E_!iv{7j@3cc&n3H1otp2<Gs+7uX}XlyUrKeCIHt9<J_&$xKl?w<wGm%6+HPhZdMnG9?U;6cMz(#BbX(_k=jhrjqJ4d?FOS+17WRCK<;}_jRw}^T$>~W-gn#W+89??Zplj;1=IzeF6reayrk~^s%#~V;?X;ya9a&$K=C~u6{n7@V>Wmghk`oC4$uF3`a2rh@dq!3m%NC|1dnp7877WcS9#u+GAE=46L>TYl_`)n+c1@qr3P!#wnRnQSA331{*tDMwQ6Oh>5Ka%^qM3=$Wtl_$92XSo7A%=jxp)^sqdE3x!pHcB!_?+<ttMNh&Wua303Rf4Hb$@;LRrKO-S{@W`b=09iSP<+O(Oo6N4KNEHQ;w9FeC=L}-8%KBo^%Pj5${PwE3N`9sx<SA~ip#rjbCy-FM)Q|Dy=7a2av?I43#rDPszLRT1VayBm^8S@BdN&XNid**qB;FycjE+$A(?J>Kqi5=1W`ExvI{$D^{HU>jHJ%Jdvit=!zVj$(*Nt(DBJ!%2+EntRios&O@OBI#NB#6fiL9P$hxyafpn`)Ds-zWpSktkOXj9Oq_51(v@V40qE?dCuMd&O?FK|C)P=MvIbN6XH`CO)pgwjivc;V5m}0S;bRx}Pv*w{Dy9>EkWcDJ!-fV3&L7+hTaFUbZ~8<b-5o!69J|0kxO_7^MJJx*droO_O3}+h=nQMCBnQ2TQXIGqp`ic{FwAt*VXY{e<eoMjm%bfw9Vh=rmo0sT;s$BxWZxJeXfn4@?>2R7p^1nbis;g3=V5&rId0J1u3gmH`n4p>8XlCPf|M;}FK%vFuDyM2vm<1dH@3{|i9FWQjmTxIXAz-!Q+E8^Bt1q^F0&`w$PE;1ysMF+xHwtm<}Y(l1?bNI0936UV}#ZK5gVU*0K*k*$5IQExgm+lpNX*|~)qmj}>VV(;wf1>_42z6w-9&p%jfxfx8B;cJ#0R^CN-bX1IE7B{p1Dt0haW+v%zn?PNd5q9r&JPJ)q3qGbzS8C&TCtq10Cy@H_+)T+}A%@L7O1C&ls3hk;TsBrM>**Bv-RoDMfA`rNwcJOwH*VJTJZ`Eyu+G1jCI%O6_63ymJV0%??H7?XTNqU09DpOFF&c?RR2!J4qVg|l&dr~>6kO&S^-TJTkVDwB9oI&fR0j%C;gP8p=IrM8h+?bTx2>ckj+?1$#mKq3jZ?|~^Y#O#jw2<a3U^6B91c(F;D-0wEzM|aLU{+H+r-u`&+ssCvrfQP)Q)r86m>X|j!K<qM|N9~s~E*d@S;v}4kM$Rph~QkGBnz>2dWa+gtS?O+k50niK1nJ`Fb<|pw2YGD+kee7JJf-+a8WRXk(cj47FoVrW!$Lma9cA3I1>%k&daiBgL%lGbbN0kML`?ZL+O=F;ph(Rph9*_ZsB|XYL;|c@^Ec{a7SBx6!?c?VkoX=CVaS%$c&e+JR78?=iEA;lr#6LFL}Q#(soPrKPc)3z~YwtHe4^w9>G{XVM#Rl4xR{Rl2N6bGNsC6`4EOG4DGf(sTYWp@*FSviri#f^9qg(7V%kCWSk#<1O&(POE;}F*pG(t_Bxvh6z87=?vWHU%Ksry8!0wBjmH)uH&Kkx)KeP3(Rb*!R|bNm$_S0slnn*i85_$=v{6j)swsE254wR#7&|wfJY`wm<!oMd?69(AZmabySsZ^CEzgd$eNJxhU4QjrzB&VTciazCE4p%Q4EuyceEjpsxr$%7RRYGpqZ+yrB?%C&+M_{U0Oq%L7dc3+pJY7th{#1Ju$SheFb~(h5ge4E^utgIvB-HAD6%0L|H0;ZN-EZ9HQBT8(hwUwIabnl{jm!Aa}U_Wy?AQB`|^1E8b*jcbCl_T%N^mhX8}=-y}KI%SUB&hj=_nZtIhB*-!J<$I49YGPpyX)6`XW3&QZt^THEYCUhV!IXAwBo9}D{jFL(BN~+L6?rkyn>;Qdu+c^O8<KS{>YRWy!ck%~u3eHo#sd8*!Zd*^!at7SC{@Gi4mdOQ5>>hS>o!^Li20M4Gf*SsGn`;RhWyv>9S<M_EO(;x8S3!xp5;DTY$2uQ`dQX<hQ_Hg&e15*oqcmC+QAge<Q`(MolUa#c=DJlhj6G>%Q0|A8#+RBXznZwA#gh5a$E$8@ENYoQmr4<Mae$bB^fhpNEpk0w*{wF;IAcCY$!M<}NEKo#RaAZ%(JEcr3<kXT^L{B47;AT8n<wi#opx$3PV{29LP{(alB{%V8vZ@3Qbo<S>GBuLuXKklzUy9`4?kn8r)I&R8zsi0N->WeXXJ(-7YSEa-GHfkXFLRe{$dOhe-mwW$o-cx98?2Liq78Sq-ia$da}1h9_UG|VECP)0|)#g`pIB4hw1+GTCaY;pyc1lhc_>ro%`wfQyn`W%JHA6h6c^NzQ9w=GRh<=i4W!@DEM`dPdf+<vd)S!9#6&RJNWLRKiZmyc7|a%SaTYMJ$S(Po7uZxvj<`wdE}!@qQj~3`5Xa`&!4a3Q@s4<%dcO4c&=B+iEGaJ*Wdp3aQGdXv8QtX;|DO!;`DF)SMRUv{lX+IK4j`KPlkRa)^6zs2}b?qyDz``{QGwwd-L6r2fzF$+p61FVm&tvf_Jv~Cv-pO3$a^W1$G2B-{p2<+2J%R;@zBxe~<5*QbfZt+qQ}jY($p#E7~px-qrHTo}ZIco(y+aA$dC8z#bR6b7LTzb$pA^V#^ymy7U@GQecXEzQZ#`YYUf9q+IPpkWY}-rD(F-t<=->naQZHG87_R2DHgSLt|vn={GaFQp@YN7O@!uzhfiI0!xALC`@}FpH<SmR)fG2FXd#YqpoG;a*Zp2B))d3LS6l1UW=;{cs=|QKB)Cb&~|DTZWqGGrh-=GxJD8-t6eDK*m8T>ibycGw+`E4x`8<Ps1lOc;!7<NqmDfAvd{T~1t1Xz0>3WQOI5Ej{Q6bwYCusmsByWR=0y=s?ixVda!LAXY~InhpmAKszV9_(;-3)lOFTTb@HIYhC4S3dNPAzh7}DOCWVFPO|0NAZ&{e*~+A#-O-EV5!uP+3Bbe(Ao<DVeWMGB{}M%9fk;?5?lq7A*~Qkw+ncCSPq;383>m%}JJ69={@HE~_X3%Mr<VnRiR=!l3E<EvZyRPmr^+R7<kpmv4sduznrmXMucsMJe$9VlJ{6YK(<;Nug!SRzgOd<%3DkfOwrzWkvsfyWZu-gRY~#EkXY54I_kB|)(}M_%ef>ck~grog9piB)jNCwhTTGIad8W5kx_dnrhCot&=_C3eC9FG?&N<tu{_dCfvlFfNpAhIz#|+9{zsZ*(m^xEVb9&j5;Em7uN5adzUjmHCm`{Ygvkm8%fa<T9A6y%2|%xjNJ#r58rt^<y~a0y>!MUBIlrb@GH55LPeYy&tQH6oK_J!oGcbrRvo+3uGp$zgZV$UkP3udV#;<_;CovNNDiag%~M-)jD}VumN05hD48T^s(}Y*FYcFg^X@*Ps>ufY$U*fOLN3$_YuhIh#d>5!A=!F&JWX9-5@PZ@BF!VV{`uJ&GU8dE@KT7F5&dTma&ImHV2oFCaKu~Gl#z()fzY6r`~)qiRJ))pm8)$tC-Qu6RBdyvE2fiUq`f-`++=oXF{E}aS_=0=_zb8f{e@;2p~_@oUfD7vCL~#HpE7<atW3iP~?4)0a3r*ZL0H;#k`L!dM+b!`u6>J6_NKF-@Co(^Ccf(el~o10egD0JA9DcnS6&|3~-!kixz!ca^M)9ZXYoTC|8(!4N|qt0Bq)IcxbdtEf&AiH}Uu$*zaaxV!x?{_`aB!bcd!<O$KpbwUPjkMr$jEy~9H=_yTrg#v*?91JWCFR(AVg(D)g5*Bf@mFd>!-;XVpfilY-7(gv9hTZ3OCQ}|-DX?}o<NOTC5!Ldg6=mmx6w5~xZ8zzLjEj-;?ZOJ0>z0oK?BH$Uzhj2Q8J~H3peh5|fX~(--R327(ucocs?Wo9CA-0=)o801vh3mr|4+X2!Taqa~=(R=T8X#xL^r`0eGe=hKj8j{`Um660bize{n&igpHY@79F*Zc<!Lxhp_Pg|wf~9rZ%03yE>=iRE+0_=E;g}3T`LHuyvzmp`%_z>o{N>xN{KoVXf$?Jd?8;ph=uCyybY?n>G<8)b6#ikA5*<~EUZ-}KOCFFUgZPrQT3dBu0YR7CX^C?Z(j8xCx}(RRq-z{SUTi+iiDhxSXZuQL^KkqRXnN8ZSRx$}UMkWDsNyH4@r>bO+p7&Ra~q~py#{}ud&u7;)8XM-THaR*?9*spYLr?){66t`-(VzuTdOn^9c}ul^+>hXNaoOWdZyc;x0|LpgYek%H2`avSqiN0qsxMEQ7AB(=fx31Rm7)bqna#uw$l*7@4-5(HH=JZTAV9QrszsX<%L_lacVZ5uLx2eL8q{x4^n3%Lx3K92?&g+-Jc)){N*v9jz3gNF5NqeSGCJ<`9$gpm-+36wb&S3R7c??HJjF=8f1EU%<4SQAhkGmK?=0TgBt7`OS7s|j`hy^JekW{O9vwpQqOOhZ-Jn1VLU!d7@F0s<I=K`c{)`j=NOeor?$iscERbsQf~#LY&Lw@ylWn`Bd&i*mXWN;pk7=ng90V4p;=R!O0|N2j|$}Uy)koxE@zy3Lom?GVTA%2vyg#gzQw>b*mJKRgH*>Gjj?8aT=viqbt_!#4W6K6>zi17U3h~XGy3Fa<_>yyNtX>_z$~pFx0Kb$8x@{@eX;&9>sJiZk252b)LebRrk)VcbOW}KYjK25VdH#1o(}lRI3KK0J||<b$wS87@Q!gJLBPu)pJtU1ytZn|^C~JwHLs-H$-3FSo>FZkTG3db6hj9OnH$x1`y%4l#?thto@bOS1XO}^yV~u@*4?m}PDt9UXQl$0nS1d?t}$YCm<JN6ES(O}=OEW;W;Ky^U%@AW1~_DF4{T`%6b4XyByX(5JcAmvS;qBfBlJrzTCGgKT;d&z9;Y?HS(Nz2t5@G1((o~7X+8cO9yDQP<BJ^f&NsVPa@TL}1?2nXLxJ#_rg*GXhY-~EZ(Eh_ScGHjG@up0eOve~k}_e8qU{zNW~z*HZ(B+H^c-F@7AZ$A!}4wsP_nG#2S{yvOri5azr=+`aKy1USaZIto_>)n2bPMk@RdWpJW$KM+~CHEG1UY_dAaa{%E4upG%T5fMrk6OGs|_rSevNQ=s6ejH!`9&jr$L0k7m^ROftqw285~S>*~JBc#oOPa&Zh+KV&7dzVryVS1pMx;}ps;D<@iyE90|Qfw2inn6Qp^sCgojwPmb)5C|qV!f{mtXwMwf49Kc)tRY8(Lkad+Za)ORtgy`4eP(uXj~BUwdCFeJHD9k<Y-K_<=qgd!ks&Ug6PMY|#vmq2f@Qaw_;=ySRO|A?!BwI88vS{W&WVC>U+!6S{XX_eO+^@R-|OUa{(}@J&^di9n7a|=#PcgVkr4{oE33-g`y71vt15SQkeRh8Ou{AJ6;YVYDikK7<7t024#_$cL&gyxa=tN!g_=QmF=YgUK%Sh0Yb-N&oLjmc#<D*y+2_F>mjH=4homG<7uZLIMsY3mP+*#aY9K6{H7aC2MLC`oY7R<}Q~(Z{Y@U_yl2r=kKTkRRK8*_M2BxVCDw+viM>%CR38oOrgSS;6S&_a(FHLfC$~uAktdUj8l9&J`&7icRUqRC;X7My3c6vTDWVd;rB#%cg(VTR&=Z3AOelH`sTl9VzMuXFJ#_aa9<6JBhV7s*EM(N8kBr;`qhc-A%Ulb#tjBfz<jW~nlHr=N(5egvfUT`N4qXVtcW%86d*~Z66G#wQuv@OsfWCsOJ;dKri^ydL=#3~HcJGzG96;)+r1?7+6Ud4cUbW2o&iik2jQe$_ClxWES)F}MipzGpoWdGj_1$jSl(fFMXh+W^sbz2b^t?AA%V%+&xL7TSxFGFC40E1XQ2RVIoO&cb2Uy?rUmL?`hD19?|?;(8X0AV>jKqRl450Tv^UD7ef1^ub9Jzm9C6&(ymB}!o*@&!b+a6+_r`luHp*eX*IeT*Yo@Q~{nyVV<e(1F~M8E9!3*SmmN%ND0DOm@ua1Za7Vk@aM13`nqiP0*iBb~UC|SKmUpi4Gz-l-R~dPVnlx^{5@zD00ORwqS<(cT5jYFcyM9!^rQt;oCuC5&q_xt?(R1n>IA56O%({I-ZKI%kIoaRtlVylI$6a2WiQ98JqPc!E`9ONCU}f%XcgVEUktqLnFa#XhE$lhY>1(c~uIBu~)mL^OrEb++uePN-j|-+VrB^Rq$UTFTmkzsV8lqJvWj*vL3R)0LAuNd=1cR^@$-BLf2G1AQhR3DUG185-?%_zCbcU5NOTSr}s(NUGh~{O&>&8OC}=`9KmOEW}nt(eA}o^ei%7W32U`CcfxH!K?`;?sDvC$nc1H&sV0-pvEhIG*u9JE*30N|ow9Z)7Y8BFQVZez<Q>el2=QFa=?DeDJ_Ok1GOX%JCrGIA$_YP?&V~XLh*F=a;vdDlN~gqheoce4^}S}4(Xb9gq-Aio5LTdb*$5%ynV^szJ<=LFcsiFcPB0fD%5q;5YF!NtvBBdsfqaa6$?Ngp$jz4>WYM2?-ZJ?fZ9^*l*?ge{ki>019?wJc$E<?M=|yT9;9WP=qK_BY@E0qYh)i~d2yLRARbt2rb)}aWyoTo({AY_^HZ&C<*C27@Z&`l@$@m-}**;$dMX;2rrbbxH(z}dWc;JFNM!k^-$7ZKk!zI*jzjRA95S2UtNbpCPweg~;>Vg0jz-rz1ib4zO1*z%L<UFi%$RLz_vL-2|r2PVz;GXPoA#KbBPo#BAG!7l5-0*#78fZ`|QGvBZ!yO+lTPsaqtL?MekXmJ2mokPZ<qDzYs*@1~xDsFTN6Mn7mu)czB%WCviiGFF6k#$-q*+hv{IcM~n+V&A<Wt2ijHla7*V9&D;Ayu76PU8iM?)cO<l5s<6i@Fu)>oi6sWzQ45J2NgXWNxp$34<ZIz%vVMq3$NwJeG*bt8I=W`>)<HK$HOvopo$16d7Q9P(}`{*cVk*3rw}6+9=Hn>aUwGgWpvcpg2+v}=pH^|DKP4ez+W65Mf-F#pAMNK~PY+kVr;=It2&DvN|UuvOwJO%%krfFdX+uc}&;cRCS_5_}?FnG3u@__HJZNI;-YNj0YUjC8_f-3B2&UGr>6L_sm?Xvb^6@5JkrT`>l@<kTpF(D#x-5>{7K@ujYJ*;GYwEG7ydkeF=A($8T9K_5w=xUe$bpVAv&6L)581*`5&6Gy1~Zt$vW<IU>*B2!66(a{hkcX_!OCp579+jW0%>-4kme*d<toS@33&H#JZg6i;CSP&K1=yKurL9$+k+c5Uyy$6zBN)y-8z5xWxwG)XLysDOCJ4EyxEa-D^p_anXvfJZtTTrlA=DV&5?R<ZjG~kKN8cv;}P<i;`ixel?6l_d5f&!vmPKG$IjQE>^WA4QI3|c4pk4GoMv}kO&$VQQhf?Wx@N0Ly3xDA1Iv1w-U<wL+4*bg!suDM)ct{-ajv;9J0n<tyT7Y)>ACX-<R#xVn@;ySvx^hv=vA!*MVI2eq>o*5@3<Ge43Fewv3Bs7@E9)evu04%VWdO-?Vo6}_qdLM-R;xkjkU!1KpPttxF0KlGq>o${sEvYH@p$%JH!AT+LJ@dIXvnW0*ZhKn}m<~<;kjI%f=DndG1nQi+y@8Nw1kVOgX!t7{hj;s2K-Z3hvL}|0V(csi@?Go4S2&dCtRm$_z3L*pD$}H#t?=wTEKjY6w=F9PB`hr9OmEjJbT2_o0lW2qxd^K#)#9XePQ&#3dFR6t`ZlmnWNfQ<+M0q!k&$O?OTuHzJMliG+FMhRV(#9(OZUb@r3}9UD*SNsJ7wqHBG7zz&R_>=_Hb|*L6B?0?1qm%y|ss2gHb(uYLYUEtu4rr%RqC>SORyE-eHH@H;JkRE=;jLsszOlw??}&+l#W2&auYTDzIHVeegp~a%_>gY_=5)p9Y27;z^P*x2aN9FjaE92<r&9-NH{HG}g^e#Ayr4!BtMw>3u!0^!ryG77eW3MX{XQ09|ZWFv_-V6rP`VJk<XL@HchZ5D}Sqm~@vsHz=k!Ep}ACq75K|o8bg1VJd`wivXJ|3e6DOm*2G}(l%i`E^69k$>4~MDLE7P8Wp@$aenR!Ep(Yj4Bs{_mDDGjj4Y}K1<*7?9Pw=J3ut6q0$|&b^MgA*6%u62+zhQ>Bb%q@!8uoDMQH<+RT@Zx$(~uIh1*dsbND_f2fwyc#O;?QGR#e6mSAS!P(kLvuYb_jNJS<!4bUH4<|vI(JLE1XK8UgoG*w0jx`L3<a~y)<C!8h*M{mTF<VZcwpG{pK+TiK%!?`AL93!D5DBB7tmLb8fyG4SM`}1LuU4G}3JVVK2r@wr<pXZ9U$^g!eFfV?d^eLCPu8MXoUxt-DE)!<tRE8AGwUB6z-Auo84?x(Gk_qM16}<yB7q6-NY}qS;Sa-~wm2svSD|ZHyKkX7%1DgK&C|ns;<N@h5-#|)5+t!I~xr}OnWXeAQx)wb+gkD!cY;rYaOEm$oW;$QK$l_~J{ocHcHG$wLGbh3+jFZOO?dqsc1JWq4sJdSuaGy3uKg@^8OCm;0=+m|{Peq27Xaz}a-nb^ftjSufDmMw5I9)p%imwpa*aErmbYgV(8-h32fl<nJTJP3LIja>8he7gkCNE5LY_BlET_SyRs~i59iZij8@_1jXS}6->F6t5$Fr~vrsK0R!j7BgNJnUg!>7WTz(LDhelRbY&kSGBrP*RPLno_u>$r>`>I&pWMU$8(ip$8?i&DDgHCNwE|Iy~98bc>3qugB4=nhamMEXk`5Gs&^_flbPc0z$pe6g(L_1}o}A5zV0YY}Q2>T9Nk#u64rVN_X1Gyw-B(Lm}7iU)#EBM5rV77Yd5Zkfpl>0;%=6?cY|cMaazJJk)DYYO0zEtO!kjgUQk7_OCT`dl=!pL5dOGYSJBQlS~&!!MPyFvxXWY`m<(@oU{Rh8rN?Dv8`RGmtAVM>JfEz((*47QrYXrh9C<Js1+(C`u=?rU&4i^P#%t6kR`6T71B`Yi}b82v(tVVyU9`4*jw!=tP8)(%u?FTS;6tH1fNn^rohP%Iv)uagSErO;C6m$@pC)_&+80zMZrk!bCGTE{MVOSGPQTS{J~6m!G>u0P6^W#7JYTSi<`z&T#!*VNMe|81?`i0w<+f(yA{zI^@>~0j99P?F&o6VRL-}O6ekgL-qq*;PfpVgOc#6x#56vG%#Tat>M=sVEOv$O<MyZ|0pXHiyux&)r|B=%Y$pI5I=yVlP7PEnsO9UmoVuGOv(-?+t53q++iGXDB#A>)RJ0)L%+Pv)Rdl%Fcfi@FOKdU&x1xjmeCYS9ZM#8}(<F<&0&VB7M=v|2KAm^l0lHOQ=XDBju`U2lv57>cpSl3I)NjJp)5PppbNa{fH;|HYz{Gsx<0NUk!V?e%gzVcWRO_c7`TWZ-WHBm7y?RprO_^?K-*reAUm*kWWK4)czirV5%10F#O!thf?jNE`@vK_wTCg)tWG$(aV%wdr7<#{z4meco?jS;0n~+!AMY-gV*xNJe<a$bq8^6bShBgS4toSuytYrJJPDjxc1f%#7E?0z!0KFK&sg$u|v?+77BnJ(Y0~-+M0X8X$7=M+--r`_`+b2SAmd6q0MwP_%d^x3BgKMBS%}!fwiEZ_iN(ZTyeiB%duGY1fjpPZ!{fu&sq)#JSvV^Y!+5_OjRTVq@T4{FFb36g<QU>a4&BT*%;>{9p=)O~44APHnHz21QP908UPa*Ciuf!!qCUZf`-Q&&zyVcaV?0Zq}pLPgl5uS3ne0qkIdT}%ecL1S?Lhhmz<rNslpl+0g@hkSW27BwMp=YY+3_}yjOIBCirw*erk{C5!W9Wrcgm0{y5-{cJF}WTV4GSzEPpZo-xy@6e7jlKN9s!o>9Y(C7&_I~3=73kp)(TKkQ?uL{3CXu&aJ1L|tF5anrM2eG#<gN9NhcCW7BhDFq1Ex3FK)zp;^OCZ<#hQ_rS{ZtdOpJPYpG<WO)3gaHSa_nHLeL6NC~*Y3&p6Eq=<Z_>4Ue9)|)m1gZ4m4?7!Od(STFggJuaXwcCWOZ`f~5^LN&hRme`@27}ZNFlk-TuRPP{7K2u>){a#fB;Iz}YF9Sh?JT4Bq(#q<C+#5=w@CXf_wEcaTQKI|U7%HSecSB4pAmsmxtIXvj<EmEXWF5m<PRo-a|l6EYd(!Qn%M5%JrAC4N2qy50owp1Luf6+JBk<Y!n+O!IzC&r7Gy{XhXOeKExtwxRh2qL!_(065{1^tDoZ!(kB6`AuZ6GuwRT@V^wG3^h44zaW~}P-$slP&RtvyLvcF!O2q_t@#P;!NWDz_fK7*nsQ)`&6YeN)lvWOwo{RA80VA8C_#R2@r!Lb&CNpgizV6I@qy&yN0Z3Dhq6Bo%P^f~W;b-Rh*<O@D|Y+KbOZ_pNN_psjp`oLFYS)n0rp)E@0Q6Q;CMnRd#AgnTVazr#+CHF-2I*tcd?vMxUt|-82+CW0FQQ4BpfYUb5k{fp~A(nWi)3M4+G^c|4?b}v6Arq6;R44ToJR`O=x8yoJRDOqhW3uH^p#gffmN4WycL)iV0%r&@DF{dUX#2JTfpLlm6E+6R@jL*do{Q&%J8efzpPj);qM?tiv6W78!ab1oU$b%rdrPj|*4~|S8agvr)}|}2eOgpBwNc0g?q2smrq5Xd;bq0l!~i$;u7Plo0B*6`oe_~REi*K$P5Bg~2`D~_iBM7>iPMJS8<MQjZod!v-)(G7JcVt~|J&eZhI`$F*EvY-?XK3<zwhSCohGNN$h^~kk(d_OKV#+p2wN#TTf>TMr4kx74U5@hmupnfurI5gp|;hY1D(<Xky^Qe&v9B>Wg%^w%LXGo(YjFZua|GnlQ^_HJQY|)%GyGSsMfA#bt4h2du`%d(k~VvzJ!iy%LD9b0=2X(v=f3Fuh`5*bMl@^T)$?#rNysfe|J{_FEgqF2u7Si2Fi4>n#Y!EAa!;G<yuKH>E)xRk)6NH({FP$QZeaV-rP}WG0{}iR27<L740+AKInzUBAzXtid&prIrhj%Z&j%%!sA3^%r*Tiiw-32P;o%z(${?*J>CZn=OgFSucc7(ZHBoxQ4bOZ<fL)akxY9EwXzwm=SszVf=G=UmVO6EDcx!^Rs=btHHmb^DRODt-i`W`^vOe0#!*%VF9r0*ClFDb^Z`6M{erjdcw%TDcz-V@c**I~_qv<~I_5E<o9rRp6L$!%L}9@)Bg}C&62E<1Tf&dhX9?WWK1DdI4|L6&EpHq2uu5GrCZA-MgXwjed7mCV3=kixW&?0H;6~@;Nn#X8BO2XkTV7UbR&?i4GLS_A<FVD5<Ti1npcT95VbNuP%`ZKS0A}%tVlciKh^=~$avXSR-||a3mJl?ZNqSr&8ocA&CPy^6PK1s`OAr?3n#6YvTZb(xD=6|2W5rl+Dhtf=+!Qt22_M!ZnKiZ5Q)O~nOf3UMG&?P1&}7<Fe7wl&RCRT8VVZq|>kx3BOj5-IZU?YJp;6Q<3N48x%3=YeNgrKowJjDS7o(%Z7W|-42Fq&|YIcSm${n9(V<83FTf=R-)+w>DLWRpEFm{!vI=50vTq%o%QW|doiqLza(@mcKs{-{ZLyy}ntb8xwY@!lVRO^r`#)%bOg~a0{O<4!duEfuwOcc!#;HvQih3G(}`}y^kNPq(SI8(U40id(b>NK8R%4e&kMEGCvLvCH}YG~N~Fw{$sm_A*S*EmdUI<gO8S^})>z7CO<dZ8+wKG>z@I#8JO8+>xK?`voZ>0d!`p$xB%sh~rGRUTNfBAw_M`vf0LxTq>C4JtP@mXujaRXWN^rtq%iv}EQsXVPR_Lq4$&u_V8=>q89G<Ef<5BaQtSB1qo`m$D%*Bz`6q%(xhBIpC%A1K$5pF7ordOfM0~MbBa-kdgPaF+4(O37AS2BZe=FBpf+aN?n?sLYQejT}7^0Q~@uUz0jD~S)gX2PMzStrq1~hI;J`4nwv-#){uFF886**`dCx>*Is9=srh*Dc#~!73+t^U)D(m^n0O$WE~Wj5cc3-!OmnXtV4TWv7S;GmaSIBA4nUi1#dEPM&|cy-E##_z6L)wD)$)!XhP#}=$z8>Og-8_=1w<YCG`p)gdPVvIOkbiQ=*-6eVKAg{_cJq=J{AFIiN0)KB-(Cw0g2du90<(eHr2AppKp+%`HPunM{d-Gb3|x47K7O<qSZR!gg6w??6F0>j1IR-|FQ`xN-mYl`~t5F=B&E5-0IU9XqaXo4LzGfifrY-sy3W-D;t3QbEvDlFPKB*=0j^qoK#G@AhG0P(vw!ZMxDjZ?bKsiB5ys3fhgv!rSC)m0Bvf%65K7^8r{i-sEBp<0uDNJgKZjZymhgki+X28Slp*5>Nk>{H(AlS{RXI}7d^Da(~3SImW<Y)0wfz|6O#fBdFq4&e=p-v%Z{>Fi{~%(J%#Cix|ByOTf0vNjAxS6@rSVK@+Nl1eceorG7&VDaS|aJ&l{0kIV<1Ef|plMz{Cqz#KF^FgGh;(TKJL7-cPxdtyjmoNsd-wBh|>KxR-^G4dYmGaTkvpX}1j)y#aI9(u2e6BUxpsP)s+GKoIns?wT1P4{A;CG)6^qdZ^13sq-F^ssG<!t64A}AD;l(X*BRQ>%q*j@qxe_J|K1_7a!VvLr4eLlE|Vq-VV8C_jZN5oxrhF^@7F23R>!VH>Gg_SaMHfo711{b0jN%PSJi+IVURnxb~?_iI@Rj(YAA<50G}hSRLx?9+^iEpuB!A5eaaq)b>J{iKTY2fRn{|;rtu4jacZaSpt_8<`Oh^bR`Md1}wVGq%8NanAL4!Vl-UrTTua-8OBLNpodo7m)UKSP7lfVVpu{)J)XCG`q|vk5dj-Er386cg7HQLhAk}xMRyrn$NX5lbbmCM8%ogG!x>-}_k8lp5BIq3?+SP`aMAumcs<4^QXtIkTYIv+(~~py%qjET9D|;7)c0OHbgTD~10Qn3D0s6vr|h_RSIE&RMge7`aw3?=`JTL4)aq3rTjTJ;l>;ydxc)xl*+({?*<_QNh(3Be?Kh~5;+v%v;ezH{r3fZ4iQ9)A-Qe-~EYxaumA~f^<?6uQlu@KDLELAOWK^}?ov;p}Jr(@dw5u3A?$ug2x3RBqxBI1vnT-d^q{Q*Zgcu2nh}d1Sg5=o23WpgJ<e}_FDsLv>LEZjdZP0Xa>Va@60G1*NT6fJ9Y}jb_JfuaH85H;kQg)<?2EkIpt*a7cn-_RR)M_?k_p4UBZUH$_EILPcEaM)hhqu@C-Q$3akb7f(g&0g|*a7e)U34CTx>NENDji;6ZF@xHTv?V)b2n`+(;ieVOM-itxR_)d3sbA-K15YLZ!5Yff`4nW)UOX;z4`{Z#nZIFlQ(2Ns}i=a>&eU^ys`K`$ZxVe)TJ$!)m}w2S6@UfT9+F->11oA>(O8>&!^_r<@0y+@z6PsL~C75eXG>@^kADI*cZuqMR|au3^k!lt?%|Qeo+eRCHI}#gM<E9P2$wtHWss@V!y`cycm|Mv#e?!HyQMzJPKv@7F8l+ifva;vG|<Kz?LwCOz}N#{JB-A`e|xqj5d!J!@44vtrlmEv)a{EO}nEVjaa`6uO-`cH)1vL&QIcQ*Twx%v0#5K*bl+hwVqxI+?Tu3ACbF<h<t8$tNU`nvzk?hB!IZkh!mS|usg%P_~gKm($Q+6B{OB^Y4<pmp2Rk6)cki#k;t&$qHT9o>(^>~PlI8T)T(s`mXiMQL+(pEb{;%)9H`;zs8}jl<W;hI%!YF?mP;GfB=ZMv)S}z7+cxXv({9mP_J5hnvZL=UxQLR1$a4`}O8R{3?VKN)JfM|$ux&9t?(1BXqkwuB$`Y!5nc`)`MGIL=fmvO5^+{(9baR#E0;HYKXj7R^eZh!!QI4ZJ)dR1cwT4bx_kuEvF%}(ye9Y4`@yGIZT)8H7ZCyYW)x*Mlf!*aC+LwEG4TNH|tr;Q3wH3w4-9%iMxd^QtvXr9qJ3jKxLuy$&PsZvdr$q(~q_ATkmHRNP7@m)hT;n}PfQLWd1qP^)1Ho;^2Sf=%rgSe4MSXwtUGKKwoj%rau7Q25*u|+XwTpGk-u4azcF*GhPUaAQ*r(Z^923I0DQfF!NkICh_baM77kxh^d}Mp>Fe0jWj)L|ZJ@J)u5do;WrdU><=Lh=z$VtT<o^`iv*w!^;grnqm45^dxco>#Z^IFT%)Gs1|{hD`c>Oolo?+xoi<F$6*W+6#i=l4y!pm6eLJ<}Q^Kt4#kwIWT;*32_Feb<p0oQ=d5`!y-*lF(x#o*bKSbb8g3u!?SJ$XGd;b<(m=H*NzY2coLQZopLZjCMko)<eey1XOlUp?smLMZMJ|{-%32P|1<qCd<z0mcnwf3z0vB-FGMnapP6*;bM6jRGC4(eE!wr4?J<+86wE1=i7tqV+U-T28_a`Xc~SK|B3w7;}4t(@&Y_ol%m-hnR!UR5bc6iYGMKwpK{0#6cYw7`u5$Oe)yvw|MJ7TKl!g`KmPl(zuRn{Ki_V551X53fBEr;KRo-pXJ7yDm%seWkN^2MU;Xeu{`AA||M;h8kN@)hpMLo1-`;)xZu|8AfBv6;{L_!m{%(8!;{I=MZ=U_>$9Mn#`yYS*{U87Hr}tlbf4kfL?eppH|NY<p_|uO+y}R3o&2IYw{@eFI{qTo(-}&tIAOG;fPk-|dKm6r~KmYNkKmPA$laK!S#~<E(#k)WL^S}J@-~arf%=hy3*N4~Ne*g8$*Z**MU+Vetv%~kFy*|AB`ulHx`|5q=`X67u{^t8{-@JPLz8w0Sm;Z2h|JLK*{qD<u`lpwtzX|{P^mp$D@b^Fd@9+Qc<M03Vho2rF_Ql=p?YmL=&wu$p?{59~fBHXv^QZs#>Dl{9aT(zK^V{<PAO7-gYJ7EfKOflLa$H|*@BVfd#`X5$#qC2fuAAHYyW4v{us{6y5C8G!zxnNd{I7TKm=9|h#c#iU_3F)UzdU6BKO5!QSpM$t=KIfH{`~>Ho5eVT;eB}6-tXD)?zRuR%kch>fBotI`<MUtVLrOI%h7#!u?4es`)+(U+2}ssJUrae(fzj{{?Fh3uYdjVfBwr~e*EdrfBErWfBOFmErXqefiMWaices++OqVj7f)(59!=BOVn`qjgqjfL-E9$eXJ-H64d(mP?l&y$UT&B=nr`pz<?ZqQp?ZCOGB<Y;*wtIb=5Fk5y4c+L%!gw4>(8p*aIbT&_0|=|wNGkwes+^j)LIs$a~E4(we?qfweR}0&1|a8|MqJ7-;Y}qK63SZ5u;FF&a!l;zW*(<TGvCZ->2uu&*^b8ZisUNH-lJ~3PgT+AVC4M*bk)a1OWEqF^!9(rDLq?2WCkCwoCxC4gzrkWQYM3J6;|NDiKG)hNesyrZPdY%Gg(Esw@Ly&1*qxC1Neuu$BqKS|-R^8CwfYtz|&0&v!!Kn2BishGSrcU0~!DQ#J~D>JpGzge#B-q-qk8<r1l76Dj*ZE=G|UP7#U~&7zn9abs%e@ql5-10*SkJsGB|%*8f-MO9426ObVZ)G!1}dYH2tkW>sHSsli=;-VhTm({lGckOYwX+M@tTMb8|@nDe;ugKMM(=VHP*H(*dHykd!n;(7wM-V<a"


def _decode_payload(blob):
    if not blob:
        return {"routes": [], "meta": [], "shop_map": {}, "default_route": 0}
    return json.loads(zlib.decompress(base64.b85decode(blob.encode("ascii"))).decode("utf-8"))


# --------------------------------------------------------------------------- helpers
def _get(value, key, default=None):
    """Field access that works for dicts and Kaggle's attribute-style Structs."""
    if isinstance(value, dict):
        return value.get(key, default)
    getter = getattr(value, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(value, key, default)


def _int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _step_of(observation):
    raw = _get(observation, "step")
    if raw is not None:
        return _int(raw)
    return _int(_get(observation, "day", 0)) * 24 + _int(_get(observation, "hour", 0))


def _shed_adjacent(pos, board):
    if not isinstance(pos, (list, tuple)) or len(pos) < 2:
        return False
    half = board // 2
    return _int(pos[0]) in (half - 1, half) and _int(pos[1]) in (half - 1, half)


def _tile_at(tiles, pos):
    try:
        return tiles[_int(pos[1])][_int(pos[0])]
    except (TypeError, ValueError, IndexError):
        return "LOCKED"


def projected_shed(observation, action, player, board, capacity):
    """The shed as the market will see it this turn.

    The interpreter applies every unit action before it touches the market, so a
    SELL this turn can draw on goods a DROP or PLACE puts in the shed on the
    same step, and cannot draw on goods a PICKUP has just removed. Mirrors
    ``_apply_unit_action``'s DROP / PLACE / PICKUP branches, including the fact
    that shed operations resolve before the LOCKED-tile guard.
    """
    private = _get(observation, "private", {}) or {}
    shed = {}
    for item, qty in dict(_get(private, "shed", {}) or {}).items():
        n = _int(qty)
        if n > 0:
            shed[item] = n
    invs = [dict(inv or {}) for inv in (_get(private, "inventories", []) or [])]
    farms = list(_get(observation, "farms", []) or [])
    farm = farms[player] if player < len(farms) else {}
    tiles = _get(farm, "tiles", []) or []
    positions = [_get(farm, "farmer", None)]
    positions.extend(list(p) for p in (_get(farm, "hands", []) or []))
    units = [action.get("farmer") or ["PASS"]]
    units.extend(action.get("hands") or [])

    for idx, pos in enumerate(positions):
        if idx >= len(units):
            break
        act = units[idx]
        if not isinstance(act, (list, tuple)) or not act:
            continue
        op = act[0]
        if op not in ("DROP", "PLACE", "PICKUP"):
            continue
        inv = invs[idx] if idx < len(invs) else {}
        adjacent = _shed_adjacent(pos, board)
        if op == "DROP":
            if not adjacent:
                continue
            for item, qty in inv.items():
                n = _int(qty)
                if n <= 0:
                    continue
                room = max(0, capacity - sum(shed.values()))
                take = min(n, room)
                if take > 0:
                    shed[item] = shed.get(item, 0) + take
        elif op == "PICKUP":
            if not adjacent or len(act) < 2:
                continue
            item = act[1]
            n = _int(act[2], 1) if len(act) >= 3 else 1
            n = min(n, shed.get(item, 0))
            if n > 0:
                shed[item] -= n
                if shed[item] <= 0:
                    del shed[item]
        else:  # PLACE
            if len(act) < 2:
                continue
            item = act[1]
            tile = _tile_at(tiles, pos) if pos else "LOCKED"
            # Placing an animal onto its matching empty structure never reaches
            # the shed path.
            if (item in ANIMALS and isinstance(tile, dict)
                    and _get(tile, "kind") == ANIMALS[item]
                    and _get(tile, "animal") is None):
                continue
            if not adjacent:
                continue
            n = _int(act[2], 1) if len(act) >= 3 else 1
            n = min(n, _int(inv.get(item, 0)), max(0, capacity - sum(shed.values())))
            if n > 0:
                shed[item] = shed.get(item, 0) + n
    return shed


def suppress_dead_sells(orders, shed, max_orders):
    """Drop SELL orders with nothing behind them; keep everything else in place.

    Returns ``(kept_orders, shed_after)``. Quantities are never lowered -- the
    engine stops a SELL the moment the shed runs dry, so only the *empty* order
    is waste, and only because it costs a slot.
    """
    work = dict(shed)
    kept = []
    for order in orders or []:
        if not isinstance(order, (list, tuple)) or not order:
            continue
        op = order[0]
        if op == "SELL" and len(order) >= 3:
            item = order[1]
            want = _int(order[2])
            have = work.get(item, 0)
            if want <= 0 or have <= 0 or item not in PRODUCTS:
                continue
            work[item] = max(0, have - want)
        elif op == "BUY_PRODUCT" and len(order) >= 3:
            work[order[1]] = work.get(order[1], 0) + max(0, _int(order[2]))
        kept.append(list(order))
        if len(kept) >= max_orders:
            break
    return kept, work


def liquidate(orders, shed, prices, max_orders, replace):
    """Sell out. ``replace`` throws the tape's own queue away (final step only)."""
    stock = [(item, qty) for item, qty in shed.items() if qty > 0 and item in PRODUCTS]
    stock.sort(key=lambda kv: (-_int(prices.get(kv[0], 0)) * kv[1], kv[0]))
    if replace:
        return [["SELL", item, qty] for item, qty in stock][:max_orders]
    already = {o[1] for o in orders if o and o[0] == "SELL" and len(o) > 1}
    out = list(orders)
    for item, qty in stock:
        if len(out) >= max_orders:
            break
        if item in already:
            continue
        out.append(["SELL", item, qty])
    return out[:max_orders]


def route_for_shops(shop_map, shops, default_route):
    """Route by the shops the town actually unlocked.

    ``shop_map`` is keyed on the ordered pair of the first two unlocked shops,
    which is everything the town has revealed by the start of day 6. Falls back
    to the pair taken in either order, then to a match on the first shop alone,
    then to the default opening route.
    """
    pair = tuple(shops[:2])
    if len(pair) == 2:
        hit = shop_map.get("%s|%s" % pair)
        if hit is not None:
            return int(hit)
        hit = shop_map.get("%s|%s" % (pair[1], pair[0]))
        if hit is not None:
            return int(hit)
    if len(pair) == 1:
        for key, route in sorted(shop_map.items()):
            if key.split("|")[0] == pair[0]:
                return int(route)
    return int(default_route)


# --------------------------------------------------------------------------- agent
def build_agent(payload, settings=None):
    """Build the ``agent(observation, configuration)`` callable from a payload."""
    routes = [list(tape) for tape in payload.get("routes", [])]
    shop_map = dict(payload.get("shop_map", {}))
    default_route = int(payload.get("default_route", 0))
    decide_step = int(payload.get("decide_step", DECIDE_STEP))
    liquidate_from = int(payload.get("liquidate_from", LIQUIDATE_FROM))
    cfg = dict(_DEFAULTS)
    cfg.update(settings or {})
    players = {}
    stats = {"steps": 0, "sells_dropped": 0, "liquidation_orders": 0, "routes_used": {}}

    def decide(observation, configuration=None):
        if not routes:
            return dict(PASS_ACTION)
        step = _step_of(observation)
        player = _int(_get(observation, "player", 0))
        board = _int(_get(configuration, "boardSize", cfg["board_size"]), cfg["board_size"])
        capacity = _int(_get(configuration, "shedCapacity", cfg["shed_capacity"]),
                        cfg["shed_capacity"])
        max_orders = _int(_get(configuration, "maxMarketOrdersPerTurn", cfg["max_orders"]),
                          cfg["max_orders"])

        mind = players.setdefault(player, {"route": default_route, "locked": False})
        if not mind["locked"] and step >= decide_step:
            town = _get(observation, "town", {}) or {}
            shops = list(_get(town, "unlocked_shops", []) or [])
            mind["route"] = route_for_shops(shop_map, shops, default_route)
            mind["locked"] = True
        route = mind["route"] if 0 <= mind["route"] < len(routes) else default_route
        stats["routes_used"][route] = stats["routes_used"].get(route, 0) + 1

        # The record at index k was chosen while observing step k-1.
        tape = routes[route]
        index = step + 1
        planned = tape[index] if 0 <= index < len(tape) and isinstance(tape[index], dict) else {}
        action = {
            "farmer": list(planned.get("farmer") or ["PASS"]),
            "hands": [list(a) for a in (planned.get("hands") or [])],
            "market": [list(o) for o in (planned.get("market") or [])],
        }

        shed = projected_shed(observation, action, player, board, capacity)
        raw = action["market"]
        if PREMIUM_SELL_CAP is not None and step < liquidate_from:
            metered = []
            for order in raw:
                if (isinstance(order, (list, tuple)) and len(order) >= 3
                        and order[0] == "SELL" and order[1] in PREMIUM_GOODS):
                    order = [order[0], order[1],
                             min(_int(order[2]), PREMIUM_SELL_CAP)]
                metered.append(list(order))
            raw = metered
            action["market"] = raw
        kept, after = suppress_dead_sells(raw, shed, max_orders)
        stats["sells_dropped"] += max(0, len(raw[:max_orders]) - len(kept))
        action["market"] = kept

        if step >= liquidate_from:
            market = _get(observation, "market", {}) or {}
            prices = dict(_get(market, "prices", {}) or {})
            before = len(action["market"])
            action["market"] = liquidate(action["market"], after, prices, max_orders,
                                         replace=(step >= LAST_ACT_STEP))
            stats["liquidation_orders"] += max(0, len(action["market"]) - before)
        if ORDER_MICROSTRUCTURE:
            rank = {"SELL": 0, "BUY_PRODUCT": 1}
            action["market"] = sorted(
                action["market"], key=lambda o: rank.get(str(o[0]), 2))
        stats["steps"] += 1
        return action

    def agent(observation, configuration=None):
        try:
            return decide(observation, configuration)
        except Exception:
            return dict(PASS_ACTION)

    agent.stats = stats
    agent.players = players
    agent.routes = routes
    return agent


_PAYLOAD = _decode_payload(_PAYLOAD_B85)
ROUTE_META = _PAYLOAD.get("meta", [])
SHOP_MAP = _PAYLOAD.get("shop_map", {})
_IMPL = build_agent(_PAYLOAD)


# kaggle_environments loads a submitted file with `get_last_callable`, which
# takes the LAST callable defined in the module -- not the one named `agent`.
# So agent() must be the final definition in this file. It was not, once, and
# the ladder ran the diagnostic below as the agent: every action was rejected
# as malformed, both farms sat at their starting 3,000 coins for thirty days,
# and the submission scored a tie against itself.
def recorded_fraction():
    """How much of a game is replay and how much is Agent I reacting.

    Every farmer instruction and every hand instruction on all 719 acting steps
    comes straight off the tape: Agent I never writes one. The only thing it
    re-decides is the market queue, and only in two ways -- removing SELL orders
    that cannot fill, and selling the shed out at the end.
    """
    return {
        "unit_actions_recorded": 1.0,
        "market_steps_touched_by_liquidation": (LAST_ACT_STEP - LIQUIDATE_FROM + 1) / 719.0,
        "decisions_made_by_agent_i": "one route choice at step %d" % DECIDE_STEP,
    }


def agent(observation, configuration=None):
    return _IMPL(observation, configuration)
