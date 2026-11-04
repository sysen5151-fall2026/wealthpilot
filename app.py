"""Run UC.1 once.

    python app.py            the investor sends an explicit Plan Save Request
    python app.py --no-save  the investor never asks to save, so nothing is saved
"""

import argparse

from wealthpilot_service import run_investment_planning_session


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the WealthPilot UC.1 walking skeleton.")
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="the investor does not send a Plan Save Request",
    )
    args = parser.parse_args()
    run_investment_planning_session(save_requested=not args.no_save)


if __name__ == "__main__":
    main()
