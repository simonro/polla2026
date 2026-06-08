"""Build full picks for Entry A (consensus) and Entry B (contrarian) + edge finder.
Reads sim_results.json, blends.json, draw + bracket files. Writes picks_A/B.json, edges.json."""
import json, io, sys
from collections import defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
P = r'C:\Users\simon\Projects\pollawc2026'
TAG = sys.argv[1] if len(sys.argv) > 1 else ''        # '' -> Entries A & B; 'C' -> Entry C
# ALL entries now run on the corrected 3-source strength (Elo+Massey+market, +injuries) — the
# sim_results_C / blends_C engine. TAG only controls which entry's champion override is applied.
# This removes the CONMEBOL/Elo-inflation artifacts (Group E->Germany, no Ecuador>Brazil, Turkey>Belgium).
sim = json.load(open(f'{P}\\output\\sim_results_C.json', encoding='utf-8'))
teams = sim['teams']; GP = sim['group_pred']
bl = json.load(open(f'{P}\\output\\blends_C.json', encoding='utf-8'))
CH = bl['market_leaning']; FIELD = bl['field']; SIMCH = bl['sim_ch']; MKT = bl['market_full']
draw = json.load(open(f'{P}\\data\\draw_verified.json', encoding='utf-8'))
GROUPS = draw['groups']
r32 = json.load(open(f'{P}\\data\\bracket_r32.json', encoding='utf-8'))['r32']
tree = json.load(open(f'{P}\\data\\bracket_tree.json', encoding='utf-8'))
ELO = {t: teams[t]['elo'] for t in teams}
def grp(t):
    for g,ts in GROUPS.items():
        if t in ts: return g

# ---- predicted group standings from expected points -------------------------
exp_pts = defaultdict(float); exp_gd = defaultdict(float)
for m in GP:
    h,a = m['home'], m['away']; pH,pD,pA = m['pH'],m['pD'],m['pA']; sh,sa = m['score']
    exp_pts[h] += 3*pH + pD; exp_pts[a] += 3*pA + pD
    exp_gd[h] += sh-sa; exp_gd[a] += sa-sh
standings = {}
for g,ts in GROUPS.items():
    standings[g] = sorted(ts, key=lambda t:(exp_pts[t], exp_gd[t], ELO[t]), reverse=True)

# ---- best 8 thirds + slot matching ------------------------------------------
thirds = {g: standings[g][2] for g in GROUPS}
best8 = sorted(GROUPS, key=lambda g:(exp_pts[thirds[g]], exp_gd[thirds[g]], ELO[thirds[g]]), reverse=True)[:8]
THIRD_SLOTS = {}
for m in r32:
    for side in ('home','away'):
        if m[side].startswith('3'): THIRD_SLOTS[(m['m'],side)] = list(m[side][1:])
def match_thirds(qgroups):
    slots = sorted(THIRD_SLOTS.items(), key=lambda kv: len(kv[1])); assign={}; used=set()
    def bt(i):
        if i==len(slots): return True
        key,allowed = slots[i]
        for gg in allowed:
            if gg in qgroups and gg not in used:
                used.add(gg); assign[key]=gg
                if bt(i+1): return True
                used.remove(gg); del assign[key]
        return False
    return assign if bt(0) else None
assign = match_thirds(set(best8))

winners = {g: standings[g][0] for g in GROUPS}
runners = {g: standings[g][1] for g in GROUPS}
def resolve(tok, side, m):
    if tok[0]=='1': return winners[tok[1]]
    if tok[0]=='2': return runners[tok[1]]
    if tok[0]=='3':
        g = assign.get((m,side)); return thirds[g] if g else None
    return None

# ---- KO advancement prob (recompute lightweight from elo via sim calib) ------
calib = sim['calib']; B_SUP=calib['sup_per_elo']; TOT=calib['avg_total']; RHO=calib['rho']
import math
def ko_p(a,b):
    sup=B_SUP*(ELO[a]-ELO[b]); lh=max(.12,(TOT+sup)/2); la=max(.12,(TOT-sup)/2)
    ph=[math.exp(-lh)*lh**i/math.factorial(i) for i in range(9)]
    pa=[math.exp(-la)*la**i/math.factorial(i) for i in range(9)]
    import numpy as np; M=np.outer(ph,pa)
    M[0,0]*=1-lh*la*RHO; M[0,1]*=1+lh*RHO; M[1,0]*=1+la*RHO; M[1,1]*=1-RHO; M/=M.sum()
    pHw=np.tril(M,-1).sum(); pAw=np.triu(M,1).sum(); pDr=1-pHw-pAw
    so=1/(1+10**(-(ELO[a]-ELO[b])/600))
    return pHw+pDr*so

def build_bracket(force=None):
    """force: dict team->'CH'|'F'|'SF'|'QF' = make that team win until that round. Else favorite advances."""
    force = force or {}
    ROUND_AT = {73:'R32',89:'R16',97:'QF',101:'SF',104:'CH'}  # match -> round label of its WINNER
    order = {'R32':0,'R16':1,'QF':2,'SF':3,'CH':4}
    def round_of_winner(m):
        if m<=88: return 'R32'
        if m<=96: return 'R16'
        if m<=100: return 'QF'
        if m<=102: return 'SF'
        return 'CH'
    part={}; winner={}
    for mm in r32:
        h=resolve(mm['home'],'home',mm['m']); a=resolve(mm['away'],'away',mm['m'])
        part[mm['m']]=(h,a)
    def pick(h,a,rnd):
        if h is None: return a
        if a is None: return h
        for t in (h,a):
            if t in force and order[round_of_winner_target(t)]>=order[rnd]:
                # forced team wins this round if its target round >= this round
                return t
        return h if ko_p(h,a)>=ko_p(a,h) else a
    def round_of_winner_target(t): return force[t]
    # R32
    for mm in r32:
        h,a=part[mm['m']]; winner[mm['m']]=pick(h,a,'R32')
    def play(d, rnd):
        for m,(f1,f2) in d.items():
            w1,w2=winner.get(int(f1)),winner.get(int(f2)); winner[int(m)]=pick(w1,w2,rnd)
    play(tree['r16'],'R16'); play(tree['qf'],'QF'); play(tree['sf'],'SF'); play(tree['final'],'CH')
    return part, winner

def bracket_rounds(winner, part):
    R32=[part[m['m']] for m in r32]
    r16w=[winner[m['m']] for m in r32]
    r16m={int(k):(winner.get(int(v[0])),winner.get(int(v[1]))) for k,v in tree['r16'].items()}
    r16win=[winner[int(m)] for m in tree['r16']]
    qfwin=[winner[int(m)] for m in tree['qf']]
    sfwin=[winner[int(m)] for m in tree['sf']]
    champ=winner[104]; finalists=[winner[int(m)] for m in tree['sf']]
    return r16win, r16win, qfwin, sfwin, finalists, champ

# Three DISTINCT champions for diversification:
#   A = England champ (distinct 3rd, wins right half)  | B = France champ + Portugal->SF leverage
#   C = favorites on the 3-source strength (= Spain)
A_FORCE = {'England':'CH'}
B_FORCE = {'France':'CH', 'Portugal':'SF'}
if TAG == 'C':
    partC, winC = build_bracket(force={})
else:
    partA, winA = build_bracket(force=A_FORCE)
    partB, winB = build_bracket(force=B_FORCE)

def conf_ko(p):
    return 'High' if p>=0.65 else ('Med' if p>=0.55 else 'Low')
def summarize(part, winner, label):
    out={'round32':[], 'r16':[], 'qf':[], 'sf':[], 'final':None, 'champion':winner[104]}
    for mm in r32:
        h,a=part[mm['m']]; w=winner[mm['m']]; l=a if w==h else h
        p=ko_p(w,l) if (h and a) else 1.0
        out['round32'].append({'m':mm['m'],'home':h,'away':a,'pick':w,'conf':conf_ko(p),'p':round(p,3)})
    for grpname,dct in (('r16',tree['r16']),('qf',tree['qf']),('sf',tree['sf'])):
        for m,(f1,f2) in dct.items():
            w1,w2=winner.get(int(f1)),winner.get(int(f2)); w=winner[int(m)]; l=w2 if w==w1 else w1
            p=ko_p(w,l); out[grpname].append({'m':int(m),'a':w1,'b':w2,'pick':w,'conf':conf_ko(p),'p':round(p,3)})
    fa,fb = winner[int(list(tree['final'].values())[0][0])], winner[int(list(tree['final'].values())[0][1])]
    pf=ko_p(winner[104], fb if winner[104]==fa else fa)
    out['final']={'a':fa,'b':fb,'pick':winner[104],'conf':conf_ko(pf),'p':round(pf,3)}
    return out

if TAG == 'C':
    C = summarize(partC, winC, 'C')
else:
    A = summarize(partA, winA, 'A'); B = summarize(partB, winB, 'B')

# ---- group-stage 72 picks with confidence + rationale -----------------------
def conf_score(m):
    pmax=max(m['pH'],m['pD'],m['pA'])
    return 'High' if pmax>=0.55 else ('Med' if pmax>=0.42 else 'Low')
group_picks=[]
for m in GP:
    fav = m['home'] if m['pH']>=m['pA'] else m['away']
    pmax=max(m['pH'],m['pD'],m['pA'])
    res='draw' if (m['pD']>=m['pH'] and m['pD']>=m['pA']) else fav
    note=f"{fav} favored ({max(m['pH'],m['pA'])*100:.0f}% vs {min(m['pH'],m['pA'])*100:.0f}%); modal {m['score'][0]}-{m['score'][1]}"
    group_picks.append({**m,'conf':conf_score(m),'fav':res,'note':note})

# ---- edge finder ------------------------------------------------------------
edges_lev = sorted(teams, key=lambda t: (CH[t]/FIELD[t] if FIELD[t] else 0), reverse=True)
field_lev=[{'team':t,'champ':round(CH[t]*100,1),'field':round(FIELD[t]*100,1),
            'leverage':round(CH[t]/FIELD[t],2)} for t in edges_lev if CH[t]>=0.05][:10]
fades=[{'team':t,'champ':round(CH[t]*100,1),'field':round(FIELD[t]*100,1),
        'leverage':round(CH[t]/FIELD[t],2)} for t in sorted(teams,key=lambda t:(CH[t]/FIELD[t] if FIELD[t] else 9)) if FIELD[t]>0.02][:5]
model_market=[{'team':t,'sim':round(SIMCH[t]*100,1),'market':round(MKT[t]*100,1),
               'gap':round((SIMCH[t]-MKT[t])*100,1)} for t in sorted(teams,key=lambda t:abs(SIMCH[t]-MKT[t]),reverse=True)[:8]]

if TAG == 'C':
    # Entry C = favorites on the 3-source (Elo+Massey+market) strength (already summarized above).
    json.dump({'entry':'C','standings':standings,'best8_thirds':[thirds[g] for g in best8],
               'bracket':C,'group_picks':group_picks},
              open(f'{P}\\output\\picks_C.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    json.dump({'field_leverage':field_lev,'fades':fades,'model_market_gaps':model_market},
              open(f'{P}\\output\\edges_C.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
else:
    json.dump({'entry':'A','standings':standings,'best8_thirds':[thirds[g] for g in best8],
               'bracket':A,'group_picks':group_picks},
              open(f'{P}\\output\\picks_A.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    json.dump({'entry':'B','standings':standings,'best8_thirds':[thirds[g] for g in best8],
               'bracket':B,'group_picks':group_picks,'force':B_FORCE},
              open(f'{P}\\output\\picks_B.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    json.dump({'field_leverage':field_lev,'fades':fades,'model_market_gaps':model_market},
              open(f'{P}\\output\\edges.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)

# ---- console summary --------------------------------------------------------
print('PREDICTED GROUP WINNERS / RUNNERS (both entries share groups):')
for g in GROUPS:
    print(f'  {g}: 1.{standings[g][0]:22s} 2.{standings[g][1]:22s} 3.{standings[g][2]}')
print('\nBest-8 thirds:', [thirds[g] for g in best8])
def show_bracket(X,name):
    print(f'\n=== ENTRY {name} bracket ===')
    print('  QF:', ' | '.join(f"{x['pick']}({x['conf'][0]})" for x in X['qf']))
    print('  SF:', ' | '.join(f"{x['pick']}({x['conf'][0]})" for x in X['sf']))
    print('  Final:', X['final']['a'],'vs',X['final']['b'],'->',X['final']['pick'])
    print('  CHAMPION:', X['champion'])
if TAG == 'C':
    show_bracket(C,'C (3-source: Elo+Massey+market)')
    print('\nWrote picks_C.json')
else:
    show_bracket(A,'A'); show_bracket(B,'B')
    print('\nFIELD-LEVERAGE (Entry B targets):')
    for e in field_lev[:6]: print(f"  {e['team']:14s} champ {e['champ']}% field {e['field']}% lev {e['leverage']}x")
    print('FADES (over-crowded):')
    for e in fades[:4]: print(f"  {e['team']:14s} lev {e['leverage']}x")
    print('\nWrote picks_A.json, picks_B.json, edges.json')
