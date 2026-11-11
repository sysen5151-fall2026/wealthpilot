"""Execute a frozen exercise in one separate operator-role process."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from system_administration import load_configuration
from wealthpilot_service import Planner
from wealthpilot_service.exploration import apply_approved_change
from scripts.baseline_recovery import inspect_state


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    for name in ("configuration","prices","investor","database"):p.add_argument('--'+name,required=True)
    a=p.parse_args()
    investor=json.loads(Path(a.investor).read_text())
    planner=Planner(configuration=load_configuration(Path(a.configuration)),snapshot_directory=Path(a.prices),database_path=Path(a.database))
    sid=planner.start_session().session_id
    planner.submit_investor_information(sid,**investor)
    plan=planner.build_plan(sid,profile_interpretation_confirmed=True)
    assert planner.request_save(sid,plan_id=plan.presented.plan_id,action="save").status=="saved"
    result=apply_approved_change(planner,sid,plan_id=plan.presented.plan_id,action="approve_simulated_change",approval_id="frozen-exercise-approval")
    assert result["status"]=="applied"
    print(json.dumps(inspect_state(a.database,a.configuration),sort_keys=True))
