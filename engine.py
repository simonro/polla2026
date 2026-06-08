"""
Polla WC2026 prediction engine.
Elo-anchored Dixon-Coles scoreline model + Monte Carlo of the real 2026 bracket.
Data is verified/current (see data/*.json _meta). No LLM-extracted numbers in the math path.
"""
import json, csv, io, sys, math
import numpy as np
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
RNG = np.random.default_rng(20260608)
D = r'C:\Users\simon\Projects\pollawc2026\data'
OUT_TAG = sys.argv[1] if len(sys.argv) > 1 else ''          # '' -> sim_results.json; 'C' -> sim_results_C.json
STR_OVR = sys.argv[2] if len(sys.argv) > 2 else None        # optional strength override json (draw-name -> rating)

# ----------------------------------------------------------------------------- load
draw = json.load(open(f'{D}\\draw_verified.json', encoding='utf-8'))
GROUPS = draw['groups']                      # {'A': [4 teams], ...}
elo_raw = json.load(open(f'{D}\\elo_raw.json', encoding='utf-8'))
r32 = json.load(open(f'{D}\\bracket_r32.json', encoding='utf-8'))['r32']
tree = json.load(open(f'{D}\\bracket_tree.json', encoding='utf-8'))
fixtures = list(csv.DictReader(open(f'{D}\\wc2026_fixtures.csv', encoding='utf-8')))

TEAMS = [t for g in GROUPS.values() for t in g]
assert len(TEAMS) == 48

# Elo name aliases: draw-name -> eloratings-name
ALIAS = {
    'United States': 'USA', 'Czech Republic': 'Czechia', 'Turkey': 'Turkey',
    'Curaçao': 'Curacao', 'Ivory Coast': 'Ivory Coast', 'DR Congo': 'DR Congo',
    'Cape Verde': 'Cape Verde', 'Bosnia and Herzegovina': 'Bosnia/Herz',
    'South Korea': 'South Korea', 'Saudi Arabia': 'Saudi Arabia',
}
def elo_of(team):
    for key in (team, ALIAS.get(team, team)):
        if key in elo_raw:
            return elo_raw[key]
    # loose contains-match
    for k, v in elo_raw.items():
        if k.lower().replace('.', '') == team.lower().replace('.', ''):
            return v
    return None

ELO = {}
missing = []
for t in TEAMS:
    e = elo_of(t)
    if e is None: missing.append(t)
    else: ELO[t] = e
if missing:
    print('UNMATCHED ELO:', missing)
    # print candidate elo keys to help fix
    for m in missing:
        cands = [k for k in elo_raw if m.split()[0].lower() in k.lower()]
        print('  ', m, '->', cands[:5])
    sys.exit(1)
print('Elo resolved for all 48 teams. Range %d-%d' % (min(ELO.values()), max(ELO.values())))
if STR_OVR:
    ov = json.load(open(STR_OVR, encoding='utf-8'))
    nov = 0
    for t, v in ov.items():
        if t in ELO: ELO[t] = float(v); nov += 1
    print(f'STRENGTH OVERRIDE: replaced {nov} WC team ratings from {STR_OVR} (range %d-%d)'
          % (min(ELO.values()), max(ELO.values())))
import os as _os
_inj = f'{D}\\injury_adj.json'
if _os.path.exists(_inj):
    inj = json.load(open(_inj, encoding='utf-8'))
    na = 0
    for t, d in inj.items():
        if t in ELO and isinstance(d, (int, float)): ELO[t] += d; na += 1
    print(f'INJURY ADJUSTMENT: applied to {na} teams (e.g. Brazil {inj.get("Brazil")}, applied on top of base/override)')

# ----------------------------------------------------------------------------- calibrate
rows = list(csv.DictReader(open(f'{D}\\results_recent.csv', encoding='utf-8')))
# eloratings name set for matching historical teams
def hist_elo(name):
    if name in elo_raw: return elo_raw[name]
    return None
X_diff, X_home, Y_diff, totals = [], [], [], []
for r in rows:
    try:
        gh, ga = int(r['home_score']), int(r['away_score'])
    except: continue
    eh, ea = hist_elo(r['home_team']), hist_elo(r['away_team'])
    if eh is None or ea is None: continue
    home = 0 if r['neutral'].upper() == 'TRUE' else 1
    X_diff.append(eh - ea); X_home.append(home)
    Y_diff.append(gh - ga); totals.append(gh + ga)
X_diff = np.array(X_diff); X_home = np.array(X_home); Y_diff = np.array(Y_diff); totals = np.array(totals)
# OLS: goal_diff = b*elo_diff + c*home
A = np.column_stack([X_diff, X_home])
coef, *_ = np.linalg.lstsq(A, Y_diff, rcond=None)
B_SUP, C_HOME = coef            # supremacy per elo pt, home goal bonus
BASE_TOTAL = totals.mean()
RHO = -0.04                      # Dixon-Coles low-score correction (mild, standard)
print(f'Calibrated on {len(Y_diff)} matches: supremacy/Elo={B_SUP:.5f} (~{1/B_SUP:.0f} Elo/goal), '
      f'home={C_HOME:.3f} goals, avg total={BASE_TOTAL:.2f}')

HOST_COUNTRY = {'Mexico': 'Mexico', 'Canada': 'Canada', 'United States': 'United States'}
MAXG = 9

def lambdas(home_team, away_team, home_flag):
    sup = B_SUP * (ELO[home_team] - ELO[away_team]) + C_HOME * home_flag
    lh = max(0.12, (BASE_TOTAL + sup) / 2)
    la = max(0.12, (BASE_TOTAL - sup) / 2)
    return lh, la

def dc_matrix(lh, la):
    """Dixon-Coles adjusted scoreline probability matrix (MAXG x MAXG)."""
    ph = np.array([math.exp(-lh) * lh**i / math.factorial(i) for i in range(MAXG)])
    pa = np.array([math.exp(-la) * la**i / math.factorial(i) for i in range(MAXG)])
    M = np.outer(ph, pa)
    t = 1.0
    M[0,0] *= 1 - lh*la*RHO
    M[0,1] *= 1 + lh*RHO
    M[1,0] *= 1 + la*RHO
    M[1,1] *= 1 - RHO
    M /= M.sum()
    return M

def outcome_probs(M):
    pH = np.tril(M, -1).sum()   # home goals > away
    pA = np.triu(M, 1).sum()
    pD = 1 - pH - pA
    return pH, pD, pA

def modal_score(M):
    i, j = np.unravel_index(np.argmax(M), M.shape)
    return int(i), int(j)

def ko_adv_prob(a, b):
    """P(a advances past b) in a knockout: reg win + half of draws -> shootout slightly toward stronger."""
    lh, la = lambdas(a, b, 0)
    M = dc_matrix(lh, la)
    pH, pD, pA = outcome_probs(M)
    # shootout edge: logistic of elo diff, gentle
    so = 1/(1+10**(-(ELO[a]-ELO[b])/600))
    return pH + pD*so

# Precompute KO advancement matrix
idx = {t:i for i,t in enumerate(TEAMS)}
ADV = np.zeros((48,48))
for a in TEAMS:
    for b in TEAMS:
        if a!=b: ADV[idx[a],idx[b]] = ko_adv_prob(a,b)

# ----------------------------------------------------------------------------- group fixtures
# map fixtures to (home,away,group,home_flag); store lambdas
def team_group(t):
    for g,ts in GROUPS.items():
        if t in ts: return g
ALIAS_FIX = {'Czechia':'Czech Republic','Türkiye':'Turkey','Turkey':'Turkey','Curacao':'Curaçao'}
def norm_fix(name):
    name = ALIAS_FIX.get(name, name)
    return name
GF = []   # group fixtures
for r in fixtures:
    h, a = norm_fix(r['home_team']), norm_fix(r['away_team'])
    if h not in idx or a not in idx:
        print('fixture team not in draw:', r['home_team'], r['away_team']); continue
    g = team_group(h)
    home_flag = 1 if HOST_COUNTRY.get(h) and r['country']==HOST_COUNTRY[h] else 0
    lh, la = lambdas(h, a, home_flag)
    GF.append((h,a,g,lh,la))
assert len(GF)==72, len(GF)
print(f'{len(GF)} group fixtures mapped.')

# modal group scores (deterministic prediction) + group match outcome probs
GROUP_PRED = []
for h,a,g,lh,la in GF:
    M = dc_matrix(lh,la); sh,sa = modal_score(M); pH,pD,pA = outcome_probs(M)
    GROUP_PRED.append({'group':g,'home':h,'away':a,'score':[sh,sa],
                       'pH':round(pH,3),'pD':round(pD,3),'pA':round(pA,3)})

# ----------------------------------------------------------------------------- Monte Carlo
N = 30000
# sample all group fixture goals vectorized
gh_all = np.array([RNG.poisson(lh, N) for h,a,g,lh,la in GF])   # (72,N)
ga_all = np.array([RNG.poisson(la, N) for h,a,g,lh,la in GF])

# index fixtures per group
group_fix_idx = defaultdict(list)
for fi,(h,a,g,lh,la) in enumerate(GF): group_fix_idx[g].append(fi)
GLIST = list(GROUPS.keys())

# third-slot allowed groups (from r32 '3XXXX')
def third_slots():
    slots = {}
    for m in r32:
        for side in ('home','away'):
            v = m[side]
            if v.startswith('3'):
                slots[m['m'], side] = list(v[1:])
    return slots
THIRD_SLOTS = third_slots()

reach = {t: {'R32':0,'R16':0,'QF':0,'SF':0,'F':0,'CH':0} for t in TEAMS}
win_group = {t:0 for t in TEAMS}; runner=defaultdict(int); third_q=defaultdict(int)

def rank_group(g, s):
    """Return ordered [1st,2nd,3rd,4th] and the 3rd-place sort key, for group g in sim s."""
    teams = GROUPS[g]
    pts = {t:0 for t in teams}; gd={t:0 for t in teams}; gf={t:0 for t in teams}
    for fi in group_fix_idx[g]:
        h,a,_,_,_ = GF[fi]; hh,aa = int(gh_all[fi,s]), int(ga_all[fi,s])
        gf[h]+=hh; gf[a]+=aa; gd[h]+=hh-aa; gd[a]+=aa-hh
        if hh>aa: pts[h]+=3
        elif aa>hh: pts[a]+=3
        else: pts[h]+=1; pts[a]+=1
    # tiebreak: pts, gd, gf, then elo (proxy for fairplay+rank), then random (drawn once)
    order = sorted(teams, key=lambda t:(pts[t], gd[t], gf[t], ELO[t], RNG.random()), reverse=True)
    t3 = order[2]
    return order, (pts[t3], gd[t3], gf[t3], ELO[t3])

def match_thirds(qual_groups):
    """Assign each qualifying 3rd (by group letter) to a third-slot. Returns {(m,side):group} or None."""
    slots = list(THIRD_SLOTS.items())   # [((m,side),[allowed groups]),...]
    groups = list(qual_groups)
    # backtracking perfect matching slot<-group
    assign = {}
    used = set()
    slots_sorted = sorted(slots, key=lambda kv: len(kv[1]))  # most-constrained first
    def bt(i):
        if i==len(slots_sorted): return True
        key, allowed = slots_sorted[i]
        for gg in allowed:
            if gg in groups and gg not in used:
                used.add(gg); assign[key]=gg
                if bt(i+1): return True
                used.remove(gg); del assign[key]
        return False
    if bt(0): return assign
    return None

def play(mlist):
    """Resolve winners for a dict of {match: [feeder1, feeder2]} using ADV. No reach bookkeeping."""
    for m,(f1,f2) in mlist.items():
        w1,w2=winner_of.get(int(f1) if str(f1).isdigit() else f1), winner_of.get(int(f2) if str(f2).isdigit() else f2)
        if w1 is None or w2 is None: continue
        w = w1 if RNG.random()<ADV[idx[w1],idx[w2]] else w2
        winner_of[int(m)]=w

R16=tree['r16']; QF=tree['qf']; SF=tree['sf']; FIN=tree['final']
for s in range(N):
    winners={}; runners={}; tk={}; order_by_g={}
    for g in GLIST:
        order, k3 = rank_group(g,s)
        order_by_g[g]=order
        winners[g]=order[0]; runners[g]=order[1]; tk[g]=k3
        win_group[order[0]]+=1; runner[order[1]]+=1
    best = sorted(GLIST, key=lambda g: tk[g], reverse=True)[:8]
    qual_groups = set(best)
    third_team = {g: order_by_g[g][2] for g in GLIST}
    for g in best: third_q[third_team[g]]+=1
    assign = match_thirds(qual_groups)
    if assign is None:  # fallback (rare): greedy strongest valid by elo
        assign={}; gleft=set(qual_groups)
        for key,allowed in sorted(THIRD_SLOTS.items(),key=lambda kv:len(kv[1])):
            cand=[x for x in allowed if x in gleft]
            if cand: pick=max(cand,key=lambda gg:ELO[third_team[gg]]); assign[key]=pick; gleft.discard(pick)
    def resolve(token, side, m):
        if token[0]=='1': return winners[token[1]]
        if token[0]=='2': return runners[token[1]]
        if token[0]=='3':
            g=assign.get((m,side)); return third_team[g] if g else None
        return None
    winner_of={}
    for mm in r32:
        h=resolve(mm['home'],'home',mm['m']); a=resolve(mm['away'],'away',mm['m'])
        winner_of[('p',mm['m'])]=(h,a)
        for t in (h,a):
            if t: reach[t]['R32']+=1
    for mm in r32:
        h,a=winner_of[('p',mm['m'])]
        if h is None or a is None: continue
        winner_of[mm['m']] = h if RNG.random()<ADV[idx[h],idx[a]] else a
    # reach R16 = R32 winners who are participants of an R16 match
    for f1,f2 in R16.values():
        for f in (f1,f2):
            w=winner_of.get(f);
            if w: reach[w]['R16']+=1
    play(R16)
    for m in R16:                       # reach QF = R16 winners
        w=winner_of.get(int(m));
        if w: reach[w]['QF']+=1
    play(QF)
    for m in QF:                        # reach SF = QF winners
        w=winner_of.get(int(m));
        if w: reach[w]['SF']+=1
    play(SF)
    for m in SF:                        # reach F = SF winners
        w=winner_of.get(int(m));
        if w: reach[w]['F']+=1
    play(FIN)
    champ=winner_of.get(104)
    if champ: reach[champ]['CH']+=1

# ----------------------------------------------------------------------------- aggregate + report
res={}
for t in TEAMS:
    res[t]={k: round(v/N,4) for k,v in reach[t].items()}
    res[t]['win_group']=round(win_group[t]/N,4)
    res[t]['elo']=ELO[t]; res[t]['group']=team_group(t)

print('\n=== CHAMPION PROBABILITY (sim) vs market ===')
mkt=json.load(open(f'{D}\\market_odds.json',encoding='utf-8'))['kalshi_champion_pct']
for t,_ in sorted(res.items(), key=lambda kv:-kv[1]['CH'])[:14]:
    mk = mkt.get(t,'')
    print(f'  {t:24s} CH {res[t]["CH"]*100:5.1f}%   SF {res[t]["SF"]*100:5.1f}%   '
          f'R16 {res[t]["R16"]*100:5.1f}%   Elo {ELO[t]}   mkt {mk}')

_suf = ('_'+OUT_TAG) if OUT_TAG else ''
json.dump({'teams':res,'group_pred':GROUP_PRED,
           'calib':{'sup_per_elo':B_SUP,'home_goals':C_HOME,'avg_total':BASE_TOTAL,'rho':RHO}},
          open(rf'C:\Users\simon\Projects\pollawc2026\output\sim_results{_suf}.json','w',encoding='utf-8'),
          ensure_ascii=False, indent=1)
print(f'\nWrote output/sim_results{_suf}.json   (N=%d sims)'%N)
