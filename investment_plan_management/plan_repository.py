"""F.6.4 Persist Reviewed Investment Plan, performed by C.6.4 Plan Repository Component.

Satisfies CS6.1.4.4; also the C.6.4 part of CS6.1.1.3.

ICOM from the second-level IDEF0 of F.6:
    input      IO.6.2 Authorized Plan Save Payload (from F.6.3, over IF.6.3)
    control    Plan Save Request (from X.1, over EF.22)
    output     IO.6.3 Plan Persistence Result (to F.6.5, over IF.6.4)
    mechanism  C.6.4 Plan Repository Component, given a plan store

The plan store holds saved plans only. It never reads or writes simulated cash
or holdings, and nothing here contacts a brokerage (1.4.8, CS6.2.4).
"""

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Protocol

from .io_types import (
    FAILED,
    REJECTED,
    SUCCEEDED,
    AuthorizedPlanSavePayload,
    PlanPersistenceResult,
    PlanSaveRequest,
)


class PlanStore(Protocol):
    """Where C.6.4 keeps saved plans."""

    def write(self, plan_id: str, record: dict) -> None: ...

    def read(self, plan_id: str) -> dict | None: ...


class JsonPlanStore:
    """Keeps each saved plan in its own JSON file: <directory>/<plan_id>.json."""

    def __init__(self, directory: Path) -> None:
        self.directory = Path(directory)

    def write(self, plan_id: str, record: dict) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self._path(plan_id)
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_text(json.dumps(record, indent=2, sort_keys=True))
        os.replace(temporary, path)  # the final file is never half-written

    def read(self, plan_id: str) -> dict | None:
        try:
            return json.loads(self._path(plan_id).read_text())
        except (OSError, json.JSONDecodeError):  # missing, unreadable or half-written
            return None

    def _path(self, plan_id: str) -> Path:
        return self.directory / f"{plan_id}.json"


def persist_reviewed_investment_plan(
    authorized_plan_save_payload: AuthorizedPlanSavePayload,
    *,
    plan_save_request: PlanSaveRequest,
    plan_store: PlanStore,
) -> PlanPersistenceResult:
    """Save the reviewed plan and report success only after a full read-back."""
    plan_id = authorized_plan_save_payload.reviewed_plan.plan_id

    def result(status: str, detail: str, persisted_plan: dict | None = None) -> PlanPersistenceResult:
        return PlanPersistenceResult(
            status=status,
            plan_id=plan_id,
            request_id=plan_save_request.request_id,
            persisted_plan=persisted_plan,
            detail=detail,
        )

    if authorized_plan_save_payload.authorization != plan_save_request:
        return result(REJECTED, "the payload was not authorized by this Plan Save Request")

    record = asdict(authorized_plan_save_payload.reviewed_plan)
    try:
        plan_store.write(plan_id, record)
    except OSError as error:
        return result(FAILED, f"write failed: {error}")

    stored = plan_store.read(plan_id)
    if stored != record:
        return result(FAILED, "read-back did not match the reviewed plan")
    return result(SUCCEEDED, "persisted and read back in full", stored)
