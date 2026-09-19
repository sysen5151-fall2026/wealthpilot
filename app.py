from wealthpilot_service import generate_investment_plan

def run_investment_planning():
    plan = generate_investment_plan()
    print(plan)

if __name__ == "__main__":
    run_investment_planning()