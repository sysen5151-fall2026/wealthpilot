from wealthpilot_service import generate_investment_plan

def Wealthpilot():
    plan = generate_investment_plan()
    print(plan)

if __name__ == "__main__":
    Wealthpilot()