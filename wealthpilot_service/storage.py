"""Local storage for the running product: one SQLite file holds both tables.

    saved_plans            written only by C.6.4 (investment_plan_management.SqlitePlanStore)
    simulated_portfolios   the investor's simulated cash and holdings, one row per session

The simulated portfolio is recorded when the investor enters or corrects their
information (F.1). Nothing on the plan-save path (F.6.3 to F.6.5) writes it,
so saving a plan leaves simulated cash and holdings unchanged (SR-05).
Applying a simulated change would need its own explicit approval (SR-06),
which UC.1 does not include.
"""

import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DATABASE_PATH = Path(
    os.environ.get("WEALTHPILOT_DATABASE", Path(__file__).resolve().parent.parent / "data" / "wealthpilot.db")
)


class SimulatedPortfolioStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = Path(database_path)

    def record(self, session_id: str, cash: float, holdings: list[dict]) -> None:
        recorded_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with closing(self._connect()) as connection, connection:
            connection.execute(
                "INSERT INTO simulated_portfolios (session_id, cash, holdings, recorded_at) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(session_id) DO UPDATE SET cash = excluded.cash, holdings = excluded.holdings, "
                "recorded_at = excluded.recorded_at",
                (session_id, float(cash), json.dumps(holdings, sort_keys=True), recorded_at),
            )

    def read(self, session_id: str) -> dict | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT cash, holdings, recorded_at FROM simulated_portfolios WHERE session_id = ?", (session_id,)
            ).fetchone()
        if row is None:
            return None
        cash, holdings, recorded_at = row
        return {"session_id": session_id, "cash": cash, "holdings": json.loads(holdings), "recorded_at": recorded_at}

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path)
        connection.execute(
            "CREATE TABLE IF NOT EXISTS simulated_portfolios "
            "(session_id TEXT PRIMARY KEY, cash REAL NOT NULL, holdings TEXT NOT NULL, recorded_at TEXT NOT NULL)"
        )
        return connection
