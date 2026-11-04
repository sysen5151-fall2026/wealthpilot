"""Run WealthPilot.

    python app.py --serve    the browser app at http://127.0.0.1:8000 (UC.1 for a real investor)
    python app.py            UC.1 once in the terminal with the sample investor, who saves the plan
    python app.py --no-save  the same, but the investor never asks to save, so nothing is saved

The plan needs the price snapshot in data/prices/ (scripts/fetch_price_snapshot.py).
Saved plans go to data/wealthpilot.db, or to the file named by WEALTHPILOT_DATABASE.
"""

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="WealthPilot educational investment-planning simulator.")
    parser.add_argument("--serve", action="store_true", help="start the browser app")
    parser.add_argument("--host", default="127.0.0.1", help="address to serve on (default 127.0.0.1, this computer only)")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-save", action="store_true", help="console run: the investor does not send a Plan Save Request")
    args = parser.parse_args()

    if args.serve:
        import uvicorn

        from wealthpilot_service.api import create_app

        print(f"WealthPilot is running at http://{args.host}:{args.port}  (press Ctrl+C to stop)")
        uvicorn.run(create_app(), host=args.host, port=args.port, log_level="warning")
        return 0

    from investment_plan_management import language_model_from_environment
    from wealthpilot_service import PlanWithheld, run_investment_planning_session

    try:
        run_investment_planning_session(
            save_requested=not args.no_save, language_model=language_model_from_environment()
        )
    except PlanWithheld:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
