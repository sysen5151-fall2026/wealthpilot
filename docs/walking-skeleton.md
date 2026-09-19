# UC.1 — Investor obtains target allocation and securities recommendations
# Internally, the wealthpilot_service is decomposed into four functional modules—risk_engine, allocation_engine, screening_engine, and ai_explanation_model—which are not external systems on the context diagram.
1. Investor → investor_interface: initiate_session()
2. investor_interface → wealthpilot_service: request_financial_profile(session_id)
3. Investor → investor_interface: provide_financial_profile(profile_data)
4. wealthpilot_service → investor_interface: request_risk_questionnaire()
5. Investor → investor_interface: provide_risk_questionnaire(response)
6. wealthpilot_service → risk_engine: determine_risk_score(profile, questionnaire)
7. risk_engine → wealthpilot_service: returns risk_score
8. wealthpilot_service → investor_interface: present_risk_score(risk_score)
9. Investor → investor_interface: confirm_risk_score()
10. wealthpilot_service → market_data_provider: get_historical_prices(tickers, period)
11. market_data_provider → wealthpilot_service: returns historical_price_data
12. wealthpilot_service → allocation_engine: determine_allocation(risk_score, profile, market_data)
13. allocation_engine → wealthpilot_service: returns target_allocation
14. wealthpilot_service → screening_engine: filter_securities(target_allocation, market_data)
15. screening_engine → wealthpilot_service: returns recommendation_list
16. wealthpilot_service → ai_explanation_model: compose_explanation(allocation, recommendations)
17. ai_explanation_model → wealthpilot_service: returns explanation_text
18. wealthpilot_service → investor_interface: provide_investment_plan(allocation, recommendations, explanation)
19. Investor → investor_interface: save_and_confirm()
20. wealthpilot_service → investor_interface: save_investment_plan(plan_data)