import re, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

src = r'C:\Users\simon\.claude\projects\C--Users-simon\1f682ebf-75a7-4a3f-93fd-ae613ba54522\tool-results\mcp-firecrawl-firecrawl_scrape-1780925190917.txt'
t = open(src, encoding='utf-8').read()
t = t.replace('\\n', '\n')  # file stores literal backslash-n

pairs = re.findall(r'\[([^\]]+)\]\(https://www\.eloratings\.net/[^)]+\)\s*\n+\s*(\d{3,4})', t)
d = {}
for name, r in pairs:
    if name not in d:
        d[name] = int(r)

print('parsed', len(d), 'teams')
for k, v in sorted(d.items(), key=lambda x: -x[1])[:30]:
    print(f'{v}  {k}')

json.dump(d, open(r'C:\Users\simon\Projects\pollawc2026\data\elo_raw.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=0)
