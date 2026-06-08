import json, io, sys, math
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
P = r'C:\Users\simon\Projects\pollawc2026'
sim = json.load(open(f'{P}\\output\\sim_results.json', encoding='utf-8'))
cal = sim['calib']; B_SUP=cal['sup_per_elo']; TOT=cal['avg_total']; RHO=cal['rho']
elo = json.load(open(f'{P}\\data\\elo_raw.json', encoding='utf-8'))
gp = {(m['home'],m['away']): m for m in sim['group_pred']}

# find the Belgium-Iran fixture
m = next(v for k,v in gp.items() if set(k)=={'Belgium','Iran'})
H,A = m['home'], m['away']
eh, ea = elo[H], elo[A]
sup = B_SUP*(eh-ea)   # neutral site, no home bonus
lh = max(.12,(TOT+sup)/2); la = max(.12,(TOT-sup)/2)
print(f'Fixture: {H} (Elo {eh}) vs {A} (Elo {ea})   neutral site')
print(f'Elo edge: {eh-ea:+d}  ->  supremacy {sup:+.2f} goals')
print(f'Expected goals (lambda):  {H} {lh:.2f}   {A} {la:.2f}\n')

# Dixon-Coles scoreline matrix
G=7
ph=[math.exp(-lh)*lh**i/math.factorial(i) for i in range(G)]
pa=[math.exp(-la)*la**i/math.factorial(i) for i in range(G)]
M=np.outer(ph,pa)
M[0,0]*=1-lh*la*RHO; M[0,1]*=1+lh*RHO; M[1,0]*=1+la*RHO; M[1,1]*=1-RHO; M/=M.sum()

scores=[]
for i in range(G):
    for j in range(G):
        scores.append((M[i,j],i,j))
scores.sort(reverse=True)
print('Most-probable exact scorelines:')
for p,i,j in scores[:7]:
    print(f'  {H} {i}-{j} {A}   {p*100:4.1f}%')

pH=np.tril(M,-1).sum(); pA=np.triu(M,1).sum(); pD=1-pH-pA
print(f'\nMatch OUTCOME:  {H} win {pH*100:.0f}%   draw {pD*100:.0f}%   {A} win {pA*100:.0f}%')
print(f'Modal exact score (the pick): {H} {scores[0][1]}-{scores[0][2]} {A}  ({scores[0][0]*100:.1f}%)')
