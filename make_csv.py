"""Write a copy-down entry sheet per entry, laid out to match pollaworldcup.com sections."""
import json, csv, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
P = r'C:\Users\simon\Projects\pollawc2026'
GROUPS = json.load(open(f'{P}\\data\\draw_verified.json', encoding='utf-8'))['groups']

def write_entry(tag):
    X = json.load(open(f'{P}\\output\\picks_{tag}.json', encoding='utf-8'))
    rows = []
    rows.append(['== GROUP STAGE: exact scores (2 pts each) =='])
    by_g = {}
    for m in X['group_picks']: by_g.setdefault(m['group'], []).append(m)
    for g in GROUPS:
        for m in by_g[g]:
            rows.append([f'Group {g}', m['home'], f"{m['score'][0]}-{m['score'][1]}", m['away'], m['conf']])
    rows.append([])
    rows.append(['== GROUP STANDINGS (1st / 2nd / 3rd) =='])
    for g in GROUPS:
        st = X['standings'][g]
        rows.append([f'Group {g}', '1st: '+st[0], '2nd: '+st[1], '3rd: '+st[2]])
    rows.append([])
    rows.append(['== BEST 8 THIRD-PLACE (ranked) ==', *X['best8_thirds']])
    rows.append([])
    rows.append(['== ROUND OF 32 winners (16) =='])
    for m in X['bracket']['round32']:
        rows.append([f"M{m['m']}", m['home'], 'vs', m['away'], '-> '+str(m['pick']), m['conf']])
    rows.append([])
    rows.append(['== ROUND OF 16 winners (8) =='])
    for m in X['bracket']['r16']:
        rows.append([f"M{m['m']}", m['a'], 'vs', m['b'], '-> '+str(m['pick']), m['conf']])
    rows.append([])
    rows.append(['== QUARTERFINALS winners (4) =='])
    for m in X['bracket']['qf']:
        rows.append([f"M{m['m']}", m['a'], 'vs', m['b'], '-> '+str(m['pick']), m['conf']])
    rows.append([])
    rows.append(['== SEMIFINALS winners (2 = finalists) =='])
    for m in X['bracket']['sf']:
        rows.append([f"M{m['m']}", m['a'], 'vs', m['b'], '-> '+str(m['pick']), m['conf']])
    fn = X['bracket']['final']
    rows.append([])
    rows.append(['== FINAL ==', fn['a'], 'vs', fn['b'], '-> '+str(fn['pick'])])
    rows.append(['== CHAMPION (30 pts) ==', X['bracket']['champion']])
    with open(f'{P}\\output\\entry_{tag}.csv', 'w', newline='', encoding='utf-8-sig') as f:
        csv.writer(f).writerows(rows)
    print(f'Wrote entry_{tag}.csv ({len(rows)} rows) — champion {X["bracket"]["champion"]}')

write_entry('A'); write_entry('B'); write_entry('C')
