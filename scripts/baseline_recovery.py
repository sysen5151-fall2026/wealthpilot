"""Freeze and restore a local educational exercise; never contacts a brokerage."""
import hashlib
import json
import shutil
import sqlite3
from contextlib import closing
from pathlib import Path


def freeze(database, configuration, folder):
    folder = Path(folder); folder.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(database)) as source, closing(sqlite3.connect(folder/"baseline.db")) as destination:
        source.backup(destination)
    shutil.copy2(configuration, folder/"rules.json")
    hashes={n:hashlib.sha256((folder/n).read_bytes()).hexdigest() for n in ("baseline.db","rules.json")}
    (folder/"manifest.json").write_text(json.dumps(hashes,indent=2))


def restore(folder, database, configuration):
    folder = Path(folder)
    for name,expected in json.loads((folder/"manifest.json").read_text()).items():
        if hashlib.sha256((folder/name).read_bytes()).hexdigest()!=expected:
            raise ValueError("Frozen baseline was altered; recovery refused")
    with closing(sqlite3.connect(folder/"baseline.db")) as source, closing(sqlite3.connect(database)) as destination:
        source.backup(destination)
    shutil.copy2(folder/"rules.json",configuration)


def inspect_state(database, configuration):
    with closing(sqlite3.connect(database)) as connection:
        plans=[json.loads(r[0]) for r in connection.execute("SELECT record FROM saved_plans ORDER BY plan_id")]
        portfolios=[{"cash":r[0],"holdings":json.loads(r[1])} for r in connection.execute("SELECT cash,holdings FROM simulated_portfolios")]
        ledger=[{"plan_id":r[0],"before":json.loads(r[1]),"after":json.loads(r[2])} for r in connection.execute("SELECT plan_id,before_json,after_json FROM simulated_ledger ORDER BY approval_id")]
    return {"configuration_id":json.loads(Path(configuration).read_text())["configuration_id"],
            "configuration_sha256":hashlib.sha256(Path(configuration).read_bytes()).hexdigest(),
            "saved_plans":[{"plan_id":p["plan_id"],"version_sha256":hashlib.sha256(json.dumps(p,sort_keys=True).encode()).hexdigest()} for p in plans],
            "portfolios":portfolios,"ledger":ledger}
