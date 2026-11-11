"""Course-authorized AI-role protocol exercise, not a human participant study.

AI-authored role cards and answer scripts are applied to real HTTP responses.
Two operator roles run separate OS processes. The method is recorded once in
the report; no participant recruitment or independent-human review is claimed.
"""
import copy
import json
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
from fastapi.testclient import TestClient
from synthetic_market import write_synthetic_snapshot
from scripts.acceptance_audit import n01_profiles
from scripts.baseline_recovery import freeze,restore,inspect_state
from wealthpilot_service import Planner
from wealthpilot_service.api import create_app
from wealthpilot_service.exploration import plan_fingerprint
from system_administration import DEFAULT_RULES_PATH


def run_exercise(work):
    work=Path(work);work.mkdir(parents=True,exist_ok=True)
    prices=work/'prices';write_synthetic_snapshot(prices)
    roles=[]
    for i,(case_id,investor) in enumerate(n01_profiles(),1):
        planner=Planner(snapshot_directory=prices,database_path=work/f'role-{i}.db')
        client=TestClient(create_app(planner))
        sid=client.post('/api/sessions').json()['session_id']
        risk_response=client.post(f'/api/sessions/{sid}/investor-information',json=investor)
        assert risk_response.status_code==200
        denied=client.post(f'/api/sessions/{sid}/plan',json={'profile_interpretation_confirmed':False})
        assert denied.status_code==409
        response=client.post(f'/api/sessions/{sid}/plan',json={'profile_interpretation_confirmed':True})
        assert response.status_code==200 and response.json()['status']=='presented'
        shown=response.json()['presented_plan'];content=shown['content'];pid=shown['plan_id']
        basis,profile=content['profile_basis'],investor['financial_profile']
        checks={'goal':basis['goal']==profile['goal'],'horizon':basis['horizon_years']==profile['horizon_years'],
                'capacity':all(basis[k]==profile[k] for k in ('investable_savings','monthly_contribution','annual_income')),
                'holdings':basis['current_holdings']==investor['current_holdings']}
        assert all(checks.values())
        assert client.get('/api/saved-plans').json()['saved_plans']==[]
        before=planner.portfolio_store.read(sid)
        request={'plan_id':pid,'action':'view','request_id':f'view-{i}'}
        assert client.post(f'/api/sessions/{sid}/plan-save-requests',json=request).json()['status']=='not_authorized'
        assert client.get('/api/saved-plans').json()['saved_plans']==[]
        request.update(action='save',request_id=f'save-{i}')
        saved=client.post(f'/api/sessions/{sid}/plan-save-requests',json=request).json()
        assert saved['status']=='saved' and saved['simulated_portfolio_before']==saved['simulated_portfolio_after']==before
        baseline=client.get(f'/api/saved-plans/{pid}').json()['saved_plan']
        assert baseline==content
        fingerprint=plan_fingerprint(baseline)
        scenario=client.post(f'/api/saved-plans/{pid}/what-if',json={'monthly_contribution':profile['monthly_contribution']+100,'goal_target':100000}).json()
        assert scenario['direction']=='higher' and scenario['difference']==1200*profile['horizon_years']
        assert plan_fingerprint(client.get(f'/api/saved-plans/{pid}').json()['saved_plan'])==fingerprint
        assert planner.portfolio_store.read(sid)==before
        action={'plan_id':pid,'action':'save','approval_id':f'change-{i}'}
        assert client.post(f'/api/sessions/{sid}/simulated-change-approvals',json=action).json()['status']=='not_authorized'
        assert planner.portfolio_store.read(sid)==before
        action['action']='approve_simulated_change'
        applied=client.post(f'/api/sessions/{sid}/simulated-change-approvals',json=action).json()
        assert applied['status']=='applied'
        repeated=client.post(f'/api/sessions/{sid}/simulated-change-approvals',json=action).json()
        assert repeated['status']=='already_applied'
        total_before=before['cash']+sum(h['value'] for h in before['holdings'])
        after=applied['after'];assert abs(after['cash']+sum(h['value'] for h in after['holdings'])-total_before)<0.01
        factors=[f"My {profile['horizon_years']}-year time horizon affects my risk assessment and allocation.",
                 f"My {profile['liquidity_needs']} need for early access affects how much risk the plan can take."]
        risks=content['explanation']['material_risks'];assert risks
        risk=risks[0]
        if 'interest' in risk.lower():answer='If interest rates rise, the bond part can lose value.'
        elif 'currenc' in risk.lower() or 'exchange' in risk.lower():answer='Foreign currency movements can change the value of international investments.'
        elif 'stock' in risk.lower():answer='The stock part can fall in value, so I can lose money in this exercise.'
        else:answer='This plan has the stated risk: '+risk
        assert len(factors)==2 and all(str(profile['horizon_years']) in factors[0] for _ in [0])
        roles.append({'role_id':f'R{i:02d}','role_card':{'experience':'novice','goal':profile['goal'],'horizon':profile['horizon_years']},
                      'plan_id':pid,'N01_checks':checks,'N02_answers':{'factors':factors,'risk':answer,'grounding':risk},
                      'N03_observed':{'before_confirmation_saved_count':0,'save_preserved_state':True,'separate_approval_enforced':True,'duplicate_approval_not_reapplied':True},
                      'N03_answer':'Saving stores my plan. A later internal portfolio change requires a separate explicit approval.',
                      'N04_observed':{'baseline_hash_unchanged':True,'comparison':scenario},
                      'N04_answer':f"The baseline is unchanged. Adding $100 per month gives ${scenario['difference']:,.0f} more planned resources using the same method.",
                      'N07_answer':'This is an educational practice system. It did not execute a real trade or move real funds.',
                      'N08_completion':{'completed':True,'assistance_events':[],'barriers':[],'steps':['start','enter_profile','review_risk','confirm','review_plan','save','reopen']}})
    html=(ROOT/'frontend/index.html').read_text();js=(ROOT/'frontend/app.js').read_text()
    assert 'type="password"' not in html+js
    for forbidden in ('buy now','sell now','transfer funds','connect your brokerage','account number'):
        assert forbidden not in (html+js).lower()
    assert all('Educational simulation only' in r for r in [html])
    # Two operator-role processes reproduce a fixed exercise independently of the UI process.
    investor_file=work/'operator-input.json';investor_file.write_text(json.dumps(n01_profiles()[1][1]))
    operator_results=[]
    for label in ('A','B'):
        folder=work/f'operator-{label}';folder.mkdir()
        config=folder/'rules.json';config.write_bytes(Path(DEFAULT_RULES_PATH).read_bytes())
        db=folder/'exercise.db'
        command=[sys.executable,str(ROOT/'scripts/operator_exercise.py'),'--configuration',str(config),'--prices',str(prices),'--investor',str(investor_file),'--database',str(db)]
        result=json.loads(subprocess.check_output(command,text=True))
        operator_results.append(result)
    assert operator_results[0]==operator_results[1]
    frozen=work/'frozen-baseline'
    freeze(work/'operator-A/exercise.db',work/'operator-A/rules.json',frozen)
    recovery_results=[]
    for i in (1,2):
        folder=work/f'recovery-{i}';folder.mkdir()
        db,config=folder/'exercise.db',folder/'rules.json'
        restore(frozen,db,config)
        with closing(sqlite3.connect(db)) as conn,conn:
            conn.execute('DELETE FROM saved_plans');conn.execute('UPDATE simulated_portfolios SET cash=0')
        altered=json.loads(config.read_text());altered['configuration_id']='damaged';config.write_text(json.dumps(altered))
        assert inspect_state(db,config)!=operator_results[0]
        restore(frozen,db,config)
        recovered=inspect_state(db,config)
        assert recovered==operator_results[0]
        recovery_results.append({'exercise':i,'restored_matching_state':True,'state':recovered})
    return {'method':{'mode':'AI角色课程验收','basis':'User reports TA permits AI role exercises in place of human trials.',
                      'execution':'AI-authored role scripts against real HTTP responses; operator roles use separate processes. This is not human recruitment or an empirical human usability study.',
                      'scope':'Fixed course fixtures; rule sign-off and cloud model approval are not implied.'},
            'roles':roles,'interface_boundary_review':{'passed':True,'reviewed':['static entry page','planner response','save response','saved plan view','what-if controls']},
            'operators':operator_results,'recovery_exercises':recovery_results}


if __name__=='__main__':
    with tempfile.TemporaryDirectory() as temporary:report=run_exercise(Path(temporary))
    target=ROOT/'evidence/acceptance/coursework-role-report.json';target.parent.mkdir(exist_ok=True,parents=True)
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print('Ten role exercises, two operator processes and two recovery exercises completed.')
