import urllib.request,urllib.parse,json,time,re,datetime,csv
UA={'User-Agent':'occ-review (mailto:research@example.com)'}
def get(u,raw=False):
  for k in range(3):
    try:
      r=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=90).read().decode()
      return r if raw else json.loads(r)
    except Exception as e: err=str(e); time.sleep(20)
  return {'err':err}
def inv(ab):
  if not ab: return ''
  w={}; [w.__setitem__(p,k) for k,ps in ab.items() for p in ps]; return ' '.join(w[i] for i in sorted(w))
S={
'S1 schemes':'"optical camera communication" AND ("LED matrix" OR "LED array") AND modulation',
'S2 simulators':'"optical camera communication" AND (simulator OR simulation framework OR benchmark OR reproducib*)',
'S3 channel':'"optical camera communication" AND ("rolling shutter" OR blur OR noise OR "point spread function" OR "image sensor model") AND channel model',
'S4 CSK':'("color shift keying" OR "colour shift keying" OR CSK) AND (camera OR "image sensor") AND "802.15.7"',
}
# simplified keyword forms for APIs without Boolean
K={'S1 schemes':'optical camera communication LED matrix array modulation',
'S2 simulators':'optical camera communication simulator simulation framework benchmark',
'S3 channel':'optical camera communication channel model rolling shutter blur noise image sensor',
'S4 CSK':'color shift keying camera image sensor 802.15.7'}
log=[];pool={}
def add(src,doi,title,year,ab,venue,auth):
  key=(doi or '').lower().replace('https://doi.org/','') or re.sub(r'\W','',title.lower())[:60]
  if key in pool: pool[key]['src'].add(src); return
  pool[key]=dict(doi=(doi or '').lower().replace('https://doi.org/',''),title=title,year=year,abstract=ab,venue=venue,authors=auth,src={src})
for s,q in K.items():
  e=urllib.parse.quote(q); now=datetime.datetime.now().isoformat(timespec='minutes')
  # Crossref (bibliographic query, 2010+)
  cr=get(f"https://api.crossref.org/works?query.bibliographic={e}&filter=from-pub-date:2010-01-01,until-pub-date:2026-12-31&rows=30&select=DOI,title,author,container-title,issued,abstract")
  m=cr.get('message',{}); log.append([s,'Crossref',q,now,m.get('total-results','ERR'),len(m.get('items',[]))])
  for i in m.get('items',[]): add('Crossref',i['DOI'],(i.get('title') or [''])[0],i['issued']['date-parts'][0][0],re.sub('<[^>]+>','',i.get('abstract','')),(i.get('container-title') or [''])[0],'; '.join(a.get('family','') for a in i.get('author',[])))
  # OpenAlex (title+abstract search)
  oa=get(f"https://api.openalex.org/works?search={e}&filter=from_publication_date:2010-01-01&per-page=30")
  log.append([s,'OpenAlex',q,now,oa.get('meta',{}).get('count',oa.get('err','ERR')),len(oa.get('results',[]))])
  for w in oa.get('results',[]): add('OpenAlex',w.get('doi'),w.get('title') or '',w.get('publication_year'),inv(w.get('abstract_inverted_index')),((w.get('primary_location') or {}).get('source') or {}).get('display_name',''),'; '.join(a['author']['display_name'] for a in w.get('authorships',[])))
  # Semantic Scholar
  time.sleep(10); ss=get(f"https://api.semanticscholar.org/graph/v1/paper/search?query={e}&year=2010-2026&limit=30&fields=title,year,externalIds,abstract,venue,authors")
  log.append([s,'SemanticScholar',q,now,ss.get('total',ss.get('err','ERR')),len(ss.get('data',[]))])
  for w in ss.get('data',[]): add('S2',(w.get('externalIds') or {}).get('DOI'),w['title'],w['year'],w.get('abstract') or '',w.get('venue',''),'; '.join(a['name'] for a in w.get('authors',[])))
  # arXiv
  aq={'S1 schemes':'abs:"camera communication" AND (abs:LED AND abs:modulation)','S2 simulators':'abs:"camera communication" AND (abs:simulator OR abs:simulation OR abs:benchmark)','S3 channel':'abs:"camera communication" AND abs:channel','S4 CSK':'abs:"color shift keying"'}[s]
  ax=get("https://export.arxiv.org/api/query?search_query="+urllib.parse.quote(aq)+"&max_results=30",raw=True)
  if isinstance(ax,dict): log.append([s,'arXiv',aq,now,'ERR',0])
  else:
    tot=re.search(r'totalResults[^>]*>(\d+)',ax); ents=re.findall(r'<entry>(.*?)</entry>',ax,re.S)
    log.append([s,'arXiv',aq,now,tot.group(1) if tot else '?',len(ents)])
    for en in ents:
      t=re.search(r'<title>(.*?)</title>',en,re.S).group(1); sm=re.search(r'<summary>(.*?)</summary>',en,re.S).group(1); y=re.search(r'<published>(\d{4})',en).group(1); d=re.search(r'<arxiv:doi[^>]*>(.*?)<',en)
      add('arXiv',d.group(1) if d else '',' '.join(t.split()),int(y),' '.join(sm.split()),'arXiv','')
  # DBLP
  dq={'S1 schemes':'optical camera communication LED','S2 simulators':'camera communication simulat','S3 channel':'camera communication channel model','S4 CSK':'color shift keying'}[s]
  db=get("https://dblp.org/search/publ/api?format=json&h=30&q="+urllib.parse.quote(dq))
  h=db.get('result',{}).get('hits',{}) if isinstance(db,dict) else {}
  log.append([s,'DBLP',dq,now,h.get('@total','ERR'),len(h.get('hit',[]))])
  for x in h.get('hit',[]):
    i=x['info']; add('DBLP',i.get('doi',''),i.get('title',''),int(i.get('year',0)),'',i.get('venue',''),'')
  time.sleep(15)
json.dump({k:{**v,'src':sorted(v['src'])} for k,v in pool.items()},open('pool.json','w'),indent=1)
csv.writer(open('raw_log.csv','w')).writerows([['set','source','query','datetime_IST','total_hits','retrieved']]+log)
print(len(pool)); [print(r) for r in log]
