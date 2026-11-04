"""F.6.4 Persist Reviewed Investment Plan, performed by C.6.4 Plan Repository Component.

Satisfies CS6.1.4.4; also the C.6.4 part of CS6.1.1.3.

ICOM from the second-level IDEF0 of F.6:
    input      IO.6.2 Authorized Plan Save Payload (from F.6.3, over IF.6.3)
    control    Plan Save Request (from X.1, over EF.22)
    output     IO.6.3 Plan Persistence Result (to F.6.5, over IF.6.4)
    mechanism  C.6.4 Plan Repository Component, given a plan store

The plan store holds saved plans only. It never reads or writes simulated cash
or holdings, and nothing here contacts a brokerage (SR-05, 1.4.8, CS6.2.4).
"""

import json
import sqlite3
from contextlib import closing
from dataclasses import asdict
from datetime import datetime, timezone
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


class SqlitePlanStore:
    """Keeps saved plans in one SQLite database file, in the table saved_plans.

    The record is stored as JSON text exactly as F.6.4 wrote it; the time of
    the save is kept beside it, not inside it, so a read-back can be compared
    with what was written.
    """

    def __init__(self, database_path: Path) -> None:
        self.database_path = Path(database_path)

    def write(self, plan_id: str, record: dict) -> None:
        saved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with closing(self._connect()) as connection, connection:  # one transaction: all or nothing
            connection.execute(
                "INSERT INTO saved_plans (plan_id, saved_at, record) VALUES (?, ?, ?) "
                "ON CONFLICT(plan_id) DO UPDATE SET saved_at = excluded.saved_at, record = excluded.record",
                (plan_id, saved_at, json.dumps(record)),  # key order kept, so the plan reads back as shown
            )

    def read(self, plan_id: str) -> dict | None:
        try:
            with closing(self._connect()) as connection:
                row = connection.execute("SELECT record FROM saved_plans WHERE plan_id = ?", (plan_id,)).fetchone()
            return None if row is None else json.loads(row[0])
        except (OSError, sqlite3.Error, ValueError):  # unreadable, or not a whole JSON record
            return None

    def list_saved(self, limit: int = 20) -> list[dict]:
        """The most recent saved plans, newest first, for the investor to review."""
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT plan_id, saved_at, record FROM saved_plans ORDER BY saved_at DESC, plan_id LIMIT ?", (limit,)
            ).fetchall()
        listing = []
        for plan_id, saved_at, text in rows:
            try:
                record = json.loads(text)
            except ValueError:
                continue
            listing.append({
                "plan_id": plan_id,
                "saved_at": saved_at,
                "risk_category": record.get("risk_category"),
                "risk_score": record.get("risk_score"),
                "target_allocation": record.get("target_allocation", {}),
            })
        return listing

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path)
        connection.execute(
            "CREATE TABLE IF NOT EXISTS saved_plans "
            "(plan_id TEXT PRIMARY KEY, saved_at TEXT NOT NULL, record TEXT NOT NULL)"
        )
        return connection


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
    except (OSError, sqlite3.Error) as error:
        return result(FAILED, f"write failed: {error}")

    stored = plan_store.read(plan_id)
    if stored != record:
        return result(FAILED, "read-back did not match the reviewed plan")
    return result(SUCCEEDED, "persisted and read back in full", stored)
