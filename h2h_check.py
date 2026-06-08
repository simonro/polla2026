import json, csv, io, sys
from collections import defaultdict
from itertools import combinations
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
P = r'C:\Users\simon\Projects\pollawc2026'
GROUPS = json.load(open(f'{P}\\data\\draw_verified.json', encoding='utf-8'))['groups']
TEAMS = [t for g in GROUPS.values() for t in g]
ALIAS = {'United States':'USA','Czech Republic':'Czechia','Turkey':'Turkey','Curaçao':'Curacao',
         'Bosnia and Herzegovina':'Bosnia and Herzegovina','DR Congo':'DR Congo'}
def nm(t): return ALIAS.get(t,t)
rows=[r for r in csv.DictReader(open(f'{P}\\data\\results_recent.csv',encoding='utf-8'))]
names={nm(t) for t in TEAMS}
h2h=defaultdict(int)
for r in rows:
    h,a=r['home_team'],r['away_team']
    if h in names and a in names:
        h2h[frozenset((h,a))]+=1
# only count pairs that could actually meet (same group OR could meet in KO = any pair)
pairs=list(combinations([nm(t) for t in TEAMS],2))
with3=[p for p in pairs if h2h[frozenset(p)]>=3]
with1=[p for p in pairs if h2h[frozenset(p)]>=1]
# group-stage pairs specifically (the 72 games' pairings)
gpairs=[]
for g,ts in GROUPS.items():
    for a,b in combinations(ts,2): gpairs.append((nm(a),nm(b)))
g_with_hist=[p for p in gpairs if h2h[frozenset(p)]>=1]
g_with3=[p for p in gpairs if h2h[frozenset(p)]>=3]
print(f'Among all {len(pairs)} possible pairs of the 48 WC teams (since 2021):')
print(f'  with >=1 direct meeting: {len(with1)} ({len(with1)/len(pairs)*100:.0f}%)')
print(f'  with >=3 direct meetings (enough to be a signal): {len(with3)} ({len(with3)/len(pairs)*100:.0f}%)')
print(f'\nOf the 66 actual group-stage matchups (the games we predict):')
print(f'  with any direct history since 2021: {len(g_with_hist)} of {len(gpairs)}')
print(f'  with >=3 meetings: {len(g_with3)}')
print('\nGroup pairs that DO have >=3 recent meetings:')
for p in g_with3: print('  ',' vs '.join(p),'->',h2h[frozenset(p)],'matches')
print('\nBelgium-Iran specifically:', h2h[frozenset(("Belgium","Iran"))], 'meetings since 2021')
