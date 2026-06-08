"""Build a recency-weighted Massey rating (direct results + common-opponent chaining, by construction)
from 2021+ results, INDEPENDENT of Elo. Then measure divergence vs Elo for the 48 WC teams."""
import json, csv, io, sys, math
import numpy as np
from datetime import date
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
P = r'C:\Users\simon\Projects\pollawc2026'
GROUPS = json.load(open(f'{P}\\data\\draw_verified.json', encoding='utf-8'))['groups']
elo = json.load(open(f'{P}\\data\\elo_raw.json', encoding='utf-8'))
WC = [t for g in GROUPS.values() for t in g]
ELOALIAS = {'United States':'USA','Czech Republic':'Czechia','Bosnia and Herzegovina':'Bosnia/Herz'}
def ekey(t):
    for k in (t, ELOALIAS.get(t,t)):
        if k in elo: return k
    for k in elo:
        if k.lower().replace('.','')==t.lower().replace('.',''): return k
    raise KeyError(t)

rows = list(csv.DictReader(open(f'{P}\\data\\results_recent.csv', encoding='utf-8')))
TODAY = date(2026,6,8)
def wcomp(t):
    if t=='FIFA World Cup': return 1.0
    if 'qualification' in t: return 0.7
    if any(k in t for k in ('Nations League','Euro','Copa','African Cup','Asian Cup','Gold Cup','Confederations')): return 0.8
    if t=='Friendly': return 0.4
    return 0.6
HFA = 0.43  # same home-goal bonus as the main calibration

# index every team that appears
teams = sorted({r['home_team'] for r in rows} | {r['away_team'] for r in rows})
ix = {t:i for i,t in enumerate(teams)}; n=len(teams)
Mmat = np.zeros((n,n)); b = np.zeros(n); games = np.zeros(n)
for r in rows:
    try: gh,ga=int(r['home_score']),int(r['away_score'])
    except: continue
    h,a=r['home_team'],r['away_team']; i,j=ix[h],ix[a]
    y,m,d=map(int,r['date'].split('-')); yrs=(TODAY-date(y,m,d)).days/365.25
    w = 0.5**(yrs/2.0) * wcomp(r['tournament'])          # recency half-life 2y x competition
    margin = max(-4,min(4, gh-ga)) - (0 if r['neutral'].upper()=='TRUE' else HFA)  # neutralize home edge
    Mmat[i,i]+=w; Mmat[j,j]+=w; Mmat[i,j]-=w; Mmat[j,i]-=w
    b[i]+=w*margin; b[j]-=w*margin; games[i]+=w; games[j]+=w
# sum-to-zero constraint (replace last eq)
Mmat[-1,:]=1; b[-1]=0
rating = np.linalg.lstsq(Mmat,b,rcond=None)[0]   # Massey rating, units = goals vs avg team, neutral site
massey = {t: rating[ix[t]] for t in teams}

# ---- compare on the 48 WC teams ----
rows_cmp=[]
for t in WC:
    e=elo[ekey(t)]; m=massey.get(t)
    rows_cmp.append((t,e,m,games[ix[t]]))
E=np.array([r[1] for r in rows_cmp],float)
Mr=np.array([r[2] for r in rows_cmp],float)
# linear fit Elo ~ a + b*Massey  -> put Massey on Elo scale, residual = divergence
A=np.column_stack([np.ones_like(Mr),Mr]); coef,*_=np.linalg.lstsq(A,E,rcond=None); pred=A@coef
resid=E-pred
ss_res=np.sum(resid**2); ss_tot=np.sum((E-E.mean())**2); R2=1-ss_res/ss_tot
from numpy import corrcoef
pear=corrcoef(E,Mr)[0,1]
# spearman
def rank(x):
    o=np.argsort(np.argsort(x)); return o
spear=corrcoef(rank(E),rank(Mr))[0,1]
print(f'Massey (common-opponent) vs Elo, {len(WC)} WC teams:')
print(f'  Pearson r = {pear:.3f}   Spearman rho = {spear:.3f}   R^2 (Elo explained by Massey) = {R2:.3f}')
print(f'  Residual std = {resid.std():.0f} Elo-equivalent points  (avg WC team Elo ~{E.mean():.0f})')
print(f'  Elo-points per Massey goal = {coef[1]:.0f}\n')

order=np.argsort(-np.abs(resid))
print('Biggest DISAGREEMENTS (Massey vs Elo), + = Massey rates HIGHER than Elo implies:')
print(f'  {"Team":24s} {"Elo":>5s} {"MasseyG":>8s} {"resid(Elo)":>11s} {"wGames":>6s}')
for k in order[:12]:
    t,e,m,g=rows_cmp[k]
    print(f'  {t:24s} {e:5d} {m:+8.2f} {resid[k]:+11.0f} {g:6.1f}')

# Belgium-Iran head to head in both metrics
def sup_elo(a,b): return 0.00465*(elo[ekey(a)]-elo[ekey(b)])
print('\nBelgium vs Iran supremacy (neutral, goals):')
print(f'  Elo-model:    {sup_elo("Belgium","Iran"):+.2f}')
print(f'  Massey-model: {massey["Belgium"]-massey["Iran"]:+.2f}   (Belgium wGames {games[ix["Belgium"]]:.1f}, Iran {games[ix["Iran"]]:.1f})')

# ---- emit blended strength for Entry C: 50% Elo + 50% Massey(on Elo scale) ----
W_MASSEY = 0.5
strengthC = {}
for t in WC:
    massey_elo = coef[0] + coef[1]*massey[t]      # Massey mapped onto Elo scale
    strengthC[t] = round((1-W_MASSEY)*elo[ekey(t)] + W_MASSEY*massey_elo, 1)
json.dump(strengthC, open(f'{P}\\data\\strength_C.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'\nWrote data/strength_C.json (blend {1-W_MASSEY:.0%} Elo / {W_MASSEY:.0%} Massey) for {len(strengthC)} teams.')
print('Biggest C-vs-Elo shifts:')
for t in sorted(WC, key=lambda x: abs(strengthC[x]-elo[ekey(x)]), reverse=True)[:6]:
    print(f'  {t:22s} Elo {elo[ekey(t)]:4d} -> C {strengthC[t]:.0f} ({strengthC[t]-elo[ekey(t)]:+.0f})')
