"""Blend Elo-sim with market; build field model; compare market-leaning vs even blends."""
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
P = r'C:\Users\simon\Projects\pollawc2026'
TAG = sys.argv[1] if len(sys.argv) > 1 else ''
SUF = f'_{TAG}' if TAG else ''
sim = json.load(open(f'{P}\\output\\sim_results{SUF}.json', encoding='utf-8'))['teams']
mkt = json.load(open(f'{P}\\data\\market_odds.json', encoding='utf-8'))['kalshi_champion_pct']

TEAMS = list(sim.keys())
sim_ch = {t: sim[t]['CH'] for t in TEAMS}
ssum = sum(sim_ch.values()) or 1
sim_ch = {t: v/ssum for t,v in sim_ch.items()}

# ---- full 48-team market champion distribution: pin explicit top-5, spread remainder by sim shape
mkt_top = {t: mkt[t]/100 for t in mkt if t in sim}
rem = max(0.0, 1 - sum(mkt_top.values()))
rest = [t for t in TEAMS if t not in mkt_top]
rsum = sum(sim_ch[t] for t in rest) or 1
mkt_ch = {t: mkt_top.get(t, rem*sim_ch[t]/rsum) for t in TEAMS}
ms = sum(mkt_ch.values()); mkt_ch = {t: v/ms for t,v in mkt_ch.items()}

def blend(w_mkt):
    b = {t: w_mkt*mkt_ch[t] + (1-w_mkt)*sim_ch[t] for t in TEAMS}
    s = sum(b.values()); return {t: v/s for t,v in b.items()}

ml = blend(0.65)      # market-leaning
ev = blend(0.50)      # even

# ---- field model: hand-estimated casual CHAMPION-pick distribution for THIS pool.
# Decoupled from our win model on purpose: casual pickers go on fame/narrative, NOT injuries or Elo.
# This Polla runs out of Miami / New York / Bogota (contest contacts) -> Latino-heavy entrant base,
# so South American giants + hosts are heavily over-picked. That is the core field-leverage edge.
FIELD_PRIOR = {'Argentina':16,'Brazil':15,'Spain':9,'France':9,'England':7,'Colombia':7,
               'Mexico':6,'Portugal':6,'Germany':5,'Uruguay':4,'United States':4,
               'Netherlands':3,'Ecuador':3}
DEF = 0.6   # everyone else: small uniform reputation weight
_raw = {t: FIELD_PRIOR.get(t, DEF) for t in TEAMS}
_s = sum(_raw.values()); fld = {t: _raw[t]/_s for t in TEAMS}

def show(name, b):
    print(f'\n=== {name} ===')
    print(f'{"Team":22s} {"champ%":>7s} {"field%":>7s} {"leverage":>8s}  {"SF%":>6s}')
    for t in sorted(TEAMS, key=lambda x:-b[x])[:14]:
        lev = b[t]/fld[t] if fld[t] else 0
        print(f'{t:22s} {b[t]*100:6.1f}% {fld[t]*100:6.1f}% {lev:7.2f}x  {sim[t]["SF"]*100:5.1f}%')

show('MARKET-LEANING blend (65% mkt / 35% sim)', ml)
show('EVEN blend (50/50)', ev)

print('\nleverage = champ% / field% .  >1 = UNDER-picked by the field (contrarian value for Entry B).')
print('<1 = over-crowded (everyone piles on; bad place to plant your flag).')

json.dump({'market_leaning':ml,'even':ev,'field':fld,'market_full':mkt_ch,'sim_ch':sim_ch},
          open(f'{P}\\output\\blends{SUF}.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
