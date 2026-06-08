"""Artifact audit: re-score A/B picks (Elo+injuries) against the corrected 3-source ratings (C).
Flags (1) group-standings flips and (2) knockout picks where the corrected model favors the OTHER team."""
import json, io, sys, math
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
P = r'C:\Users\simon\Projects\pollawc2026'
AB = json.load(open(f'{P}\\output\\sim_results.json', encoding='utf-8'))
C  = json.load(open(f'{P}\\output\\sim_results_C.json', encoding='utf-8'))
pA = json.load(open(f'{P}\\output\\picks_A.json', encoding='utf-8'))
pB = json.load(open(f'{P}\\output\\picks_B.json', encoding='utf-8'))
pC = json.load(open(f'{P}\\output\\picks_C.json', encoding='utf-8'))
ABr = {t: AB['teams'][t]['elo'] for t in AB['teams']}
Cr  = {t: C['teams'][t]['elo']  for t in C['teams']}
cal = C['calib']; Bc=cal['sup_per_elo']; TOT=cal['avg_total']; RHO=cal['rho']

def kop(a, b, R):
    sup=Bc*(R[a]-R[b]); lh=max(.12,(TOT+sup)/2); la=max(.12,(TOT-sup)/2)
    ph=[math.exp(-lh)*lh**i/math.factorial(i) for i in range(9)]; pa=[math.exp(-la)*la**i/math.factorial(i) for i in range(9)]
    M=np.outer(ph,pa); M[0,0]*=1-lh*la*RHO; M[0,1]*=1+lh*RHO; M[1,0]*=1+la*RHO; M[1,1]*=1-RHO; M/=M.sum()
    pH=np.tril(M,-1).sum(); pA_=np.triu(M,1).sum(); pD=1-pH-pA_
    so=1/(1+10**(-(R[a]-R[b])/600)); return pH+pD*so

print('===== INFLATION MAP (how 3-source re-rates each team vs A/B Elo) =====')
shift = sorted(AB['teams'], key=lambda t: Cr[t]-ABr[t])
print('Most INFLATED in A/B (3-source marks them DOWN):')
for t in shift[:8]: print(f'  {t:16s} A/B {ABr[t]:.0f} -> C {Cr[t]:.0f}  ({Cr[t]-ABr[t]:+.0f})')
print('Most UNDER-rated in A/B (3-source marks them UP):')
for t in shift[-6:]: print(f'  {t:16s} A/B {ABr[t]:.0f} -> C {Cr[t]:.0f}  ({Cr[t]-ABr[t]:+.0f})')

print('\n===== (1) GROUP-STANDINGS FLIPS (A/B vs corrected C) =====')
for g in pA['standings']:
    a=pA['standings'][g]; c=pC['standings'][g]
    if a[:3]!=c[:3]:
        print(f'  Group {g}:  A/B 1.{a[0]} 2.{a[1]} 3.{a[2]}   |   C 1.{c[0]} 2.{c[1]} 3.{c[2]}')

print('\n===== (2) KNOCKOUT PICKS where corrected ratings FLIP the favorite =====')
def audit_entry(p, name):
    flags=[]
    for m in p['bracket']['round32']:
        a,b,pick=m['home'],m['away'],m['pick']
        if a and b and pick:
            other=b if pick==a else a
            pc=kop(pick,other,Cr)
            if pc<0.5: flags.append(('R32',m['m'],pick,other,pc,m['conf']))
    for rnd in ('r16','qf','sf'):
        for m in p['bracket'][rnd]:
            a,b,pick=m['a'],m['b'],m['pick']; other=b if pick==a else a
            pc=kop(pick,other,Cr)
            if pc<0.5: flags.append((rnd.upper(),m['m'],pick,other,pc,m['conf']))
    f=p['bracket']['final']; other=f['b'] if f['pick']==f['a'] else f['a']
    pc=kop(f['pick'],other,Cr)
    if pc<0.5: flags.append(('FINAL',104,f['pick'],other,pc,f['conf']))
    print(f'\n  --- Entry {name} (champion {p["bracket"]["champion"]}) ---')
    if not flags: print('    no flips — all picks survive the correction.')
    for rnd,mm,pick,other,pc,conf in flags:
        print(f'    {rnd:5s} M{mm}: picked {pick} over {other} [{conf}] -> corrected says {other} {(1-pc)*100:.0f}% / {pick} {pc*100:.0f}%')
audit_entry(pA,'A'); audit_entry(pB,'B')
