"""results.md から results.html を作る(依存なし)。python3 build_results.py"""
import re,html
md=open('results.md',encoding='utf-8').read().split('\n')
out=[];ul=False;tb=[]
def flush_tb():
    global tb
    if not tb: return
    h='<table>'
    for i,r in enumerate(tb):
        t='th' if i==0 else 'td'
        h+='<tr>'+''.join(f'<{t}>{html.escape(c)}</{t}>' for c in r)+'</tr>'
    out.append(h+'</table>'); tb=[]
for l in md:
    l=l.rstrip()
    if l.startswith('|'):
        c=[x.strip() for x in l.strip('|').split('|')]
        if all(re.fullmatch(r':?-+:?',x) for x in c): continue
        tb.append(c); continue
    flush_tb()
    if ul and not l.startswith('- '): out.append('</ul>'); ul=False
    if l.startswith('# '): out.append(f'<h1>{html.escape(l[2:])}</h1>')
    elif l.startswith('## '): out.append(f'<h2>{html.escape(l[3:])}</h2>')
    elif l.startswith('- '):
        if not ul: out.append('<ul>'); ul=True
        out.append(f'<li>{html.escape(l[2:])}</li>')
    elif l: out.append(f'<p>{html.escape(l)}</p>')
flush_tb()
if ul: out.append('</ul>')
head=open('results.html',encoding='utf-8').read().split('<main>')[0]
open('results.html','w',encoding='utf-8').write(head+'<main>\n<p><a href="index.html">&larr; トップへ</a></p>\n'+'\n'.join(out)+'\n</main></body></html>\n')
