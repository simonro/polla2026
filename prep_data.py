import csv, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

rows = list(csv.DictReader(open(r'data\results_full.csv', encoding='utf-8')))

def is_num(x):
    try:
        int(x); return True
    except: return False

# Completed matches 2021+ for Dixon-Coles fit
recent = [r for r in rows if r['date'] >= '2021-01-01' and is_num(r['home_score']) and is_num(r['away_score'])]
with open(r'data\results_recent.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(recent)
print('completed matches 2021+:', len(recent), 'latest:', max(r['date'] for r in recent))

# 2026 World Cup fixtures (scheduled, scores NA)
wc = [r for r in rows if r['date'] >= '2026-06-01' and 'World Cup' in r['tournament'] and not is_num(r['home_score'])]
print('2026 WC scheduled fixtures:', len(wc))
# how many have both teams as real (group stage) vs placeholders
from collections import Counter
print('sample fixtures:')
for r in wc[:6]:
    print(' ', r['date'], r['home_team'], 'vs', r['away_team'], '@', r['city'], r['country'])
with open(r'data\wc2026_fixtures.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(wc)

# tournament-type weights present in recent data
print('tournaments in recent (top):')
for t, c in Counter(r['tournament'] for r in recent).most_common(12):
    print(f'  {c:5d}  {t}')
