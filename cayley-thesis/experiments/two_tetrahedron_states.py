"""Fixed two-tetrahedron 6^4 census and marked H1-state collision audit."""
import sys,json,hashlib,importlib.util,types,inspect
from pathlib import Path
from itertools import permutations,product,combinations
from datetime import datetime,timezone
import example7_rebuild as core
import one_tetrahedron_census as old
import boundary_homology as bh
from integer_homology import integral_homology,verify_homology
ROOT=core.ROOT
spec=importlib.util.spec_from_file_location("lens",ROOT/"reports/examples/fixed_graph_lens17.py")
lens=importlib.util.module_from_spec(spec);spec.loader.exec_module(lens)
# Two parallel cross edges plus one loop at each node: connected 4-regular graph.
PAIRS=[(0,[0,1,2],1,[0,1,2]),(0,[0,1,3],1,[0,1,3]),(0,[0,2,3],0,[1,2,3]),(1,[0,2,3],1,[1,2,3])]
def glues(indices):
 return [dict(source_tet=t,source_face=a,target_tet=s,target_face=list(list(permutations(b))[i])) for i,(t,a,s,b) in zip(indices,PAIRS)]
def constraints(gs):
 records,_=core.normalize(gs,tetrahedra=2);ec=[];fc=[];eq=[]
 for t,f,s,g,p in records:
  for a,b in combinations(sorted(set(range(4))-{f}),2):ec.append(((t,a,b),(s,min(p[a],p[b]),max(p[a],p[b])),1 if p[a]<p[b] else -1))
  fc.append(((t,f),(s,g),core.parity([p[v] for v in range(4) if v!=f])))
 return records,ec,fc,eq
# Dedicated general chain builder; all signs use the same lexicographic basis.
def chain(gs,stage):
 records,ec,fc,_=constraints(gs)
 vs=stage['vertex_classes'];es=stage['edge_classes'];fs,fo=core.quotient([(t,f) for t in range(2) for f in range(4)],[(a,b) for a,b,_ in fc])
 vo={tuple(x):i for i,g in enumerate(vs) for x in g};eo={tuple(x):i for i,g in enumerate(es) for x in g}
 signs,ok=core.signed_labels(list(eo),ec);signf,okf=core.signed_labels(list(fo),fc)
 if not(ok and okf):raise ValueError('reversed cell')
 B1=[[0]*len(es) for _ in vs];B2=[[0]*len(fs) for _ in es];B3=[[0]*2 for _ in fs]
 for j,g in enumerate(es):
  t,a,b=g[0];B1[vo[t,a]][j]-=1;B1[vo[t,b]][j]+=1
 for j,g in enumerate(fs):
  t,f=g[0];a,b,c=sorted(set(range(4))-{f})
  for x,y,z in [(b,c,1),(a,c,-1),(a,b,1)]:B2[eo[t,x,y]][j]+=z*signs[t,x,y]
 for t in range(2):
  for f in range(4):B3[fo[t,f]][t]+=(-1)**f*signf[t,f]
 return dict(dimensions=[len(vs),len(es),len(fs),2],boundaries={'1':B1,'2':B2,'3':B3},bases=dict(vertices=[g[0] for g in vs],edges=[g[0] for g in es],faces=[g[0] for g in fs],tetrahedra=[0,1]))
# Isolate the existing inclusion routine's single-tet dependency; do not mutate it.
proxy=types.SimpleNamespace(boundary_state=old.boundary_state,chain_complex=chain,constraints=constraints)
namespace=dict(bh.build_boundary_inclusion.__globals__);namespace['census']=proxy
exec(inspect.getsource(bh.build_boundary_inclusion).replace('[(0,f) for f in range(4)]','[(t,f) for t in range(2) for f in range(4)]'),namespace)
build=namespace['build_boundary_inclusion']
def key(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def main():
 run=ROOT/'experiments/results/two-tetrahedron'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');(run/'cases').mkdir(parents=True)
 histories={};cases=[];unsupported=[]
 for prefix in product(range(6),repeat=3):
  gs=glues(prefix)
  try:stage=core.analyse(gs,tetrahedra=2)
  except ValueError as e:
   histories[prefix]=dict(prefix=prefix,status='INVALID_BOUNDARY',reason=str(e));continue
  valid=stage['orientable'] and stage['manifold_with_boundary_link_test']
  h=dict(prefix=prefix,glues=gs,stage=stage,status='INELIGIBLE',state=None)
  if valid:
   try:
    inc=build(gs,stage);bh.verify_boundary_inclusion(inc)
    h.update(status='SUPPORTED',inclusion=inc,state=dict(base=old.boundary_state(stage),map=inc['canonical_map_key'],cycles=inc['induced_H1']['boundary_generator_cycles']))
   except ValueError as e:h.update(status='UNSUPPORTED',reason=str(e));unsupported.append(h)
  histories[prefix]=h
 for indices in product(range(6),repeat=4):
  gs=glues(indices);stage=core.analyse(gs,tetrahedra=2);decision=old.decide(stage)
  c=dict(case_id=''.join(map(str,indices)),indices=indices,glues=gs,after=stage,decision=decision,homology=None)
  if decision['accepted']:
   ch=chain(gs,stage);hom=integral_homology(ch['boundaries'],ch['dimensions']);verify_homology(ch['boundaries'],ch['dimensions'],hom)
   records,_=core.normalize(gs,tetrahedra=2)
   other=lens.analyse(2,[(t,f,s,tuple(p[i] for i in range(4))) for t,f,s,g,p in records])
   assert other['connected'] and other['orientable'] and other['edge_orientation_consistent']
   assert all(l['is_surface'] and l['type']=='sphere' for l in other['links'])
   assert lens.smith_factors(other['B2'])==[d for d in __import__('integer_homology').smith_normal_form(ch['boundaries']['2'])['diagonal']]
   c.update(chain_complex=ch,homology=hom)
  cases.append(c);(run/'cases'/(c['case_id']+'.json')).write_text(json.dumps(c),encoding='utf-8')
 groups={}
 for pre,h in histories.items():
  if h['status']=='SUPPORTED':groups.setdefault(key(h['state']),[]).append(pre)
 byid={tuple(c['indices']):c for c in cases};comparisons=[]
 for members in groups.values():
  for a,b in combinations(members,2):
   for end in range(6):
    ca,cb=byid[a+(end,)],byid[b+(end,)];both=ca['decision']['accepted'] and cb['decision']['accepted']
    same=ca['homology']['groups']==cb['homology']['groups'] if both else None
    comparisons.append(dict(left=ca['case_id'],right=cb['case_id'],both_accepted=both,same_homology=same,counterexample=both and not same))
 counts=dict(assignments=len(cases),accepted=sum(c['decision']['accepted'] for c in cases),prefixes=len(histories),prefix_status={s:sum(h['status']==s for h in histories.values()) for s in set(h['status'] for h in histories.values())},state_groups=len(groups),shared_groups=sum(len(v)>1 for v in groups.values()),distinct_history_same_completion_comparisons=len(comparisons),both_accepted=sum(c['both_accepted'] for c in comparisons),counterexamples=sum(c['counterexample'] for c in comparisons))
 out=dict(fixed_pairs=PAIRS,counts=counts,histories=list(histories.values()),shared_groups=[v for v in groups.values() if len(v)>1],comparisons=comparisons,counterexamples=[c for c in comparisons if c['counterexample']],scope='H1 target 0/Z only; unsupported prefixes explicitly retained. Full-history reconstruction, not state-only updater.',source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path(bh.__file__),Path(core.__file__)]})
 (run/'results.json').write_text(json.dumps(out),encoding='utf-8')
 lines=['# 固定兩四面體 1296 案','',json.dumps(counts,ensure_ascii=False),'','固定前三次貼合為歷史，第四次為共同後續貼合。排列索引0..5依lexicographic順序。','', '## 共享增強狀態案例']
 for group in out['shared_groups'][:5]:
  lines+=['',str(group)]
  for c in comparisons:
   if tuple(map(int,c['left'][:3]))==tuple(group[0]) and c['both_accepted']:lines.append(str(c))
 lines+=['','本輪是完整歷史核對；同調映射的相等比較僅支援內部H1為0或Z。未支援者沒有當成不相等或成功。原始逐案links、拒絕原因及通過者整數證書見cases。']
 (run/'report.md').write_text('\n'.join(lines),encoding='utf-8')
 report=ROOT/'reports/two-tetrahedron-1296';report.mkdir(exist_ok=True)
 (report/'latest-run.json').write_text(json.dumps(dict(run_directory=str(run),counts=counts)),encoding='utf-8');(report/'report.md').write_bytes((run/'report.md').read_bytes())
 print(run);print(counts)
if __name__=='__main__':main()
