"""Predict one-tetrahedron closing H1 from marked boundary data only.

For F=M union_K Q with K the remaining boundary and Q its face quotient,
the connected-case Mayer-Vietoris sequence gives
H1(F)=coker(H1(K) --(i*,-q*)--> H1(M) + H1(Q)).
CW-subcomplex K->M is a cofibration, so this pushout has the required homotopy
type. See Hatcher, Algebraic Topology, Section 2.2 pp149-152 and Prop0.18.
This is an application of that standard result, not a new topological theorem.

The predictor reads no original gluing history, interior chain complex, or
completed quotient. Its target scope is connected one-tetrahedron prefixes,
whose interior H1 is 0 or Z and whose marked boundary has two faces.
Reversed boundary edges are rejected before the intended cellular basis is used.
"""
from __future__ import annotations

from itertools import combinations
import json

from integer_homology import integral_homology, multiply, smith_normal_form, verify_homology
from boundary_homology import (boundary_complex, homology_generator_cycles,
                               homology_coordinates, parse_face, occurrence_name)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def parity(sequence):
    return -1 if sum(a > b for i,a in enumerate(sequence) for b in sequence[i+1:]) % 2 else 1


class SignedQuotient:
    """Canonical minimum roots; e_i = sign_i e_root."""
    def __init__(self,n):
        self.parent=list(range(n))
        self.sign=[1]*n
        self.consistent=True

    def find(self,i):
        if self.parent[i] == i:
            return i,1
        root,sign=self.find(self.parent[i])
        self.sign[i] *= sign
        self.parent[i]=root
        return root,self.sign[i]

    def join(self,a,b,sign=1):
        ra,sa=self.find(a)
        rb,sb=self.find(b)
        if ra == rb:
            self.consistent = self.consistent and sa == sign*sb
        elif ra < rb:
            self.parent[rb]=ra
            self.sign[rb]=sa*sign*sb
        else:
            self.parent[ra]=rb
            self.sign[ra]=sa*sign*sb

    def projection(self):
        roots=sorted({self.find(i)[0] for i in range(len(self.parent))})
        owner={root:i for i,root in enumerate(roots)}
        matrix=[[0]*len(self.parent) for _ in roots]
        for i in range(len(self.parent)):
            root,sign=self.find(i)
            matrix[owner[root]][i]=sign
        return roots,matrix


def quotient_boundary(boundary,gluing):
    """Construct Q and q:K->Q, using marked boundary cells and the last map."""
    faces=boundary['bases']['faces']
    require(len(faces)==2,'Completion predictor requires exactly two boundary faces')
    st,tt=gluing['source_tet'],gluing['target_tet']
    source=tuple(gluing['source_face'])
    target=tuple(gluing['target_face'])
    require(len(source)==len(target)==3 and len(set(source))==len(set(target))==3,'Face map must be bijective')
    source_name=f't{st}:'+''.join(map(str,sorted(source)))
    target_name=f't{tt}:'+''.join(map(str,sorted(target)))
    require(source_name!=target_name and {source_name,target_name}==set(faces),'Completion must pair precisely the two marked boundary faces')
    mapping=dict(zip(source,target))
    vertex_classes=boundary['vertex_classes']
    vertex_owner={tuple(v):i for i,group in enumerate(vertex_classes) for v in group}
    edge_classes=boundary['edge_occurrence_classes']
    edge_owner={name:i for i,group in enumerate(edge_classes) for name in group}
    edge_sign=boundary['edge_occurrence_signs']
    vq,eq,fq=SignedQuotient(len(vertex_classes)),SignedQuotient(len(edge_classes)),SignedQuotient(2)
    for a in sorted(source):
        vq.join(vertex_owner[st,a],vertex_owner[tt,mapping[a]])
    edge_equations=[]
    for a,b in combinations(sorted(source),2):
        source_occ=occurrence_name(st,tuple(sorted(source)),a,b)
        c,d=mapping[a],mapping[b]
        target_occ=occurrence_name(tt,tuple(sorted(target)),min(c,d),max(c,d))
        sign=(1 if c<d else -1)*edge_sign[source_occ]*edge_sign[target_occ]
        i,j=edge_owner[source_occ],edge_owner[target_occ]
        eq.join(i,j,sign)
        edge_equations.append({'source_occurrence':source_occ,'target_occurrence':target_occ,
                               'source_edge_index':i,'target_edge_index':j,'target_sign_over_source':sign})
    if not eq.consistent:
        return {'status':'REJECTED_EDGE_REVERSAL','edge_equations':edge_equations,
                'reason':'The boundary quotient identifies an edge with its reverse; its orbit is not the intended oriented CW edge.'}
    source_index,target_index=faces.index(source_name),faces.index(target_name)
    face_sign=parity([mapping[v] for v in sorted(source)])
    fq.join(source_index,target_index,face_sign)
    v_roots,q0=vq.projection()
    e_roots,q1=eq.projection()
    f_roots,q2=fq.projection()
    B1_product=multiply(q0,boundary['boundaries']['1'],len(edge_classes))
    B1=[[row[j] for j in e_roots] for row in B1_product]
    B2_product=multiply(q1,boundary['boundaries']['2'],2)
    B2=[[row[j] for j in f_roots] for row in B2_product]
    require(multiply(B1,q1,len(edge_classes))==B1_product,'q0/q1 chain-map identity failed')
    require(multiply(B2,q2,2)==B2_product,'q1/q2 chain-map identity failed')
    quotient={'dimensions':[len(v_roots),len(e_roots),len(f_roots),0],
              'boundaries':{'1':B1,'2':B2,'3':[[] for _ in f_roots]},
              'bases':{'vertices':[boundary['bases']['vertices'][i] for i in v_roots],
                       'edges':[boundary['bases']['edges'][i] for i in e_roots],
                       'faces':[faces[i] for i in f_roots],'tetrahedra':[]}}
    return {'status':'QUOTIENT_BUILT','quotient_chain_complex':quotient,
            'quotient_chain_map':{'0':q0,'1':q1,'2':q2},'edge_equations':edge_equations,
            'face_equation':{'source_index':source_index,'target_index':target_index,'sign':face_sign}}


def predict_h1_completion(boundary_state,inclusion_record,gluing):
    """Use only Ce/Cv, marked H1 inclusion, and one closing face map.

    inclusion_record may be a thin record with exactly boundary_chain_complex,
    boundary_homology, and induced_H1. No interior proof/history is read.
    """
    boundary=json.loads(json.dumps(boundary_complex(boundary_state)))
    require(boundary==inclusion_record['boundary_chain_complex'],'Ce/Cv boundary differs from supplied inclusion domain')
    bh=inclusion_record['boundary_homology']
    verify_homology(boundary['boundaries'],boundary['dimensions'],bh)
    require(bh['groups']['H0']['free_rank']==1 and not bh['groups']['H0']['torsion'],'Boundary must be connected')
    induced=inclusion_record['induced_H1']
    require(induced['domain']==bh['groups']['H1'],'Inclusion domain differs from boundary homology')
    target=induced['target']
    require(not target['torsion'] and target['free_rank'] in (0,1),'Interior H1 currently must be 0 or Z')
    generators=homology_generator_cycles(bh)
    require(generators==induced['boundary_generator_cycles'],'Marked boundary generator cycles differ')
    n_domain=induced['domain']['free_rank']+len(induced['domain']['torsion'])
    i_map=induced['canonical_matrix']
    require(len(i_map)==target['free_rank'] and all(len(row)==n_domain for row in i_map),'Wrong inclusion matrix shape')
    quotient=quotient_boundary(boundary,gluing)
    assumptions={'M_connected':True,'K_connected':True,
                 'M_connected_justification':'Restricted to the connected single-tetrahedron prefix domain.',
                 'K_is_boundary_CW_subcomplex':True,
                 'formula':'H1(M union_K Q) = coker((i*,-q*): H1(K) -> H1(M) + H1(Q))'}
    if quotient['status']!='QUOTIENT_BUILT':
        return {**quotient,'assumptions':assumptions,'predicted_H1':None,'uses_completed_history':False}
    qchain=quotient['quotient_chain_complex']
    qh=integral_homology(qchain['boundaries'],qchain['dimensions'])
    require(qh['groups']['H0']['free_rank']==1 and not qh['groups']['H0']['torsion'],'Boundary quotient must be connected')
    assumptions['Q_connected']=True
    images=multiply(quotient['quotient_chain_map']['1'],generators,n_domain)
    q_map=homology_coordinates(qh,images,columns=n_domain)
    qgroup=qh['groups']['H1']
    n_m=target['free_rank']
    n_q=len(qgroup['torsion'])+qgroup['free_rank']
    n_torsion=len(qgroup['torsion'])
    relations=[[0]*(n_torsion+n_domain) for _ in range(n_m+n_q)]
    for i,order in enumerate(qgroup['torsion']):
        relations[n_m+i][i]=order
    for j in range(n_domain):
        for i in range(n_m):
            relations[i][n_torsion+j]=i_map[i][j]
        for i in range(n_q):
            relations[n_m+i][n_torsion+j]=-q_map[i][j]
    smith=smith_normal_form(relations,n_torsion+n_domain)
    group={'free_rank':n_m+n_q-smith['rank'],'torsion':[d for d in smith['diagonal'] if d>1]}
    pieces=[]
    if group['free_rank']:
        pieces.append('Z' if group['free_rank']==1 else 'Z^'+str(group['free_rank']))
    pieces.extend('Z/'+str(d) for d in group['torsion'])
    group['label']=' + '.join(pieces) or '0'
    return {**quotient,'status':'PREDICTED','quotient_homology':qh,'induced_q_H1':q_map,
            'interior_H1_group':target,'canonical_inclusion_H1':i_map,
            'pushout_H1_presentation':{'rows':n_m+n_q,'columns':n_torsion+n_domain,'relations':relations,
                                      'generator_order':'interior free generators, then Q torsion generators, then Q free generators',
                                      'smith_certificate':smith},
            'predicted_H1':group,'assumptions':assumptions,'uses_completed_history':False,
            'scope':'Only connected single-tetrahedron prefixes; prediction concerns H1, not complete homology or local manifold legality.'}
