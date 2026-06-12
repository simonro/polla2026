"""Render the dark-theme HTML infographic: bracket (A/B toggle), group grids, edge panel."""
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
P = r'C:\Users\simon\Projects\pollawc2026'
A = json.load(open(f'{P}\\output\\picks_A.json', encoding='utf-8'))
B = json.load(open(f'{P}\\output\\picks_B.json', encoding='utf-8'))
C = json.load(open(f'{P}\\output\\picks_C.json', encoding='utf-8'))
E = json.load(open(f'{P}\\output\\edges.json', encoding='utf-8'))
sim = json.load(open(f'{P}\\output\\sim_results.json', encoding='utf-8'))['teams']
GROUPS = json.load(open(f'{P}\\data\\draw_verified.json', encoding='utf-8'))['groups']

CONF_COLOR = {'High':'#27c08a','Med':'#e0a33a','Low':'#d65a5a'}
def badge(c): return f'<span class="b" style="background:{CONF_COLOR[c]}22;color:{CONF_COLOR[c]};border:1px solid {CONF_COLOR[c]}55">{c}</span>'

def _slot(team, win, conf=None):
    edge = f' style="border-left:3px solid {CONF_COLOR[conf]}"' if (win and conf) else ''
    return f'<div class="sl {"win" if win else ""}"{edge}>{team or "&nbsp;"}</div>'
def _mbox(t1,t2,pick,conf):
    return f'<div class="mt">{_slot(t1,t1==pick,conf)}{_slot(t2,t2==pick,conf)}</div>'

def tracker_html(X):
    r32={m['m']:m for m in X['bracket']['round32']}
    r16={m['m']:m for m in X['bracket']['r16']}
    qf ={m['m']:m for m in X['bracket']['qf']}
    sf ={m['m']:m for m in X['bracket']['sf']}
    fn=X['bracket']['final']; champ=X['bracket']['champion']
    L={'r32':[74,77,73,75,83,84,81,82],'r16':[89,90,93,94],'qf':[97,98],'sf':[101]}
    R={'r32':[76,78,79,80,86,88,85,87],'r16':[91,92,95,96],'qf':[99,100],'sf':[102]}
    src={'r16':r16,'qf':qf,'sf':sf}
    def colhtml(nums, kind):
        bx=''
        for n in nums:
            if kind=='r32': m=r32[n]; bx+=_mbox(m['home'],m['away'],m['pick'],m['conf'])
            else: d=src[kind][n]; bx+=_mbox(d['a'],d['b'],d['pick'],d['conf'])
        return f'<div class="col c-{kind}">{bx}</div>'
    left =''.join(colhtml(L[k],k) for k in ('r32','r16','qf','sf'))
    right=''.join(colhtml(R[k],k) for k in ('r32','r16','qf','sf'))
    center=(f'<div class="center"><div class="finalbox"><div class="finlbl">Final</div>'
            f'{_slot(fn["a"],fn["a"]==champ,fn["conf"])}{_slot(fn["b"],fn["b"]==champ,fn["conf"])}</div>'
            f'<div class="champ2">🏆<br>{champ}</div></div>')
    return f'<div class="tracker"><div class="side left">{left}</div>{center}<div class="side right">{right}</div></div>'

def bracket_html(X):
    cols = []
    # column builder: list of (top, bottom, pick, conf)
    def col(title, items):
        rows = ''.join(
            f'<div class="tie"><div class="tm {"win" if it.get("pick")==it.get("t1") else ""}">{it["t1"] or "—"}</div>'
            f'<div class="tm {"win" if it.get("pick")==it.get("t2") else ""}">{it["t2"] or "—"}</div>'
            f'<div class="pk">{it["pick"] or ""} {badge(it["conf"]) if it.get("conf") else ""}</div></div>'
            for it in items)
        return f'<div class="bcol"><h4>{title}</h4>{rows}</div>'
    r32=[{'t1':m['home'],'t2':m['away'],'pick':m['pick'],'conf':m['conf']} for m in X['bracket']['round32']]
    r16=[{'t1':m['a'],'t2':m['b'],'pick':m['pick'],'conf':m['conf']} for m in X['bracket']['r16']]
    qf =[{'t1':m['a'],'t2':m['b'],'pick':m['pick'],'conf':m['conf']} for m in X['bracket']['qf']]
    sf =[{'t1':m['a'],'t2':m['b'],'pick':m['pick'],'conf':m['conf']} for m in X['bracket']['sf']]
    fn = X['bracket']['final']
    fin=[{'t1':fn['a'],'t2':fn['b'],'pick':fn['pick'],'conf':fn['conf']}]
    champ=f'<div class="bcol"><h4>Champion</h4><div class="champ">🏆 {X["bracket"]["champion"]}</div></div>'
    return ('<div class="bracket">'+col('Round of 32',r32)+col('Round of 16',r16)+col('Quarterfinals',qf)
            +col('Semifinals',sf)+col('Final',fin)+champ+'</div>')

def groups_html(X):
    cards=''
    by_group={}
    for m in X['group_picks']:
        by_group.setdefault(m['group'],[]).append(m)
    for g in GROUPS:
        st=X['standings'][g]
        rank=''.join(f'<tr><td>{i+1}</td><td>{t}</td><td class="elo">{sim[t]["elo"]}</td>'
                     f'<td>{"✅" if i<2 else ("◐" if i==2 else "")}</td></tr>' for i,t in enumerate(st))
        games=''.join(f'<div class="gm"><span>{m["home"]} <b>{m["score"][0]}–{m["score"][1]}</b> {m["away"]}</span>{badge(m["conf"])}</div>'
                      for m in by_group[g])
        cards+=(f'<div class="gcard"><h3>Group {g}</h3>'
                f'<table class="gt"><tr><th>#</th><th>Team</th><th>Elo</th><th></th></tr>{rank}</table>'
                f'<div class="games">{games}</div></div>')
    return cards

def edge_html():
    lev=''.join(f'<tr><td>{e["team"]}</td><td>{e["champ"]}%</td><td>{e["field"]}%</td>'
                f'<td class="{"good" if e["leverage"]>=1.1 else ""}">{e["leverage"]}×</td></tr>' for e in E['field_leverage'][:8])
    fad=''.join(f'<tr><td>{e["team"]}</td><td class="bad">{e["leverage"]}×</td></tr>' for e in E['fades'][:5])
    gap=''.join(f'<tr><td>{e["team"]}</td><td>{e["sim"]}%</td><td>{e["market"]}%</td>'
                f'<td class="{"bad" if abs(e["gap"])>5 else ""}">{e["gap"]:+}</td></tr>' for e in E['model_market_gaps'][:8])
    return f'''<div class="edges">
      <div class="ecard"><h3>⚡ Field-leverage (Entry B targets)</h3>
        <p class="sub">champ% ÷ field% — &gt;1 = under-picked by the 415, your edge.</p>
        <table><tr><th>Team</th><th>Champ</th><th>Field</th><th>Lev</th></tr>{lev}</table></div>
      <div class="ecard"><h3>🚫 Fades (over-crowded)</h3>
        <p class="sub">Field piles on; bad place to plant your flag.</p>
        <table><tr><th>Team</th><th>Lev</th></tr>{fad}</table></div>
      <div class="ecard"><h3>⚑ Model vs market gaps</h3>
        <p class="sub">Big gap = treat skeptically (usually model noise, not alpha).</p>
        <table><tr><th>Team</th><th>Sim</th><th>Mkt</th><th>Gap</th></tr>{gap}</table></div>
    </div>'''

HTML = f'''<!doctype html><html><head><meta charset="utf-8"><title>Polla WC2026 — Picks</title>
<style>
*{{box-sizing:border-box}} body{{margin:0;background:#0d1117;color:#e6edf3;font:14px/1.4 -apple-system,Segoe UI,Roboto,sans-serif}}
.wrap{{max-width:1500px;margin:0 auto;padding:24px}}
h1{{font-size:26px;margin:0 0 4px}} h2{{font-size:18px;color:#58a6ff;border-bottom:1px solid #21262d;padding-bottom:6px;margin:28px 0 14px}}
.tag{{color:#8b949e}} .pill{{display:inline-block;background:#1f6feb22;color:#58a6ff;border:1px solid #1f6feb55;border-radius:12px;padding:2px 10px;margin:2px;font-size:12px}}
.tabs{{margin:14px 0}} .tab{{display:inline-block;padding:8px 18px;background:#161b22;border:1px solid #30363d;border-radius:8px 8px 0 0;cursor:pointer;color:#8b949e}}
.tab.active{{background:#1f6feb22;color:#58a6ff;border-color:#1f6feb55}}
.view{{display:none}} .view.active{{display:block}}
.bracket{{display:flex;gap:14px;overflow-x:auto;padding:12px;background:#0a0e14;border:1px solid #21262d;border-radius:10px}}
.bcol{{min-width:170px}} .bcol h4{{color:#8b949e;font-size:12px;text-transform:uppercase;letter-spacing:.5px;margin:0 0 8px}}
.tie{{background:#161b22;border:1px solid #21262d;border-radius:8px;padding:7px;margin-bottom:8px}}
.tm{{color:#8b949e;font-size:13px;padding:1px 0}} .tm.win{{color:#e6edf3;font-weight:600}}
.pk{{margin-top:4px;padding-top:4px;border-top:1px dashed #30363d;font-size:12px;color:#58a6ff}}
.champ{{background:linear-gradient(135deg,#1f6feb33,#27c08a22);border:1px solid #58a6ff55;border-radius:8px;padding:18px 12px;font-size:18px;font-weight:700;text-align:center}}
.b{{font-size:10px;padding:1px 6px;border-radius:10px;margin-left:4px}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}
.gcard{{background:#161b22;border:1px solid #21262d;border-radius:10px;padding:12px}}
.gcard h3{{margin:0 0 8px;font-size:15px}} .gt{{width:100%;border-collapse:collapse;font-size:12px;margin-bottom:8px}}
.gt th{{color:#8b949e;text-align:left;font-weight:500;border-bottom:1px solid #21262d}} .gt td{{padding:2px 0}} .elo{{color:#8b949e}}
.gm{{display:flex;justify-content:space-between;align-items:center;font-size:12px;padding:3px 0;border-top:1px solid #0d1117}}
.edges{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}
.ecard{{background:#161b22;border:1px solid #21262d;border-radius:10px;padding:14px}} .ecard h3{{margin:0 0 2px;font-size:14px}}
.sub{{color:#8b949e;font-size:11px;margin:0 0 8px}} .ecard table{{width:100%;border-collapse:collapse;font-size:12px}}
.ecard th{{color:#8b949e;text-align:left;font-weight:500}} .ecard td{{padding:3px 0;border-top:1px solid #0d1117}}
.good{{color:#27c08a;font-weight:600}} .bad{{color:#d65a5a;font-weight:600}}
.note{{background:#e0a33a11;border:1px solid #e0a33a44;border-radius:8px;padding:10px 14px;color:#e0a33a;font-size:13px;margin:10px 0}}
/* ---- scoreboard ---- */
.sb-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:20px}}
.sb-card{{background:#161b22;border:1px solid #21262d;border-radius:10px;padding:16px;text-align:center}}
.sb-card h3{{margin:0 0 4px;font-size:16px;color:#58a6ff}}.sb-card .sb-champ{{font-size:12px;color:#8b949e;margin-bottom:12px}}
.sb-total{{font-size:36px;font-weight:700;color:#e6edf3;line-height:1}}.sb-max{{font-size:12px;color:#8b949e;margin-top:2px}}
.sb-bar-wrap{{background:#0d1117;border-radius:4px;height:6px;margin:10px 0 8px;overflow:hidden}}
.sb-bar{{height:100%;border-radius:4px;background:#1f6feb;transition:width .4s}}
.sb-rounds{{width:100%;border-collapse:collapse;font-size:11px;text-align:left;margin-top:6px}}
.sb-rounds td{{padding:2px 0;border-top:1px solid #0d1117;color:#8b949e}}.sb-rounds td:last-child{{text-align:right;color:#e6edf3}}
.sb-matches{{margin-top:18px}}.sb-matches h3{{font-size:14px;color:#8b949e;margin:0 0 8px;text-transform:uppercase;letter-spacing:.5px}}
.sm-row{{display:flex;justify-content:space-between;align-items:center;padding:6px 10px;border-radius:6px;margin-bottom:4px;background:#161b22;font-size:12px}}
.sm-hit{{border-left:3px solid #27c08a}}.sm-miss{{border-left:3px solid #d65a5a}}.sm-hit .sm-badge{{color:#27c08a}}.sm-miss .sm-badge{{color:#d65a5a}}
.sb-div{{margin-top:20px}}.sb-div h3{{font-size:14px;color:#8b949e;margin:0 0 8px;text-transform:uppercase;letter-spacing:.5px}}
.div-table{{width:100%;border-collapse:collapse;font-size:12px}}
.div-table th{{color:#8b949e;font-weight:500;padding:4px 8px;text-align:left;border-bottom:1px solid #21262d}}
.div-table td{{padding:5px 8px;border-top:1px solid #0d1117}}
.div-win{{color:#27c08a;font-weight:700}}.div-loss{{color:#d65a5a}}.div-pending{{color:#8b949e}}
.sb-loading{{color:#8b949e;font-size:14px;padding:40px 0;text-align:center}}
.sb-leader{{display:inline-block;background:#27c08a22;color:#27c08a;border:1px solid #27c08a55;border-radius:12px;padding:2px 10px;font-size:12px;margin-left:6px}}
.gsh{{color:#58a6ff;font-size:15px;margin:18px 0 10px;border-top:1px solid #21262d;padding-top:12px}}
/* ---- guide ---- */
.guide{{background:#0d1117;border:1px solid #21262d;border-radius:12px;margin-bottom:14px}}
.glead{{padding:14px 16px;color:#e6edf3;font-size:14px;border-bottom:1px solid #1b2027;background:#11161d;border-radius:12px 12px 0 0}}
.step{{display:flex;gap:14px;padding:13px 16px;border-bottom:1px solid #1b2027}}
.step:last-child{{border-bottom:none}}
.snum{{flex:0 0 28px;height:28px;border-radius:50%;background:#1f6feb22;color:#58a6ff;border:1px solid #1f6feb55;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px}}
.sbody h4{{margin:1px 0 4px;font-size:14.5px;color:#e6edf3}}
.sbody p{{margin:0;color:#aeb6c0;font-size:13px;line-height:1.55}}
.sbody b{{color:#e6edf3}} .gk{{color:#27c08a;font-weight:600}} .gx{{color:#d65a5a;font-weight:600}}
.callout{{padding:13px 16px;border-bottom:1px solid #1b2027}}
.callout h4{{margin:0 0 6px;font-size:14.5px;color:#e0a33a}}
.callout p{{margin:0 0 4px;color:#aeb6c0;font-size:13px;line-height:1.55}}
/* ---- converging bracket tracker ---- */
:root{{--g:#3a6e2f}}
.tracker{{display:flex;align-items:stretch;justify-content:center;background:#060a06;border:1px solid #1d3a1d;border-radius:12px;padding:18px 14px;overflow-x:auto;margin-bottom:14px}}
.side{{display:flex;flex:1;gap:14px}} .side.right{{flex-direction:row-reverse}}
.col{{display:flex;flex-direction:column;justify-content:space-around;flex:1;gap:8px;min-width:92px}}
.mt{{position:relative;display:flex;flex-direction:column;justify-content:center;flex:1}}
.sl{{background:#0d1411;border:1px solid #1f3d22;border-radius:4px;padding:4px 6px;margin:1px 0;font-size:11px;color:#7da06f;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.sl.win{{background:#1a3d12;color:#a6f56a;font-weight:600;border-color:#4caf3a}}
.side.left .col:not(.c-sf) .mt::before{{content:'';position:absolute;right:-14px;top:50%;width:14px;height:2px;background:var(--g)}}
.side.left .col:not(.c-sf) .mt:nth-child(odd)::after{{content:'';position:absolute;right:-14px;top:50%;width:2px;height:calc(100% + 8px);background:var(--g)}}
.side.right .col:not(.c-sf) .mt::before{{content:'';position:absolute;left:-14px;top:50%;width:14px;height:2px;background:var(--g)}}
.side.right .col:not(.c-sf) .mt:nth-child(odd)::after{{content:'';position:absolute;left:-14px;top:50%;width:2px;height:calc(100% + 8px);background:var(--g)}}
.center{{display:flex;flex-direction:column;justify-content:center;align-items:center;min-width:150px;padding:0 8px}}
.finalbox{{width:100%}} .finlbl{{color:#8b949e;font-size:11px;text-transform:uppercase;letter-spacing:.5px;text-align:center;margin-bottom:6px}}
.champ2{{margin-top:14px;background:linear-gradient(135deg,#1a3d12,#2a5d1a);border:1px solid #4caf3a;border-radius:10px;padding:14px 10px;text-align:center;font-weight:700;color:#a6f56a;font-size:16px;width:100%}}
</style></head><body><div class="wrap">
<h1>⚽ Polla World Cup 2026 — Model Picks</h1>
<div class="tag">Elo-anchored Dixon-Coles + market-blended Monte Carlo (30k sims) · field ~415 · 2 entries · data through 2026-06-07</div>
<div style="margin-top:10px">
  <span class="pill">3 distinct champions → A: {A['bracket']['champion']}</span>
  <span class="pill">B: {B['bracket']['champion']} (+Portugal→SF)</span>
  <span class="pill">C: {C['bracket']['champion']} (3-source, best single)</span>
  <span class="pill">Fade Brazil 0.21× &amp; Latino over-picks</span>
</div>

<div class="note">⚑ <b>Bracket correction (Jun 12):</b> the R32 match-number map was rebuilt verbatim from FIFA.com. The original ESPN-derived numbering had several matches swapped, which mis-routed the R16+ tree (it produced a Brazil vs Spain semifinal that is impossible in the real bracket). True routing: <b>Germany vs France in the Round of 16 (M89)</b>; Brazil's half runs through England (QF M99); Spain's semifinal opponent comes from the France/Netherlands side. Champions unchanged (A England / B France / C Spain). Picks below reflect the TRUE bracket. <b>Compare against what was actually submitted on Jun 9; the submitted CSVs are preserved as entry_X_submitted_jun9.csv.</b></div>

<h2 id="guide">📖 How this works — a guide you can explain to anyone</h2>
<div class="guide">
  <div class="glead"><b>The goal isn't to predict games — it's to win a 415-person pool.</b> Being right isn't enough; you have to be right about things most people got <i>wrong</i>. So every team is judged two ways: how likely it is to win, and how many rivals also picked it.</div>
  <div class="step"><div class="snum">1</div><div class="sbody"><h4>Rate every team — from 3 sources</h4><p><b>Elo</b> (a power rating updated after every match) + <b>common-opponent</b> strength (who-beat-whom across the whole results web) + the <b>betting market</b> (the sharpest public estimate). We blend all three. They agree ~95% of the time; the disagreements are where it gets interesting.</p></div></div>
  <div class="step"><div class="snum">2</div><div class="sbody"><h4>Adjust for injuries</h4><p>We read the June 6 injury report and docked teams for missing stars. <b>Brazil</b> got hit hardest (Rodrygo and Estêvão out, Neymar doubtful).</p></div></div>
  <div class="step"><div class="snum">3</div><div class="sbody"><h4>Predict each game</h4><p>From two teams' ratings we get each side's <b>expected goals</b>, then a probability for every possible score. Quirk: a favorite's most-likely <i>exact</i> score is often a draw or 1-0 — because low scores bunch up — even when they're clearly favored to win.</p></div></div>
  <div class="step"><div class="snum">4</div><div class="sbody"><h4>Simulate the tournament 30,000 times</h4><p>Play all 104 games with those probabilities, over and over, on the real 2026 bracket. Count how often each team wins it all. That's each team's <b>win % (p)</b>.</p></div></div>
  <div class="step"><div class="snum">5</div><div class="sbody"><h4>Model the field</h4><p>Estimate what the other 415 will pick. This pool runs out of <b>Miami / New York / Bogotá</b> — a Latino-heavy crowd — so Argentina, Brazil, Colombia and Mexico are heavily over-picked. That's each team's <b>field % (f)</b>.</p></div></div>
  <div class="step"><div class="snum">6</div><div class="sbody"><h4>Pick for value, not fame</h4><p>The deciding number is <b>leverage = win % ÷ field %</b>. <span class="gk">Above 1 = undervalued</span> (more rivals would let you win it outright). <span class="gx">Below 1 = over-crowded</span> (you'd split the prize). This is what tells us to <b>fade Brazil</b>: great reputation, but injured, ~3% to win, yet ~13% of the field picks it → leverage 0.21.</p></div></div>
  <div class="callout"><h4>Why three entries with three different champions</h4><p>We rank the strong, undervalued teams and put a <b>different winner on each ticket</b> — three shots at the 30-point champion instead of tripling down on one.</p>
  <p><b>C → Spain:</b> highest win % <i>and</i> most undervalued (2.6×). The best single bet.<br>
  <b>B → France:</b> second-best, a strong independent second shot.<br>
  <b>A → England:</b> third — covers one more outcome.</p></div>
  <div class="callout"><h4>What we deliberately ignore — and the honest limits</h4><p>Exact group scores are near-random for everyone (~10% hit rate), so they don't separate you — the pool is won <b>deep in the bracket</b> (semis, final, champion). No model reliably beats the market, so we lean on it. The field estimate is our best guess, not real data (picks stay hidden until June 10). Upsets happen — which is exactly why we spread across three entries.</p></div>
</div>

<h2>Knockout bracket</h2>
<div class="tabs">
<span class="tab" id="tabSB" onclick="sw('SB')">📊 Scoreboard</span>
<span class="tab active" id="tabA" onclick="sw('A')">Entry A — {A['bracket']['champion']} champion (Euro value)</span>
<span class="tab" id="tabB" onclick="sw('B')">Entry B — {B['bracket']['champion']} champion (+Portugal→SF)</span>
<span class="tab" id="tabC" onclick="sw('C')">Entry C — {C['bracket']['champion']} champion (3-source, best single)</span>
</div>
<div id="SB" class="view"><div id="sb-root"><div class="sb-loading">Loading scores…</div></div></div>
<div id="A" class="view active">{tracker_html(A)}<details><summary class="tag">Detailed picks + confidence (Entry A)</summary>{bracket_html(A)}</details><h3 class="gsh">Group stage — Entry A standings &amp; scores</h3><div class="grid">{groups_html(A)}</div></div>
<div id="B" class="view">{tracker_html(B)}<details><summary class="tag">Detailed picks + confidence (Entry B)</summary>{bracket_html(B)}</details><h3 class="gsh">Group stage — Entry B standings &amp; scores</h3><div class="grid">{groups_html(B)}</div></div>
<div id="C" class="view">{tracker_html(C)}<details><summary class="tag">Detailed picks + confidence (Entry C)</summary>{bracket_html(C)}</details><h3 class="gsh">Group stage — Entry C standings &amp; scores (note: Germany 1st in Group E)</h3><div class="grid">{groups_html(C)}</div></div>

<h2>The edge — where the contest is won</h2>
{edge_html()}


<p class="tag" style="margin-top:24px">Confidence = prob margin + cross-source agreement. ✅ advance · ◐ third-place (best 8 qualify). Scores are the most-probable Dixon-Coles scoreline per match. Not betting advice.</p>
</div>
<script>
function sw(v){{
  for(const id of ['SB','A','B','C']){{
    document.getElementById(id).classList.toggle('active',id===v);
    document.getElementById('tab'+id).classList.toggle('active',id===v);
  }}
  if(v==='SB' && !window._sbLoaded) loadSB();
}}

function loadSB(){{
  window._sbLoaded = true;
  fetch('scores.json?t='+Date.now())
    .then(r=>r.json()).then(renderSB)
    .catch(()=>{{document.getElementById('sb-root').innerHTML='<div class="sb-loading">scores.json not found — run python score_update.py then push.</div>';}});
}}

function renderSB(d){{
  const ROUNDS=[['group','Group stage',144],['round32','Round of 32',32],['r16','Round of 16',32],
                ['qf','Quarterfinals',32],['sf','Semifinals',32],['final','Final',24],['champion','Champion',30]];
  const total=358;
  const entries=['A','B','C'];
  const maxTotal=d.scores.A.total;  // same scale for all
  const leader=entries.reduce((best,t)=>d.scores[t].total>d.scores[best].total?t:best,'A');
  const champs={{A:'{A['bracket']['champion']}',B:'{B['bracket']['champion']}',C:'{C['bracket']['champion']}'}};

  let cards='';
  for(const t of entries){{
    const s=d.scores[t]; const pct=Math.round(s.total/total*100);
    const isLead=t===leader&&s.total>0;
    const rows=ROUNDS.map(([k,label,mx])=>s[k]?`<tr><td>${{label}}</td><td>${{s[k]}}/${{mx}}</td></tr>`:'').join('');
    cards+=`<div class="sb-card">
      <h3>Entry ${{t}}${{isLead?'<span class="sb-leader">leading</span>':''}}</h3>
      <div class="sb-champ">Champion pick: <b>${{champs[t]}}</b></div>
      <div class="sb-total">${{s.total}}</div><div class="sb-max">/ ${{total}} pts</div>
      <div class="sb-bar-wrap"><div class="sb-bar" style="width:${{pct}}%"></div></div>
      ${{rows?`<table class="sb-rounds">${{rows}}</table>`:''}}
    </div>`;
  }}

  let matchRows='';
  if(d.completed_matches.length===0){{
    matchRows='<div style="color:#8b949e;font-size:13px;padding:8px 0">No group stage results yet.</div>';
  }} else {{
    for(const m of d.completed_matches){{
      const hit=m.hit;
      matchRows+=`<div class="sm-row ${{hit?'sm-hit':'sm-miss'}}">
        <span>${{m.home}} ${{m.actual[0]}}-${{m.actual[1]}} ${{m.away}}</span>
        <span>pick ${{m.pick[0]}}-${{m.pick[1]}} <b class="sm-badge">${{hit?'✓':'✗'}}</b></span>
      </div>`;
    }}
  }}

  let divRows='';
  for(const row of d.divergence){{
    const act=row.actual;
    const cells=['A','B','C'].map(t=>{{
      if(!act) return `<td class="div-pending">${{row[t]}}</td>`;
      return `<td class="${{row[t]===act?'div-win':'div-loss'}}">${{row[t]}}</td>`;
    }}).join('');
    const actCell=act?`<td class="div-win">${{act}}</td>`:`<td class="div-pending">—</td>`;
    divRows+=`<tr><td>${{row.label}}</td>${{cells}}${{actCell}}</tr>`;
  }}

  document.getElementById('sb-root').innerHTML=`
    <p style="color:#8b949e;font-size:12px;margin:0 0 14px">Updated ${{d.updated}} · ${{d.matches_played}}/${{d.total_group}} group matches played</p>
    <div class="sb-grid">${{cards}}</div>
    <div class="sb-matches"><h3>Group stage results vs picks</h3>${{matchRows}}</div>
    <div class="sb-div"><h3>Key divergence picks (where A/B/C differ)</h3>
      <table class="div-table"><thead><tr><th>Round</th><th>Entry A</th><th>Entry B</th><th>Entry C</th><th>Actual</th></tr></thead>
      <tbody>${{divRows}}</tbody></table>
      <p style="color:#8b949e;font-size:11px;margin:8px 0 0">Green = correct. Entries diverge only from QF onwards — group stage and R32/R16 picks are identical across all three.</p>
    </div>`;
}}
</script></body></html>'''

open(f'{P}\\output\\report.html','w',encoding='utf-8').write(HTML)
print('Wrote output/report.html (%d KB)'%(len(HTML)//1024))
