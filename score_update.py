"""
Generate scores.json for the GitHub Pages scoreboard.
Run after updating data/wc2026_fixtures.csv or data/ko_results.json.

  python score_update.py
  git add scores.json && git commit -m "scores update" && git push
"""
import json, csv, io, sys
from datetime import date
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

P = r'C:\Users\simon\Projects\pollawc2026'
PTS = {'round32': 1, 'r16': 2, 'qf': 4, 'sf': 8, 'final': 12, 'champion': 30}
MAX = {'group': 144, 'round32': 32, 'r16': 32, 'qf': 32, 'sf': 32, 'final': 24, 'champion': 30}

picks = {tag: json.load(open(f'{P}\\output\\picks_{tag}.json', encoding='utf-8'))
         for tag in ('A', 'B', 'C')}
ko = json.load(open(f'{P}\\data\\ko_results.json', encoding='utf-8'))

# group stage results from fixtures CSV
group_results = {}
with open(f'{P}\\data\\wc2026_fixtures.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        h, a, hs, as_ = row['home_team'], row['away_team'], row['home_score'], row['away_score']
        if hs != 'NA' and as_ != 'NA':
            group_results[(h, a)] = (int(hs), int(as_))

# compute scores
scores = {tag: {k: 0 for k in ('group', 'round32', 'r16', 'qf', 'sf', 'final', 'champion')}
          for tag in ('A', 'B', 'C')}

for tag in ('A', 'B', 'C'):
    for m in picks[tag]['group_picks']:
        actual = group_results.get((m['home'], m['away']))
        if actual and (m['score'][0], m['score'][1]) == actual:
            scores[tag]['group'] += 2

for rnd in ('round32', 'r16', 'qf', 'sf'):
    actual_rnd = ko.get(rnd, {})
    for tag in ('A', 'B', 'C'):
        for m in picks[tag]['bracket'][rnd]:
            if str(m['m']) in actual_rnd and actual_rnd[str(m['m'])] == m['pick']:
                scores[tag][rnd] += PTS[rnd]

if ko.get('final'):
    for tag in ('A', 'B', 'C'):
        if picks[tag]['bracket']['final']['pick'] == ko['final']:
            scores[tag]['final'] += PTS['final']

if ko.get('champion'):
    for tag in ('A', 'B', 'C'):
        if picks[tag]['bracket']['champion'] == ko['champion']:
            scores[tag]['champion'] += PTS['champion']

for tag in ('A', 'B', 'C'):
    scores[tag]['total'] = sum(scores[tag][k] for k in MAX)

# completed group stage match details
completed_matches = []
for m in picks['A']['group_picks']:
    actual = group_results.get((m['home'], m['away']))
    if actual:
        ph, pa = m['score']
        completed_matches.append({
            'group': m['group'],
            'home': m['home'], 'away': m['away'],
            'pick': [ph, pa],
            'actual': list(actual),
            'hit': (ph, pa) == actual
        })

# divergence picks and actual outcomes
divs = [
    {'label': 'QF M99',   'match': 99,  'rnd': 'qf'},
    {'label': 'QF M100',  'match': 100, 'rnd': 'qf'},
    {'label': 'SF M102',  'match': 102, 'rnd': 'sf'},
]
divergence = []
for d in divs:
    row = {'label': d['label']}
    for tag in ('A', 'B', 'C'):
        m = next((x for x in picks[tag]['bracket'][d['rnd']] if x['m'] == d['match']), None)
        row[tag] = m['pick'] if m else '?'
    actual_rnd = ko.get(d['rnd'], {})
    row['actual'] = actual_rnd.get(str(d['match']))
    divergence.append(row)

# final / champion rows
final_row = {'label': 'Final pick'}
for tag in ('A', 'B', 'C'):
    final_row[tag] = picks[tag]['bracket']['final']['pick']
final_row['actual'] = ko.get('final')
divergence.append(final_row)

champ_row = {'label': 'Champion'}
for tag in ('A', 'B', 'C'):
    champ_row[tag] = picks[tag]['bracket']['champion']
champ_row['actual'] = ko.get('champion')
divergence.append(champ_row)

out = {
    'updated': str(date.today()),
    'matches_played': len(completed_matches),
    'total_group': 72,
    'scores': scores,
    'max': MAX,
    'completed_matches': completed_matches,
    'ko_results': ko,
    'divergence': divergence
}

out_path = f'{P}\\scores.json'
json.dump(out, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'Wrote scores.json  ({len(completed_matches)}/72 group matches, scores A={scores["A"]["total"]} B={scores["B"]["total"]} C={scores["C"]["total"]})')
