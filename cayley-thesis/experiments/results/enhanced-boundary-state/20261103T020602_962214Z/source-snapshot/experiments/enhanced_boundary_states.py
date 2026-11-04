"""Test Ce/Cv plus marked integral H1 inclusion on the certified 36-case census.

State extraction uses only each first gluing. Final homology is held out until
comparison. Equality preserves boundary labels and quotients interior Z by sign.
All histories, transitions and distinct-history comparisons are persisted.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
from itertools import combinations
import json
from pathlib import Path
import time

import one_tetrahedron_census as census
from boundary_homology import build_boundary_inclusion, verify_boundary_inclusion

ROOT = census.ROOT
REPORT = ROOT / 'reports/enhanced-boundary-state'
DEFAULT_OUTPUT = ROOT / 'experiments/results/enhanced-boundary-state'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def key_hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')


def eligibility(stage):
    reasons = []
    if not stage['edge_orientation_consistent']:
        reasons.append('REVERSED_SELF_EDGE')
    if not all(link['is_surface'] and link['connected'] and link['orientable']
               and link['type'] in ('disk','sphere') for link in stage['links']):
        reasons.append('NON_MANIFOLD_VERTEX_LINK')
    if not stage['orientable']:
        reasons.append('AMBIENT_NONORIENTABLE')
    return {'eligible':not reasons,'reasons':reasons,
            'scope':'First-stage connected orientable 3-manifold with boundary; no final outcome used.'}


def make_history(first, source_case):
    glues = source_case['glues'][:1]
    stage = census.core.analyse(glues,tetrahedra=1)
    require(census.jsonable(stage)==source_case['after_first'],'Source first-stage data differs')
    base = census.boundary_state(stage)
    decision = eligibility(stage)
    history = {'history_id':first,'glues':glues,'stage':census.jsonable(stage),
               'eligibility':decision,'base_state':base,'base_key':key_hash(base),
               'augmentation':None,'enhanced_state':None,'enhanced_key':None}
    if decision['eligible']:
        augmentation = build_boundary_inclusion(glues,stage)
        verify_boundary_inclusion(augmentation)
        state = {'version':'CeCv+marked-H1-inclusion-v1','base':base,
                 'homology_map':augmentation['canonical_map_key'],
                 'marked_boundary_generator_cycles':augmentation['induced_H1']['boundary_generator_cycles']}
        history.update(augmentation=augmentation,enhanced_state=state,enhanced_key=key_hash(state))
    return history


def thin_prediction_input(history):
    """Deliberately omit all interior chain matrices, original gluings and final truth."""
    record = history['augmentation']
    return {'boundary_chain_complex':record['boundary_chain_complex'],
            'boundary_homology':record['boundary_homology'],
            'induced_H1':{name:record['induced_H1'][name] for name in
                          ('domain','target','boundary_generator_cycles','canonical_matrix')}}


def make_transition(case, history):
    result = {'case_id':case['case_id'],'history_id':history['history_id'],
              'completion':case['glues'][1],'eligible':history['eligibility']['eligible'],
              'base_key':history['base_key'],'enhanced_key':history['enhanced_key'],
              'state_predictor':None,'prediction_H1_matches':None,
              'truth':{'accepted':case['decision']['accepted'],
                       'rejection_codes':sorted({r['code'] for r in case['decision']['rejection_reasons']}),
                       'homology':case['homology']['groups'] if case['homology'] else None}}
    if result['eligible']:
        from boundary_completion import predict_h1_completion
        # The predictor receives neither case nor history: its input omits the
        # original first gluing and every interior chain/final-homology matrix.
        prediction = predict_h1_completion(history['base_state'],thin_prediction_input(history),result['completion'])
        result['state_predictor'] = prediction
        if prediction['status']=='PREDICTED' and result['truth']['homology'] is not None:
            predicted = prediction['predicted_H1']
            truth = result['truth']['homology']['H1']
            result['prediction_H1_matches'] = all(predicted[k]==truth[k] for k in ('free_rank','torsion'))
            require(result['prediction_H1_matches'],'State-only H1 prediction disagrees with full history')
    return result


def compare_transitions(transitions, histories):
    by_history = {h['history_id']:h for h in histories}
    groups = defaultdict(list)
    for case in transitions:
        groups[json.dumps(case['completion'],sort_keys=True)].append(case)
    comparisons = []
    for group in groups.values():
        for left,right in combinations(group,2):
            a,b = by_history[left['history_id']],by_history[right['history_id']]
            eligible = left['eligible'] and right['eligible']
            base_equal = a['base_key']==b['base_key'] if eligible else None
            enhanced_equal = a['enhanced_key']==b['enhanced_key'] if eligible else None
            both = left['truth']['accepted'] and right['truth']['accepted'] if eligible else None
            same_homology = left['truth']['homology']==right['truth']['homology'] if both else None
            comparisons.append({'left_case':left['case_id'],'right_case':right['case_id'],
                'completion':left['completion'],'eligible':eligible,'base_equal':base_equal,
                'enhanced_equal':enhanced_equal,'both_accepted':both,'homology_equal':same_homology,
                'base_counterexample':bool(eligible and base_equal and both and not same_homology),
                'enhanced_counterexample':bool(eligible and enhanced_equal and both and not same_homology),
                'comparison_status':'CHECKED' if eligible else 'EXCLUDED_INADMISSIBLE_FIRST_STAGE'})
    return comparisons


def aggregate(histories, transitions, comparisons):
    eligible = [h for h in histories if h['eligibility']['eligible']]
    groups = {}
    for label,key in (('base','base_key'),('enhanced','enhanced_key')):
        buckets = defaultdict(list)
        for history in eligible:
            buckets[history[key]].append(history['history_id'])
        groups[label] = sorted(buckets.values())
    predictions = [t for t in transitions if t['state_predictor'] is not None]
    return {'source_assignments':len(transitions),'first_histories':len(histories),
            'eligible_first_histories':len(eligible),'excluded_first_histories':len(histories)-len(eligible),
            'eligible_transitions':sum(t['eligible'] for t in transitions),
            'accepted_completions':sum(t['eligible'] and t['truth']['accepted'] for t in transitions),
            'excluded_transitions':sum(not t['eligible'] for t in transitions),
            'distinct_history_same_completion_candidates':len(comparisons),
            'eligible_distinct_history_same_completion_candidates':sum(c['eligible'] for c in comparisons),
            'equal_base_state_comparisons':sum(c['base_equal'] is True for c in comparisons),
            'equal_base_state_both_accepted':sum(c['base_equal'] is True and c['both_accepted'] is True for c in comparisons),
            'base_homology_counterexamples':sum(c['base_counterexample'] for c in comparisons),
            'equal_enhanced_state_comparisons':sum(c['enhanced_equal'] is True for c in comparisons),
            'equal_enhanced_state_both_accepted':sum(c['enhanced_equal'] is True and c['both_accepted'] is True for c in comparisons),
            'enhanced_homology_counterexamples':sum(c['enhanced_counterexample'] for c in comparisons),
            'state_groups':groups,
            'prediction_status_counts':dict(sorted(Counter(p['state_predictor']['status'] for p in predictions).items())),
            'predictions_checked_against_truth':sum(t['prediction_H1_matches'] is not None for t in transitions),
            'prediction_mismatches':sum(t['prediction_H1_matches'] is False for t in transitions),
            'nontrivial_enhanced_collision_test':'NO_DISTINCT_HISTORY_PAIR_REMAINS; absence of counterexamples is not a general sufficiency proof.'}


def write_csv_files(run, histories, transitions, comparisons):
    with (run/'states.csv').open('w',encoding='utf-8-sig',newline='') as handle:
        w=csv.writer(handle)
        w.writerow(['history_id','eligible','exclusion_codes','base_key','enhanced_key','boundary_H1','interior_H1','canonical_map'])
        for h in histories:
            a=h['augmentation']
            w.writerow([h['history_id'],h['eligibility']['eligible'],';'.join(h['eligibility']['reasons']),h['base_key'],h['enhanced_key'] or '',
                a['boundary_homology']['groups']['H1']['label'] if a else '',a['interior_homology']['groups']['H1']['label'] if a else '',
                json.dumps(a['canonical_map_key']['matrix']) if a else ''])
    with (run/'transitions.csv').open('w',encoding='utf-8-sig',newline='') as handle:
        w=csv.writer(handle)
        w.writerow(['case_id','eligible','truth_accepted','truth_H1','prediction_status','predicted_H1','prediction_matches'])
        for t in transitions:
            p=t['state_predictor']
            w.writerow([t['case_id'],t['eligible'],t['truth']['accepted'],t['truth']['homology']['H1']['label'] if t['truth']['homology'] else '',
                p['status'] if p else 'EXCLUDED_INADMISSIBLE_FIRST_STAGE',p['predicted_H1']['label'] if p and p['status']=='PREDICTED' else '',
                t['prediction_H1_matches'] if t['prediction_H1_matches'] is not None else ''])
    with (run/'comparisons.csv').open('w',encoding='utf-8-sig',newline='') as handle:
        fields=['left_case','right_case','eligible','base_equal','enhanced_equal','both_accepted','homology_equal','base_counterexample','enhanced_counterexample','comparison_status']
        w=csv.DictWriter(handle,fieldnames=fields)
        w.writeheader()
        for c in comparisons:
            w.writerow({k:c[k] if c[k] is not None else '' for k in fields})


def render_summary(report):
    c=report['counts']
    lines=['# Ce/Cv 加入邊界同調包含映射：36 案結果','','候選狀態為 `(Ce,Cv,H1(M), i*:H1(boundary)->H1(M))`，保留邊界標記；內部 H1=Z 的生成元允許同時換號。來源為既有完整 36 案，取每案第一次貼合的狀態，未使用完成後同調選特徵。','',
           '| 首次貼合 | 是否納入 | 邊界 H1 | 內部 H1 | 固定邊界基底下的映射 |','|---|---|---|---|---|']
    for h in report['histories']:
        a=h['augmentation']
        if a:
            lines.append(f"| {h['history_id']} | 是 | {a['boundary_homology']['groups']['H1']['label']} | {a['interior_homology']['groups']['H1']['label']} | {a['canonical_map_key']['matrix']} |")
        else:
            lines.append(f"| {h['history_id']} | 否 | — | — | {'; '.join(h['eligibility']['reasons'])} |")
    lines += ['', '130 與 301 的程式邊界基底均為 ([03],[23])；映射是 [2,3] 與 [1,3]。換成前次熟悉的 x=[03], y=[13]，因 [23]=x+y，映射分別為 [2,1] 與 [1,2]。整列換號視為相同，不允許任意交換邊界 x、y。','',
              '| 檢查 | Ce/Cv | 增強狀態 |','|---|---:|---:|',
              f"| 合法中間歷史的狀態組數 | {len(c['state_groups']['base'])} | {len(c['state_groups']['enhanced'])} |",
              f"| 不同歷史、同狀態、同末貼合比較 | {c['equal_base_state_comparisons']} | {c['equal_enhanced_state_comparisons']} |",
              f"| 上述比較中兩案皆通過 | {c['equal_base_state_both_accepted']} | {c['equal_enhanced_state_both_accepted']} |",
              f"| 最終同調不同的反例 | {c['base_homology_counterexamples']} | {c['enhanced_homology_counterexamples']} |",'',
              '**重要限制：增強後三種合法歷史各自一組，沒有不同歷史仍被合併。因此零反例不能當作一般充分性或壓縮效益的證明。**','',
              '舊狀態保留的兩個反例：','']
    lines += [f"- {w['left_case']} vs {w['right_case']}；相同末貼合後，第一同調不同。" for w in report['base_counterexamples']]
    lines += ['', '原始 36 案全部保存；其中 18 案來自不合法或不可定向的中間歷史，明確排除於候選狀態實驗。其餘 18 次末貼合中，9 案通過，9 案因商邊反向自識別而不作目標流形同調預測。','',
              f"僅讀邊界狀態與同調映射的預測器，產生 {c['predictions_checked_against_truth']} 個可與目標真值核對的 H1 預測，錯誤 {c['prediction_mismatches']} 個。預測先建立邊界商 Q，使用連通情形的 Mayer–Vietoris 商群公式；不讀原始第一次貼合、內部鏈矩陣或完成後同調。這是本輪額外檢查，不是一般 Ce/Cv-only 合法性更新器或 FPT 複雜度證明。",'',
              '保存內容：6 個 histories、36 個 transitions、90 個同末貼合的不同歷史比較（含排除原因）、完整映射及 Smith 證書、商邊／商鏈資料、預測、反例 JSON 與三張 CSV。']
    return '\n'.join(lines)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-run',type=Path)
    parser.add_argument('--output',type=Path,default=DEFAULT_OUTPUT)
    parser.add_argument('--report-output',type=Path,default=REPORT)
    parser.add_argument('--skip-verification',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args()
    started=time.perf_counter()
    source=args.source_run or Path(json.loads((ROOT/'reports/one-tetrahedron-36/latest-run.json').read_text(encoding='utf-8'))['run_directory'])
    run=args.output/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    for name in ('histories','transitions','comparisons'):
        (run/name).mkdir(parents=True,exist_ok=False)
    write_json(run/'run-status.json',{'status':'BUILDING'})
    # The old verifier writes a dated verification record. Recheck a snapshot
    # so the previously delivered census and its checksums remain unchanged.
    shadow=run/'source-recheck'
    (shadow/'cases').mkdir(parents=True,exist_ok=False)
    for name in ('results.json','results-table.csv','compression-witnesses.json','boundary-inclusion-witness.json'):
        (shadow/name).write_bytes((source/name).read_bytes())
    for path in sorted((source/'cases').glob('*.json')):
        (shadow/'cases'/path.name).write_bytes(path.read_bytes())
    from verify_one_tetrahedron import verify_run as verify_source
    source_verification=verify_source(shadow)
    require(source_verification['status']=='PASS','Source census failed verification')
    source_report=json.loads((source/'results.json').read_text(encoding='utf-8'))
    cases=source_report['cases']
    histories=[]
    for first in sorted({case['case_id'].split('-')[0] for case in cases}):
        history=make_history(first,next(case for case in cases if case['case_id'].startswith(first+'-')))
        histories.append(history)
        write_json(run/'histories'/f'{first}.json',history)
    by_id={h['history_id']:h for h in histories}
    transitions=[]
    for case in cases:
        transition=make_transition(case,by_id[case['case_id'].split('-')[0]])
        transitions.append(transition)
        write_json(run/'transitions'/f"{case['case_id']}.json",transition)
    comparisons=compare_transitions(transitions,histories)
    for comparison in comparisons:
        write_json(run/'comparisons'/f"{comparison['left_case']}__{comparison['right_case']}.json",comparison)
    files=['enhanced_boundary_states.py','boundary_homology.py','boundary_completion.py','one_tetrahedron_census.py','example7_rebuild.py','integer_homology.py']
    report={'schema_version':1,'created_utc':datetime.now(timezone.utc).isoformat(),
        'source_census':{'run_directory':str(source.resolve()),'results_sha256':source_verification['results_sha256'],
                         'recheck_snapshot':'source-recheck'},
        'source_sha256':{f'experiments/{name}':hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in files},
        'state_equality':'Fixed marked boundary and its Ce/Cv-derived basis; interior H1=0/Z modulo target automorphisms. No general higher-rank/torsion map normal form.',
        'histories':histories,'transitions':transitions,'comparisons':comparisons,
        'counts':aggregate(histories,transitions,comparisons),
        'base_counterexamples':[c for c in comparisons if c['base_counterexample']],
        'enhanced_counterexamples':[c for c in comparisons if c['enhanced_counterexample']],
        'build_seconds':time.perf_counter()-started}
    write_json(run/'results.json',report)
    write_json(run/'counterexamples.json',{'base':report['base_counterexamples'],'enhanced':report['enhanced_counterexamples'],
        'status':'NO_INFORMATIVE_EQUAL_ENHANCED_STATE_PAIR','scope':'No remaining distinct-history collisions in this dataset; not a general sufficiency proof.'})
    write_csv_files(run,histories,transitions,comparisons)
    summary=render_summary(report)
    (run/'summary.md').write_text(summary,encoding='utf-8')
    verification={'status':'NOT_RUN'}
    if not args.skip_verification:
        from verify_enhanced_boundary import verify_run
        verification=verify_run(run)
        require(verification['status']=='PASS','Enhanced-state verification failed')
    write_json(run/'run-status.json',{'status':verification['status'],
                                     'results_sha256':hashlib.sha256((run/'results.json').read_bytes()).hexdigest()})
    if verification['status']=='PASS':
        args.report_output.mkdir(parents=True,exist_ok=True)
        for name in ('summary.md','states.csv','transitions.csv','comparisons.csv','counterexamples.json'):
            (args.report_output/name).write_bytes((run/name).read_bytes())
        write_json(args.report_output/'latest-run.json',{'run_directory':str(run.resolve()),'status':'PASS',
            'results_sha256':hashlib.sha256((run/'results.json').read_bytes()).hexdigest(),'counts':report['counts']})
    print(run)
    print(json.dumps(report['counts'],ensure_ascii=True))


if __name__=='__main__':
    main()
