# Deployment notes

WealthPilot is built to run on one computer: `python app.py --serve` listens on 127.0.0.1, keeps in-progress sessions in memory, and stores saved plans and simulated portfolios in the SQLite file `data/wealthpilot.db`. There is no sign-in. That is enough for a demo, a pilot session on a lab machine, or a grader running the repository.

## Before hosting it for other people

| What changes on a shared host | Why it matters | What to do |
| --- | --- | --- |
| Several people use one server | There is no sign-in, so every visitor can list every saved plan | Add accounts, or scope saved plans to a session token, before inviting anyone |
| Serverless platforms (for example Vercel functions) start and stop instances per request | Sessions in memory are lost between requests, and the local disk is temporary, so saved plans would disappear | Run on a host with a long-running process and a persistent disk, or move sessions and both tables to a hosted database |
| LM Studio runs on a laptop | A hosted server cannot reach `localhost:1234` on someone's laptop | Leave `WEALTHPILOT_LLM_MODEL` unset (the template is used), or serve the chosen model from the host |
| Front end and API on different origins | The browser blocks the calls unless the API allows that origin | Set `apiBase` in `frontend/config.js` and add CORS middleware for that one origin in `wealthpilot_service/api.py` |

## Running it on a lab or demo machine

```bash
python app.py --serve --host 0.0.0.0 --port 8000   # reachable from other machines on the same network
```

Use this only on a trusted network, for the reasons in the table. Back up `data/wealthpilot.db` together with the configuration ID and the price snapshot ID if a pilot needs to be reproduced or restored (N-06).
