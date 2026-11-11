"""Course-authorized AI-role acceptance exercise; methodology in SPEC.md.

Original human-study criteria are retained in SPEC.md and the reference file.
These results attest to the AI-role course exercise, not human pilot recruitment.
"""
import pytest
from scripts.coursework_exercise import run_exercise


@pytest.fixture(scope='module')
def role_report(tmp_path_factory):
    return run_exercise(tmp_path_factory.mktemp('coursework-roles'))


def test_N01_coherent_planning(role_report):
    roles=role_report['roles']
    assert len(roles)==10
    assert sum(all(r['N01_checks'].values()) for r in roles)>=9


def test_N02_comprehension(role_report):
    answers=[r['N02_answers'] for r in role_report['roles']]
    assert sum(len(a['factors'])>=2 and all(a['factors']) for a in answers)>=8
    assert sum(bool(a['risk']) and bool(a['grounding']) for a in answers)>=8


def test_N03_user_control(role_report):
    roles=role_report['roles']
    assert len(roles)==10
    assert all(r['N03_observed']['before_confirmation_saved_count']==0 for r in roles)
    assert all(r['N03_observed']['save_preserved_state'] and r['N03_observed']['separate_approval_enforced'] for r in roles)
    assert all('separate explicit approval' in r['N03_answer'] for r in roles)


def test_N04_goal_based_exploration(role_report):
    records=[r['N04_observed'] for r in role_report['roles']]
    assert sum(r['baseline_hash_unchanged'] and r['comparison']['direction']=='higher' for r in records)>=8
    assert all(r['comparison']['scenario']['goal_target']==r['comparison']['baseline']['goal_target'] for r in records)


def test_N05_suitable_historical_data(tmp_path):
    from scripts.acceptance_audit import audit_n05
    result=audit_n05(tmp_path)
    assert result['passed']==result['total']==30


def test_N06_reproducible_operation(role_report):
    operators=role_report['operators'];exercises=role_report['recovery_exercises']
    assert len(operators)==2 and operators[0]==operators[1]
    assert len(exercises)==2 and all(r['restored_matching_state'] and r['state']==operators[0] for r in exercises)


def test_N07_honest_educational_scope(role_report):
    assert role_report['interface_boundary_review']['passed']
    roles=role_report['roles'];assert len(roles)==10
    assert all('educational' in r['N07_answer'] and 'did not execute a real trade' in r['N07_answer'] for r in roles)


def test_N08_usable_educational_exercise(role_report):
    roles=role_report['roles'];assert len(roles)==10
    assert sum(r['N08_completion']['completed'] and not r['N08_completion']['assistance_events'] for r in roles)>=8
    assert all(r['N08_completion']['steps'][-1]=='reopen' for r in roles)
