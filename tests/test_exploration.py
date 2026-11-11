"""Negative and conservation checks for UC.3/UC.4 educational extensions."""
import copy
import json
import math
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from wealthpilot_service import Planner
from wealthpilot_service.api import create_app
from wealthpilot_service.exploration import compare_goal_scenario
from scripts.baseline_recovery import freeze,restore


@pytest.fixture
def exercise(tmp_path,snapshot_directory,investor):
    planner=Planner(snapshot_directory=snapshot_directory,database_path=tmp_path/'exercise.db')
    client=TestClient(create_app(planner))
    sid=client.post('/api/sessions').json()['session_id']
    assert client.post(f'/api/sessions/{sid}/investor-information',json=investor).status_code==200
    shown=client.post(f'/api/sessions/{sid}/plan',json={'profile_interpretation_confirmed':True}).json()['presented_plan']
    return planner,client,sid,shown


def save(exercise):
    planner,client,sid,shown=exercise
    assert client.post(f'/api/sessions/{sid}/plan-save-requests',json={'plan_id':shown['plan_id'],'action':'save'}).json()['status']=='saved'


def test_SR_07_SR_08_lower_contribution_preserves_saved_baseline(exercise):
    planner,client,sid,shown=exercise;save(exercise)
    before=copy.deepcopy(planner.saved_plan(shown['plan_id']))
    result=client.post(f"/api/saved-plans/{shown['plan_id']}/what-if",json={'monthly_contribution':0,'goal_target':100000}).json()
    assert result['direction']=='lower' and result['difference']==-150000
    assert result['scenario']['planned_resources']==30000
    assert result['scenario']['goal_target']==result['baseline']['goal_target']
    assert planner.saved_plan(shown['plan_id'])==before


@pytest.mark.parametrize('body',[{}, {'monthly_contribution':-1},{'horizon_years':0},{'goal_target':0}])
def test_SR_07_invalid_or_unchanged_scenario_is_rejected(exercise,body):
    _,client,_,shown=exercise;save(exercise)
    assert client.post(f"/api/saved-plans/{shown['plan_id']}/what-if",json=body).status_code==422


def test_SR_06_save_is_not_separate_change_approval(exercise):
    planner,client,sid,shown=exercise
    url=f'/api/sessions/{sid}/simulated-change-approvals'
    request={'plan_id':shown['plan_id'],'action':'approve_simulated_change','approval_id':'approval-1'}
    assert client.post(url,json=request).json()['status']=='not_authorized'
    save(exercise);before=planner.portfolio_store.read(sid)
    request['action']='save'
    assert client.post(url,json=request).json()['status']=='not_authorized'
    assert planner.portfolio_store.read(sid)==before
    request['action']='approve_simulated_change'
    first=client.post(url,json=request).json();assert first['status']=='applied'
    assert client.post(url,json=request).json()['status']=='already_applied'
    assert first['after']['cash']+sum(h['value'] for h in first['after']['holdings'])==pytest.approx(30000,abs=.01)


def test_SR_08_non_finite_goal_is_rejected(exercise):
    _,_,_,shown=exercise
    with pytest.raises(ValueError):
        compare_goal_scenario(shown['content'],monthly_contribution=600,goal_target=float('inf'))


def test_SR_12_changed_frozen_baseline_is_not_restored(tmp_path):
    import sqlite3
    database=tmp_path/'db';configuration=tmp_path/'rules.json';configuration.write_text('{}')
    with sqlite3.connect(database) as c:c.execute('CREATE TABLE example(value INTEGER)')
    folder=tmp_path/'frozen';freeze(database,configuration,folder)
    (folder/'rules.json').write_text('{"changed":true}')
    with pytest.raises(ValueError,match='altered'):
        restore(folder,database,configuration)
