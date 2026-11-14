"""Versioned Chapter 10 core benchmark (synthetic investor; actual local product).

Usage: python scripts/ch10_measure.py --out evidence/ch10/pilot --runs 100
The cache starts empty and is deliberately evicted every 10 cached requests.
This is a prescribed 10% miss workload, not an estimate of production misses.
"""
import argparse
from collections import defaultdict
from dataclasses import asdict
import functools
import hashlib
import json
from pathlib import Path
import platform
import random
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import wealthpilot_service.pipeline as pipeline
from investor_interface.console import SAMPLE_INVESTOR
from market_data_provider.snapshot_cache import VerifiedSnapshotCache

STAGES = {
    'collect_investor_information': 'bundled_input_validation',
    'assess_investor_risk_profile': 'UC.1.8',
    'request_historical_market_data': 'UC.1.11',
    'provide_historical_market_data': 'UC.1.12',
    'determine_target_asset_allocation': 'UC.1.13',
    'screen_candidate_securities': 'UC.1.14',
    'generate_investment_recommendations': 'UC.1.15',
    'explain_investment_plan': 'UC.1.16',
    'present_investment_plan': 'UC.1.17',
    'validate_explicit_plan_save_request': 'save_authorization',
    'persist_reviewed_investment_plan': 'save_persistence',
    'confirm_successful_plan_save': 'save_confirmation',
}


def identity():
    paths = sorted(p for p in ROOT.rglob('*.py') if '.venv' not in p.parts and '.git' not in p.parts)
    return {
        'base_commit': 'f012ac2894730bbabbb10d8aac208533504b4ece',
        'measured_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'working_tree_status': subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True),
        'python': sys.version, 'platform': platform.platform(),
        'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
    }


def statistics_ms(values):
    v = sorted(values)
    return dict(n=len(v), min=min(v), max=max(v), mean=statistics.mean(v),
                median=statistics.median(v), p95=v[max(0, int(.95*len(v)) - 1)],
                sd=statistics.stdev(v) if len(v)>1 else 0)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--runs', type=int, default=100)
    args=parser.parse_args(); args.out.mkdir(parents=True, exist_ok=True)
    context={}; events=[]; rows=[]
    originals={name:getattr(pipeline,name) for name in STAGES}
    def record(stage, entry, exit):
        events.append({**context, 'stage':stage, 'entry_ns':entry, 'exit_ns':exit,
                       'duration_ms':(exit-entry)/1e6})
    def timed(stage, fn):
        @functools.wraps(fn)
        def wrapped(*a, **kw):
            start=time.perf_counter_ns()
            try: return fn(*a, **kw)
            finally: record(stage,start,time.perf_counter_ns())
        return wrapped
    for name,fn in originals.items(): setattr(pipeline,name,timed(STAGES[name],fn))
    cache=VerifiedSnapshotCache(record)
    planners={m:pipeline.Planner(database_path=args.out/(m+'.sqlite')) for m in ['baseline','cached']}
    order=['baseline','cached']*args.runs; random.Random(5151).shuffle(order)
    counts=defaultdict(int); reference=None
    for mode in order:
        counts[mode]+=1; context.update(scenario=mode,run=counts[mode])
        if mode=='cached' and (counts[mode]-1)%10==0: cache.invalidate()
        pipeline.provide_historical_market_data=timed('UC.1.12', cache if mode=='cached' else originals['provide_historical_market_data'])
        start_events=len(events); planner=planners[mode]; start=time.perf_counter_ns()
        session=planner.start_session()
        planner.submit_investor_information(session.session_id,**SAMPLE_INVESTOR)
        build_start=time.perf_counter_ns()
        planner.build_plan(session.session_id,profile_interpretation_confirmed=True)
        build_end=time.perf_counter_ns(); save_start=time.perf_counter_ns()
        saved=planner.request_save(session.session_id,plan_id=session.presented.plan_id,action='save')
        end=time.perf_counter_ns(); record('UC.1.19',save_start,end)
        assert saved.status=='saved' and saved.simulated_portfolio_before==saved.simulated_portfolio_after
        assert planner.saved_plan(session.presented.plan_id)==session.presented.content
        recommendation=asdict(session.recommendations)
        if reference is None: reference=recommendation
        assert recommendation==reference
        stage={e['stage']:e['duration_ms'] for e in events[start_events:]}
        rows.append({**context,'cache_miss':mode=='cached' and 'SIM.C.12.3' in stage,
                     'total_core_ms':(end-start)/1e6,'plan_build_ms':(build_end-build_start)/1e6,
                     'C6_prepare_ms':stage['UC.1.16']+stage['UC.1.17'],
                     'stages_ms':stage,'save_ok':True,'recommendation_equal':True})
    summary={}
    for mode in planners:
        relevant=[r for r in rows if r['scenario']==mode]
        keys=sorted({k for r in relevant for k in r['stages_ms']})
        summary[mode]={k:statistics_ms([r['stages_ms'][k] for r in relevant if k in r['stages_ms']]) for k in keys}
        for key in ['total_core_ms','plan_build_ms','C6_prepare_ms']:
            summary[mode][key]=statistics_ms([r[key] for r in relevant])
    meta={**identity(),'runs_per_scenario':args.runs,'seed':5151,
          'boundary':'Planner start through explicit save; no browser or human time',
          'cache_workload':'empty initially; deliberate eviction every 10 cached requests',
          'cache_hits':cache.hits,'cache_misses':cache.misses,
          'snapshot_manifest':json.loads((pipeline.DEFAULT_SNAPSHOT_DIRECTORY/'manifest.json').read_text())}
    for filename,data in [('runs.json',rows),('events.json',events),('summary.json',summary),('experiment.json',meta)]:
        (args.out/filename).write_text(json.dumps(data,indent=2))
    print(json.dumps({'runs':len(rows),'cache_hits':cache.hits,'cache_misses':cache.misses,
                     'means_ms':{m:summary[m]['total_core_ms']['mean'] for m in planners}},indent=2))


if __name__=='__main__': main()
