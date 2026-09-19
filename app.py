from wealthpilot_service import generate_investment_plan

def run_investor_kiosk():
    plan = generate_investment_plan()
    print(plan)

if __name__ == "__main__":
    run_investor_kiosk()