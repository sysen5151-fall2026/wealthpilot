def determine_allocation(risk_score: int, profile: dict, market_data: dict) -> dict:
    return {"stocks": 0.6, "etfs": 0.4}