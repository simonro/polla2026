"""
WC2026 Polla Score Tracker
==========================
Computes running points for Entries A, B, C as the tournament progresses.

UPDATING RESULTS:
  Group stage: edit data/wc2026_fixtures.csv — replace NA with actual scores.
  KO rounds:   edit data/ko_results.json — add the winning team name per match number.
                 "r32": {"73": "Brazil", "74": "Germany", ...}
                 "r16": {"89": "Spain", ...}
                 "qf": {"97": "Spain", ...}
                 "sf": {"101": "Spain", ...}
                 "final": "Spain",
                 "champion": "Spain"

Run: python score_tracker.py
"""
import json, csv, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

P = r'C:\Users\simon\Projects\pollawc2026'

# ---- scoring weights per round -----------------------------------------
PTS = {'round32': 1, 'r16': 2, 'qf': 4, 'sf': 8, 'final': 12, 'champion': 30}
GROUP_EXACT_PTS = 2

# ---- load picks -----------------------------------------------------------
picks = {}
for tag in ('A', 'B', 'C'):
    picks[tag] = json.load(open(f'{P}\\output\\picks_{tag}.json', encoding='utf-8'))

# ---- load actual group stage results from fixtures CSV --------------------
group_results = {}  # (home, away) -> (home_score, away_score) or None
with open(f'{P}\\data\\wc2026_fixtures.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        h, a = row['home_team'], row['away_team']
        hs, as_ = row['home_score'], row['away_score']
        if hs != 'NA' and as_ != 'NA':
            group_results[(h, a)] = (int(hs), int(as_))

# ---- load KO results ------------------------------------------------------
ko = json.load(open(f'{P}\\data\\ko_results.json', encoding='utf-8'))

# ---- compute scores -------------------------------------------------------
scores = {tag: {'group': 0, 'round32': 0, 'r16': 0, 'qf': 0, 'sf': 0, 'final': 0, 'champion': 0}
          for tag in ('A', 'B', 'C')}

# Group stage (same picks for all entries — score is shared but computed per entry for clarity)
for tag in ('A', 'B', 'C'):
    for m in picks[tag]['group_picks']:
        actual = group_results.get((m['home'], m['away']))
        if actual is not None:
            ph, pa = m['score']
            if (ph, pa) == actual:
                scores[tag]['group'] += GROUP_EXACT_PTS

# KO rounds
for rnd in ('round32', 'r16', 'qf', 'sf'):
    actual_rnd = ko.get(rnd, {})
    for tag in ('A', 'B', 'C'):
        for m in picks[tag]['bracket'][rnd]:
            mn = str(m['m'])
            if mn in actual_rnd:
                if actual_rnd[mn] == m['pick']:
                    scores[tag][rnd] += PTS[rnd]

# Final (2 finalists)
if ko.get('final'):
    actual_finalist = ko['final']  # single winner (champion pick)
    # final has two finalists — check if our pick matches actual champion
    for tag in ('A', 'B', 'C'):
        f = picks[tag]['bracket']['final']
        # both finalists score 12 pts if picked correctly; we only know the champion at final
        # treat final the same as champion check for now
        if f['pick'] == ko.get('final'):
            scores[tag]['final'] += PTS['final']

# Champion
if ko.get('champion'):
    for tag in ('A', 'B', 'C'):
        if picks[tag]['bracket']['champion'] == ko['champion']:
            scores[tag]['champion'] += PTS['champion']

# ---- totals ---------------------------------------------------------------
for tag in ('A', 'B', 'C'):
    scores[tag]['total'] = sum(v for k, v in scores[tag].items() if k != 'total')

# ---- what each entry picked for the key divergence points -----------------
def entry_ko(tag):
    b = picks[tag]['bracket']
    qf_99 = next(m for m in b['qf'] if m['m'] == 99)
    qf_100 = next(m for m in b['qf'] if m['m'] == 100)
    sf_102 = next(m for m in b['sf'] if m['m'] == 102)
    return qf_99['pick'], qf_100['pick'], sf_102['pick'], b['final']['pick'], b['champion']

# ---- display --------------------------------------------------------------
rnd_names = ['group', 'round32', 'r16', 'qf', 'sf', 'final', 'champion']
max_pts   = {'group': 144, 'round32': 32, 'r16': 32, 'qf': 32, 'sf': 32, 'final': 24, 'champion': 30}

completed_group = len(group_results)
completed_ko = {r: len(ko.get(r, {})) for r in ('round32', 'r16', 'qf', 'sf')}

print('=' * 64)
print('  WC2026 POLLA SCORE TRACKER')
print('=' * 64)
print(f'  Group stage: {completed_group}/72 matches played')
for r in ('round32', 'r16', 'qf', 'sf'):
    tot = {'round32': 32, 'r16': 16, 'qf': 8, 'sf': 4}[r]
    print(f'  {r.upper()}: {completed_ko[r]}/{tot} results logged')
print()

# Score table
hdr = f"{'Round':<12} {'Max':>5}  {'A':>6} {'B':>6} {'C':>6}"
print(hdr)
print('-' * len(hdr))
for rnd in rnd_names:
    mx = max_pts[rnd]
    a = scores['A'][rnd]; b = scores['B'][rnd]; c_s = scores['C'][rnd]
    diff_marker = '*' if not (a == b == c_s) else ' '
    print(f"{diff_marker}{rnd:<11} {mx:>5}  {a:>6} {b:>6} {c_s:>6}")
print('-' * len(hdr))
a = scores['A']['total']; b = scores['B']['total']; c_s = scores['C']['total']
leader = 'A' if a >= b and a >= c_s else ('B' if b >= c_s else 'C')
print(f" {'TOTAL':<11} {'358':>5}  {a:>6} {b:>6} {c_s:>6}   <-- leader: {leader}")

print()
print('KEY DIVERGENCE PICKS (where A/B/C differ):')
print(f"{'Round/Match':<20} {'A':>18} {'B':>18} {'C':>18}")
print('-' * 76)
qa, ra, sa, fa, cha = entry_ko('A')
qb, rb, sb, fb, chb = entry_ko('B')
qc, rc, sc, fc, chc = entry_ko('C')
print(f"{'QF M99':<20} {qa:>18} {qb:>18} {qc:>18}")
print(f"{'QF M100':<20} {ra:>18} {rb:>18} {rc:>18}")
print(f"{'SF M102':<20} {sa:>18} {sb:>18} {sc:>18}")
print(f"{'Final pick':<20} {fa:>18} {fb:>18} {fc:>18}")
print(f"{'CHAMPION':<20} {cha:>18} {chb:>18} {chc:>18}")

if completed_group == 0 and not any(ko.get(r) for r in ('round32','r16','qf','sf','final','champion')):
    print()
    print('  No results logged yet. Update data/wc2026_fixtures.csv and data/ko_results.json.')
