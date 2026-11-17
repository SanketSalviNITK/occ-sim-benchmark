import urllib.request,urllib.parse,json,time,re,datetime,csv,sys
UA={'User-Agent':'occ-review (mailto:research@example.com)'}
def get(u,raw=False,tries=2):
  err=''
  for k in range(tries):
    try:
      r=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=45).read().decode()
      return r if raw else json.loads(r)
    except Exception as e: err=str(e)[:60]; time.sleep(8)
  return {'err':err}
def inv(ab):
  if not ab: return ''
  w={}; [w.__setitem__(p,k) for k,ps in ab.items() for p in ps]; return ' '.join(w[i] for i in sorted(w))
OCC='("optical camera communication" OR "image sensor communication" OR "camera communication")'
B={
'S1':OCC+' AND ("LED matrix" OR "LED array" OR "LED panel") AND modulation',
'S2':OCC+' AND (simulator OR "simulation framework" OR "simulation tool" OR benchmark OR reproducibility)',
'S3':OCC+' AND ("channel model" OR "system model") AND ("rolling shutter" OR blur OR noise OR "point spread function")',
'S4':'("color shift keying" OR "colour shift keying") AND (camera OR "image sensor")',
}
S2Q={'S1':'"camera communication" + ("LED matrix" | "LED array") + modulation','S2':'"camera communication" + (simulator | simulation | benchmark)','S3':'"camera communication" + "channel model"','S4':'"color shift keying" + (camera | "image sensor")'}
AX={'S1':'abs:"camera communication" AND (abs:"LED array" OR abs:"LED matrix")','S2':'abs:"camera communication" AND (abs:simulator OR abs:simulation OR abs:benchmark)','S3':'abs:"camera communication" AND abs:"channel model"','S4':'abs:"color shift keying"'}
DB={'S1':'camera communication LED','S2':'camera communication simulat','S3':'camera communication channel model','S4':'color shift keying'}
CRK={'S1':'optical camera communication LED matrix array modulation','S2':'optical camera communication simulator simulation framework','S3':'optical camera communication channel model rolling shutter noise blur','S4':'color shift keying camera image sensor'}
src=sys.argv[1]; log=[]; pool={}
def add(doi,title,year,ab,venue,auth):
  doi=(doi or '').lower().replace('https://doi.org/','')
  pool.setdefault(doi or re.sub(r'\W','',(title or '').lower())[:60],dict(doi=doi,title=title,year=year,abstract=ab,venue=venue,authors=auth,src=src))
for s in B:
  now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5,minutes=30))).strftime('%Y-%m-%d %H:%M IST')
  if src=='openalex':
    q=B[s]; r=get("https://api.openalex.org/works?search="+urllib.parse.quote(q)+"&filter=from_publication_date:2010-01-01,to_publication_date:2026-12-31&per-page=50&sort=relevance_score:desc")
    tot=r.get('meta',{}).get('count',r.get('err')); items=r.get('results',[])
    for w in items: add(w.get('doi'),w.get('title'),w.get('publication_year'),inv(w.get('abstract_inverted_index')),((w.get('primary_location') or {}).get('source') or {}).get('display_name',''),'; '.join(a['author']['display_name'] for a in w.get('authorships',[])))
  elif src=='crossref':
    q=CRK[s]+' [query.bibliographic, relevance-ranked]'; r=get("https://api.crossref.org/works?query.bibliographic="+urllib.parse.quote(CRK[s])+"&filter=from-pub-date:2010-01-01&rows=50&select=DOI,title,author,container-title,issued,abstract")
    m=r.get('message',{}); tot=m.get('total-results',r.get('err')); items=m.get('items',[])
    for i in items: add(i['DOI'],(i.get('title') or [''])[0],i['issued']['date-parts'][0][0],re.sub('<[^>]+>','',i.get('abstract','')),(i.get('container-title') or [''])[0],'; '.join(a.get('family','') for a in i.get('author',[])))
  elif src=='s2':
    q=S2Q[s]; r=get("https://api.semanticscholar.org/graph/v1/paper/search/bulk?query="+urllib.parse.quote(q)+"&year=2010-2026&fields=title,year,externalIds,abstract,venue,authors",tries=4)
    tot=r.get('total',r.get('err')); items=(r.get('data') or [])[:50]
    for w in items: add((w.get('externalIds') or {}).get('DOI'),w['title'],w['year'],w.get('abstract') or '',w.get('venue',''),'; '.join(a['name'] for a in w.get('authors',[])))
  elif src=='arxiv':
    q=AX[s]; r=get("https://export.arxiv.org/api/query?search_query="+urllib.parse.quote(q)+"&max_results=50",raw=True,tries=4)
    if isinstance(r,dict): tot=r['err']; items=[]
    else:
      t=re.search(r'totalResults[^>]*>(\d+)',r); tot=t.group(1) if t else '?'; items=re.findall(r'<entry>(.*?)</entry>',r,re.S)
      for en in items:
        d=re.search(r'<arxiv:doi[^>]*>(.*?)<',en); add(d.group(1) if d else '',' '.join(re.search(r'<title>(.*?)</title>',en,re.S).group(1).split()),int(re.search(r'<published>(\d{4})',en).group(1)),' '.join(re.search(r'<summary>(.*?)</summary>',en,re.S).group(1).split()),'arXiv','')
  elif src=='dblp':
    q=DB[s]; r=get("https://dblp.org/search/publ/api?format=json&h=50&q="+urllib.parse.quote(q),tries=4)
    h=r.get('result',{}).get('hits',{}) if 'err' not in r else {}; tot=h.get('@total',r.get('err')); items=h.get('hit',[])
    for x in items:
      i=x['info']; add(i.get('doi',''),i.get('title',''),int(i.get('year',0)),'',i.get('venue',''),'')
  log.append([s,src,q,now,tot,len(items)]); print(log[-1],flush=True); time.sleep(25)
json.dump(pool,open(f'pool_{src}.json','w'),indent=1)
csv.writer(open(f'log_{src}.csv','w')).writerows(log)
