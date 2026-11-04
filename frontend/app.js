// WealthPilot front end: X.1 Individual Investor's side of UC.1.
// Four legs: About you (F.1 inputs), Your answers (F.1 questionnaire, then F.2), Your risk profile
// (Profile Interpretation Confirmation, then F.3 to F.6.2), Your plan (Plan Save Request, then F.6.3 to F.6.5).
"use strict";

(() => {
  const API = (window.WEALTHPILOT_CONFIG && window.WEALTHPILOT_CONFIG.apiBase) || "";
  const DRAFT_KEY = "wealthpilot-draft";
  const FIELD_ORDER = ["goal", "horizon_years", "investable_savings", "monthly_contribution", "annual_income", "age", "liquidity_needs"];
  const MONEY_FIELDS = new Set(["investable_savings", "monthly_contribution", "annual_income"]);
  const CLASS_COLORS = {
    "US Stocks": "var(--class-us)",
    "International Stocks": "var(--class-intl)",
    "Bonds": "var(--class-bonds)",
    "Cash": "var(--class-cash)",
  };
  const SPARE_COLORS = ["#7a5c99", "#5e91ad", "#b0623c", "#3f7f5f"];
  const BAND_COLORS = ["var(--band-1)", "var(--band-2)", "var(--band-3)", "var(--band-4)", "var(--band-5)"];
  const LEGS = [
    ["about", "About you"],
    ["answers", "Your answers"],
    ["risk", "Your risk profile"],
    ["plan", "Your plan"],
  ];

  const state = {
    view: "planner",
    step: "intro",
    status: null,
    sessionId: null,
    requests: null,
    draft: loadDraft(),
    errors: [],
    risk: null,
    plan: null,
    withheld: null,
    save: null,
    trace: [],
    busy: false,
    saved: null,
    savedDetail: null,
  };

  const main = document.getElementById("main");

  // Helpers

  function esc(value) {
    return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  }
  const usdFormat = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
  const usd = (amount) => usdFormat.format(amount || 0);
  const pct = (share, digits = 0) => `${(share * 100).toFixed(digits)}%`;
  const capitalize = (text) => (text ? text.charAt(0).toUpperCase() + text.slice(1) : "");
  const classColor = (name, index) => CLASS_COLORS[name] || SPARE_COLORS[index % SPARE_COLORS.length];

  function loadDraft() {
    try {
      const saved = JSON.parse(sessionStorage.getItem(DRAFT_KEY) || "null");
      if (saved && typeof saved === "object") return { profile: saved.profile || {}, answers: saved.answers || {}, holdings: saved.holdings || [] };
    } catch (error) { /* storage unavailable: start empty */ }
    return { profile: {}, answers: {}, holdings: [] };
  }

  function saveDraft() {
    try { sessionStorage.setItem(DRAFT_KEY, JSON.stringify(state.draft)); } catch (error) { /* not essential */ }
  }

  async function api(path, options = {}) {
    let response;
    try {
      response = await fetch(API + path, {
        method: options.method || "GET",
        headers: options.body ? { "Content-Type": "application/json" } : undefined,
        body: options.body ? JSON.stringify(options.body) : undefined,
      });
    } catch (error) {
      throw new Error("WealthPilot's server is not responding. Check that it is still running (python app.py --serve), then try again.");
    }
    const data = await response.json().catch(() => ({}));
    if (response.status === 404 && path.startsWith("/api/sessions/")) {
      state.sessionId = null;
      throw new Error("This planning session has ended, for example because the server restarted. Start planning again; your answers are kept.");
    }
    if (!response.ok && response.status !== 422) {
      throw new Error(typeof data.detail === "string" ? data.detail : `The server answered with an error (${response.status}).`);
    }
    return { status: response.status, data };
  }

  function setTrace(trace) {
    if (Array.isArray(trace)) state.trace = trace;
    const list = document.getElementById("trace-list");
    list.innerHTML = state.trace.length
      ? state.trace.map((step) => `<li><span class="trace-tag${step.tag.startsWith("X.") ? " is-external" : ""}">${esc(step.tag)}</span><span><b>${esc(step.name)}</b>: ${esc(step.output)}</span></li>`).join("")
      : `<li><span class="trace-tag">–</span><span>Start planning to see each step.</span></li>`;
  }

  function go(step) {
    state.step = step;
    state.errors = [];
    render();
    window.scrollTo(0, 0);
    const heading = main.querySelector("h1");
    if (heading) { heading.setAttribute("tabindex", "-1"); heading.focus({ preventScroll: true }); }
  }

  // Views

  function render() {
    document.querySelectorAll(".nav-link").forEach((link) => {
      if (link.dataset.nav === state.view) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
    if (state.view === "saved") {
      main.innerHTML = state.savedDetail ? savedDetailView() : savedListView();
    } else {
      main.innerHTML = ({ intro: introView, about: aboutView, answers: answersView, risk: riskView, plan: planView })[state.step]();
    }
    if (state.view === "planner" && state.step === "risk") placeScoreMarker();
    renderColophon();
  }

  function route(current) {
    const index = LEGS.findIndex(([key]) => key === current);
    return `<ol class="route" aria-label="Steps">${LEGS.map(([key, label], i) => {
      const status = i < index ? "is-done" : i === index ? "is-current" : "";
      return `<li class="${status}"${i === index ? ' aria-current="step"' : ""}>${esc(label)}</li>`;
    }).join("")}</ol>`;
  }

  function errorsBlock() {
    if (!state.errors.length) return "";
    return `<div class="errors" role="alert"><b>Please fix ${state.errors.length === 1 ? "this" : "these"} first:</b><ul>${state.errors.map((e) => `<li>${esc(e)}</li>`).join("")}</ul></div>`;
  }

  function introView() {
    const data = state.status && state.status.market_data;
    const unavailable = data && !data.available;
    return `
      <h1>Build a practice investment plan</h1>
      <p class="lede">Answer a few questions about your money and how you feel about risk. WealthPilot turns your answers into a simulated plan and explains why it looks the way it does. Nothing is bought or sold.</p>
      ${route(null)}
      ${unavailable ? `<div class="limitations" role="status"><b>Plans can't be built yet.</b><p>${esc(data.problem)}</p></div>` : ""}
      ${errorsBlock()}
      <div class="actions">
        <button type="button" class="button button-primary" data-action="start"${state.busy ? " disabled" : ""}>Start planning</button>
        <span class="muted small">Takes about five minutes. Hypothetical numbers are fine.</span>
      </div>`;
  }

  function aboutView() {
    const fields = state.requests.financial_profile_fields;
    const names = [...FIELD_ORDER.filter((name) => fields[name]), ...Object.keys(fields).filter((name) => !FIELD_ORDER.includes(name))];
    const choiceFields = names.filter((name) => fields[name].type === "choice");
    const numberFields = names.filter((name) => fields[name].type !== "choice");
    const holdings = state.draft.holdings;
    return `
      ${route("about")}
      <h1>About you</h1>
      <p class="lede">These answers set the goal, time frame and amounts the plan works with.</p>
      ${errorsBlock()}
      <form class="sheet" data-form="about" novalidate>
        ${choiceFields.slice(0, 1).map((name) => choiceField(name, fields[name])).join("")}
        <div class="field-grid" style="margin-top:1.5rem">${numberFields.map((name) => numberField(name, fields[name])).join("")}</div>
        ${choiceFields.slice(1).map((name) => `<div style="margin-top:1.5rem">${choiceField(name, fields[name])}</div>`).join("")}
        <h2>What you already hold</h2>
        <p class="muted small">Add investments you already have, with their value in dollars, or leave this empty. Up to ${esc(state.requests.current_holdings.max_holdings)}.</p>
        ${holdings.length ? `
        <table class="holdings">
          <thead><tr><th scope="col">Ticker symbol</th><th scope="col">Value (USD)</th><th scope="col"><span class="visually-hidden">Remove</span></th></tr></thead>
          <tbody>${holdings.map((holding, i) => `
            <tr>
              <td><input type="text" aria-label="Ticker symbol ${i + 1}" data-holding="${i}" data-key="symbol" value="${esc(holding.symbol)}" maxlength="10" autocapitalize="characters" spellcheck="false" placeholder="VTI" style="text-transform:uppercase"></td>
              <td><input type="number" aria-label="Value of holding ${i + 1} in USD" data-holding="${i}" data-key="value" value="${esc(holding.value)}" min="0" step="any" inputmode="decimal"></td>
              <td><button type="button" class="button button-quiet" data-action="remove-holding" data-index="${i}">Remove</button></td>
            </tr>`).join("")}
          </tbody>
        </table>` : ""}
        <div class="actions" style="margin-top:0.75rem"><button type="button" class="button" data-action="add-holding">Add a holding</button></div>
      </form>
      <div class="actions">
        <button type="button" class="button button-primary" data-action="to-answers">Continue to the questions</button>
      </div>`;
  }

  function numberField(name, spec) {
    const value = state.draft.profile[name];
    const step = spec.type === "integer" ? "1" : "any";
    const hint = MONEY_FIELDS.has(name) ? "Hypothetical amounts are fine." : `${Number(spec.min).toLocaleString("en-US")} to ${Number(spec.max).toLocaleString("en-US")}`;
    return `
      <div class="field">
        <label for="f-${esc(name)}">${esc(spec.label)}</label>
        <input id="f-${esc(name)}" type="number" data-profile="${esc(name)}" value="${esc(value ?? "")}" min="${esc(spec.min)}" max="${esc(spec.max)}" step="${step}" inputmode="${spec.type === "integer" ? "numeric" : "decimal"}" aria-describedby="h-${esc(name)}">
        <span class="hint" id="h-${esc(name)}">${esc(hint)}</span>
      </div>`;
  }

  function choiceField(name, spec) {
    return `
      <fieldset>
        <legend>${esc(spec.label)}</legend>
        <div class="choices">${Object.entries(spec.options).map(([id, label]) => `
          <label class="choice"><input type="radio" name="p-${esc(name)}" data-profile="${esc(name)}" value="${esc(id)}"${state.draft.profile[name] === id ? " checked" : ""}> ${esc(label)}</label>`).join("")}
        </div>
      </fieldset>`;
  }

  function answersView() {
    const questions = state.requests.risk_questionnaire;
    return `
      ${route("answers")}
      <h1>Your answers</h1>
      <p class="lede">There are no right answers. Pick what is closest to how you would really act.</p>
      ${errorsBlock()}
      <form class="sheet" data-form="answers" novalidate>
        ${questions.map((question) => `
          <fieldset class="question">
            <legend>${esc(question.text)}</legend>
            <div class="choices">${Object.entries(question.options).map(([id, label]) => `
              <label class="choice"><input type="radio" name="q-${esc(question.id)}" data-answer="${esc(question.id)}" value="${esc(id)}"${state.draft.answers[question.id] === id ? " checked" : ""}> ${esc(label)}</label>`).join("")}
            </div>
          </fieldset>`).join("")}
      </form>
      <div class="actions">
        <button type="button" class="button button-primary" data-action="submit-answers"${state.busy ? " disabled" : ""}>${state.busy ? "Scoring your answers…" : "See my risk profile"}</button>
        <button type="button" class="button button-quiet" data-action="back-about">Back to about you</button>
      </div>`;
  }

  function riskView() {
    const risk = state.risk;
    const strong = new Set(risk.strongest_factors.map((f) => f.label));
    let lower = 0;
    const bands = risk.categories.map((category, i) => {
      const width = category.max_score - lower;
      lower = category.max_score;
      return `<div class="scale-band${category.name === risk.risk_category ? " is-yours" : ""}" style="flex:${width};background:${BAND_COLORS[i % BAND_COLORS.length]}"><span>${esc(category.name)}</span></div>`;
    }).join("");
    return `
      ${route("risk")}
      <h1>Your risk profile</h1>
      <div class="score-head">
        <span class="score-number">${esc(risk.risk_score)}</span>
        <span><span class="score-category">${esc(risk.risk_category)}</span><br><span class="score-of">risk score out of 100</span></span>
      </div>
      <div class="scale" role="img" aria-label="Risk score ${esc(risk.risk_score)} of 100, in the ${esc(risk.risk_category)} band">
        <div class="scale-bands">${bands}</div>
        <div class="scale-marker" data-score="${esc(risk.risk_score)}" style="left:0"></div>
      </div>
      <h2>What moved your score</h2>
      <p class="muted">Each answer sits somewhere between more cautious and more risk-tolerant. The two that moved your score the most are in color.</p>
      <div class="factors-key small muted" aria-hidden="true"><span></span><span class="track-ends"><span>More cautious</span><span>More risk-tolerant</span></span></div>
      <ul class="factors">${risk.factors.map((factor) => `
        <li class="factor${strong.has(factor.label) ? " is-strong" : ""}">
          <span class="factor-text"><b>${esc(capitalize(factor.label))}</b><br>${esc(factor.answer)}</span>
          <span class="track" role="img" aria-label="${esc(describeLean(factor.lean))}"><span class="track-dot" style="left:${((factor.lean + 1) / 2) * 100}%"></span></span>
        </li>`).join("")}
      </ul>
      <h2>Does this describe you?</h2>
      <p class="reading">Your plan is built from this profile, including the largest one-year loss you said you could accept (${esc(pct(risk.max_one_year_loss))}). If it doesn't sound like you, change your answers first.</p>
      ${errorsBlock()}
      <div class="actions">
        <button type="button" class="button button-primary" data-action="confirm"${state.busy ? " disabled" : ""}>${state.busy ? "Building your plan…" : "Yes, build my plan"}</button>
        <button type="button" class="button" data-action="back-answers">Change my answers</button>
      </div>`;
  }

  function describeLean(lean) {
    if (lean > 0.34) return "toward more risk-tolerant";
    if (lean < -0.34) return "toward more cautious";
    return "near the middle";
  }

  function placeScoreMarker() {
    const marker = main.querySelector(".scale-marker");
    if (!marker) return;
    const score = Number(marker.dataset.score);
    requestAnimationFrame(() => requestAnimationFrame(() => { marker.style.left = `${score}%`; }));
  }

  function planView() {
    if (state.withheld) {
      return `
        ${route("plan")}
        <h1>Your plan can't be built yet</h1>
        <div class="limitations" role="status"><b>${esc(state.withheld.reason)}</b>
          <ul>${state.withheld.limitations.map((line) => `<li>${esc(line)}</li>`).join("")}</ul>
        </div>
        <p class="reading">WealthPilot does not fill gaps in price history with made-up numbers, so the plan is held back until suitable data are installed.</p>
        <div class="actions"><button type="button" class="button" data-action="back-risk">Back to your risk profile</button></div>`;
    }
    const presented = state.plan.presented_plan;
    return `
      ${route("plan")}
      <h1>Your simulated plan</h1>
      ${planBody(presented.content, state.plan.screening)}
      ${state.save && state.save.status === "saved" ? savedConfirmation() : savePanel(presented)}`;
  }

  function planBody(content, screening) {
    const explanation = content.explanation;
    const allocation = Object.entries(content.target_allocation);
    const amounts = content.simulated_amounts || {};
    const bySymbol = Object.fromEntries((amounts.by_symbol || []).map((row) => [row.symbol, row]));
    const outside = (amounts.by_symbol || []).filter((row) => !row.in_plan);
    const metrics = content.plan_metrics;
    return `
      <p class="lede">${esc(explanation.summary)}</p>
      ${allocationBar(allocation, "allocation-bar")}
      <ul class="allocation-key">${allocation.map(([name, share], i) => `
        <li><span class="swatch" style="background:${classColor(name, i)}"></span><span>${esc(name)}</span> <b>${esc(pct(share))}</b></li>`).join("")}
      </ul>

      <h2>What the plan holds</h2>
      ${amounts.total ? `<p class="muted">Amounts show what each share means for ${esc(usd(amounts.total))}: your ${esc(usd(amounts.cash))} of cash plus ${esc(usd(amounts.current_holdings_value))} you already hold. Nothing is bought or sold.</p>` : ""}
      <div class="table-wrap">
        <table class="plan-table">
          <thead><tr><th scope="col">Security</th><th scope="col">Asset class</th><th scope="col" class="num">Share</th>${amounts.total ? '<th scope="col" class="num">Simulated amount</th><th scope="col" class="num">You hold now</th>' : ""}</tr></thead>
          <tbody>
            ${content.recommendations.map((r) => `
              <tr>
                <td><span class="symbol">${esc(r.symbol)}</span><br><span class="small muted">${esc(r.name)}</span></td>
                <td>${esc(r.asset_class)}</td>
                <td class="num">${esc(pct(r.weight, 1))}</td>
                ${amounts.total ? `<td class="num">${esc(usd(bySymbol[r.symbol] ? bySymbol[r.symbol].plan : 0))}</td><td class="num">${bySymbol[r.symbol] && bySymbol[r.symbol].current ? esc(usd(bySymbol[r.symbol].current)) : "–"}</td>` : ""}
              </tr>`).join("")}
            ${outside.map((row) => `
              <tr class="is-outside">
                <td><span class="symbol">${esc(row.symbol)}</span><br><span class="small">Not part of this plan</span></td>
                <td>–</td><td class="num">0%</td><td class="num">${esc(usd(0))}</td><td class="num">${esc(usd(row.current))}</td>
              </tr>`).join("")}
          </tbody>
        </table>
      </div>
      ${screening && screening.exclusions.length ? `
        <details style="margin-top:0.75rem"><summary class="small">Securities the screen left out (${screening.exclusions.length})</summary>
          <ul class="small">${screening.exclusions.map((e) => `<li><b>${esc(e.symbol)}</b>: ${esc(e.reason)}</li>`).join("")}</ul>
        </details>` : ""}

      <h2>Why this plan</h2>
      <ul class="reading">${explanation.allocation_rationale.map((line) => `<li>${esc(line)}</li>`).join("")}</ul>

      <h2>Risks to know</h2>
      <ul class="reading">${explanation.material_risks.map((line) => `<li>${esc(line)}</li>`).join("")}</ul>

      ${explanation.historical_evidence && explanation.historical_evidence.length ? `
        <h2>What the past data show</h2>
        <ul class="reading">${explanation.historical_evidence.map((line) => `<li>${esc(line)}</li>`).join("")}</ul>` : ""}

      <h2>Data limitations</h2>
      ${explanation.data_limitations.length
        ? `<div class="limitations"><ul>${explanation.data_limitations.map((line) => `<li>${esc(line)}</li>`).join("")}</ul></div>`
        : `<p class="muted">None reported for this plan.</p>`}

      <div class="provenance">
        <dl>
          <dt>Plan</dt><dd>${esc(content.plan_id)}</dd>
          <dt>Explanation</dt><dd>Written by ${esc(explanation.generated_by)}${explanation.generation_note ? `. ${esc(explanation.generation_note)}` : ""}</dd>
          <dt>Rules</dt><dd>${esc(content.rules_configuration_id || "not recorded")}, explanation rules ${esc(explanation.rules_version)}</dd>
          <dt>Prices</dt><dd>${esc(content.data_snapshot_id || "not recorded")}${metrics ? `, ${esc(metrics.start)} to ${esc(metrics.end)}` : ""}</dd>
        </dl>
      </div>`;
  }

  function allocationBar(allocation, className) {
    const label = allocation.map(([name, share]) => `${name} ${pct(share)}`).join(", ");
    return `<div class="${className}" role="img" aria-label="${esc(label)}">${allocation.map(([name, share], i) =>
      `<span style="flex:${share};background:${classColor(name, i)}" title="${esc(name)} ${esc(pct(share))}"></span>`).join("")}</div>`;
  }

  function savePanel(presented) {
    const action = presented.learner_actions[0] || "Save this simulated plan";
    const problem = state.save && state.save.status !== "saved"
      ? `<div class="errors" role="alert"><b>The plan was not saved.</b> ${esc(state.save.detail)}</div>` : "";
    return `
      <section class="save-panel" aria-labelledby="save-heading">
        <h2 id="save-heading">${esc(action)}</h2>
        <p class="scope-inline">${esc(state.plan.scope_notice)}</p>
        <p>Saving keeps a copy of this plan so you can come back to it. It does not change your simulated cash or holdings, and nothing is saved unless you choose to.</p>
        ${problem}
        <div class="actions">
          <button type="button" class="button button-primary" data-action="save"${state.busy ? " disabled" : ""}>${state.busy ? "Saving…" : esc(action)}</button>
          <button type="button" class="button button-quiet" data-action="back-risk">Back to your risk profile</button>
        </div>
      </section>`;
  }

  function savedConfirmation() {
    const save = state.save;
    const before = save.simulated_portfolio_before;
    const after = save.simulated_portfolio_after;
    const unchanged = JSON.stringify(before) === JSON.stringify(after);
    return `
      <div class="confirmation" role="status">
        <p><b>${esc(save.confirmation.message)}</b></p>
        <p class="small muted">You can open it any time from Saved plans.</p>
      </div>
      ${after ? `
        <h2>Your simulated portfolio</h2>
        <p class="muted">${unchanged ? "Saving did not change your simulated cash or holdings." : "Your simulated cash or holdings changed while saving. Saving must never do that; please report it."}</p>
        <table class="ledger">
          <thead><tr><th scope="col">What you have</th><th scope="col">Before saving</th><th scope="col">After saving</th></tr></thead>
          <tbody>
            <tr><td>Cash</td><td>${esc(usd(before && before.cash))}</td><td>${esc(usd(after.cash))}</td></tr>
            ${after.holdings.map((h, i) => `<tr><td>${esc(h.symbol)}</td><td>${esc(usd(before && before.holdings[i] ? before.holdings[i].value : 0))}</td><td>${esc(usd(h.value))}</td></tr>`).join("")}
          </tbody>
        </table>` : ""}
      <div class="actions">
        <button type="button" class="button" data-nav="saved">See saved plans</button>
        <button type="button" class="button button-quiet" data-action="restart">Plan again with different answers</button>
      </div>`;
  }

  function savedListView() {
    if (!state.saved) return `<h1>Saved plans</h1><p class="muted">Loading…</p>`;
    if (!state.saved.length) {
      return `
        <h1>Saved plans</h1>
        <p class="lede">No saved plans yet. Plans you choose to save appear here.</p>
        <div class="actions"><button type="button" class="button button-primary" data-nav="planner">Build a plan</button></div>`;
    }
    return `
      <h1>Saved plans</h1>
      <p class="muted">Newest first. Each is a simulated plan exactly as it was shown when you saved it.</p>
      ${errorsBlock()}
      <ul class="saved-list">${state.saved.map((plan) => `
        <li>
          <button type="button" data-action="open-saved" data-plan="${esc(plan.plan_id)}">${esc(plan.risk_category)} plan, score ${esc(plan.risk_score)}</button>
          <span class="small muted"> saved ${esc(new Date(plan.saved_at).toLocaleString())}</span>
          ${allocationBar(Object.entries(plan.target_allocation || {}), "allocation-bar")}
        </li>`).join("")}
      </ul>`;
  }

  function savedDetailView() {
    const record = state.savedDetail;
    return `
      <h1>Saved plan</h1>
      <p class="muted">${esc(record.scope_notice)}</p>
      ${planBody(record, null)}
      <div class="actions"><button type="button" class="button" data-action="close-saved">Back to saved plans</button></div>`;
  }

  function renderColophon() {
    const status = state.status;
    const colophon = document.getElementById("colophon");
    if (!status) { colophon.innerHTML = ""; return; }
    const data = status.market_data;
    colophon.innerHTML = `
      <p>Rules: ${esc(status.configuration_id)}${status.placeholder_rules ? " (placeholder values, not yet approved by the team)" : ""}.</p>
      <p>Prices: ${data.available ? `${esc(data.snapshot_id)}, ${esc(data.source)}, ${esc(data.start)} to ${esc(data.end)}` : "no snapshot installed"}.</p>
      <p>Explanations: ${status.explanation.mode === "language model" ? `local language model ${esc(status.explanation.model)}, checked against the approved template` : "approved template"}.</p>`;
  }

  // Reading the forms

  function readAboutForm() {
    main.querySelectorAll("[data-profile]").forEach((input) => {
      const name = input.dataset.profile;
      if (input.type === "radio") { if (input.checked) state.draft.profile[name] = input.value; return; }
      state.draft.profile[name] = input.value === "" ? null : Number(input.value);
    });
    main.querySelectorAll("[data-holding]").forEach((input) => {
      const holding = state.draft.holdings[Number(input.dataset.holding)];
      if (!holding) return;
      if (input.dataset.key === "symbol") holding.symbol = input.value.trim().toUpperCase();
      else holding.value = input.value === "" ? null : Number(input.value);
    });
    saveDraft();
  }

  function readAnswersForm() {
    main.querySelectorAll("[data-answer]:checked").forEach((input) => { state.draft.answers[input.dataset.answer] = input.value; });
    saveDraft();
  }

  function aboutProblems() {
    const fields = state.requests.financial_profile_fields;
    const problems = [];
    for (const [name, spec] of Object.entries(fields)) {
      const value = state.draft.profile[name];
      if (value === null || value === undefined || value === "" || Number.isNaN(value)) { problems.push(`${spec.label} is required.`); continue; }
      if (spec.type === "choice") continue;
      if (spec.type === "integer" && !Number.isInteger(value)) problems.push(`${spec.label} must be a whole number.`);
      else if (value < spec.min || value > spec.max) problems.push(`${spec.label} must be between ${Number(spec.min).toLocaleString("en-US")} and ${Number(spec.max).toLocaleString("en-US")}.`);
    }
    state.draft.holdings.forEach((holding, i) => {
      if (!holding.symbol) problems.push(`Holding ${i + 1} needs a ticker symbol, or remove it.`);
      if (holding.value === null || holding.value === undefined || Number.isNaN(holding.value) || holding.value < 0) problems.push(`Holding ${i + 1} needs a value of zero or more.`);
    });
    return problems;
  }

  // Actions

  async function ensureSession() {
    if (state.sessionId) return;
    const { data } = await api("/api/sessions", { method: "POST" });
    state.sessionId = data.session_id;
    state.requests = data.requests_for_investor_input;
    state.risk = state.plan = state.withheld = state.save = null;
    setTrace(data.trace);
  }

  async function start() {
    state.busy = true; render();
    try {
      state.sessionId = null;
      await ensureSession();
      state.busy = false;
      go("about");
    } catch (error) {
      state.busy = false; state.errors = [error.message]; render();
    }
  }

  async function submitAnswers() {
    readAnswersForm();
    const missing = state.requests.risk_questionnaire.filter((q) => !state.draft.answers[q.id]);
    if (missing.length) { state.errors = missing.map((q) => `Please answer: ${q.text}`); render(); return; }
    state.busy = true; render();
    try {
      await ensureSession();
      const { status, data } = await api(`/api/sessions/${encodeURIComponent(state.sessionId)}/investor-information`, {
        method: "POST",
        body: {
          financial_profile: state.draft.profile,
          risk_questionnaire_responses: state.draft.answers,
          current_holdings: state.draft.holdings,
        },
      });
      state.busy = false;
      if (status === 422) {
        state.errors = data.errors || ["Some answers could not be used."];
        render();
        main.querySelector(".errors").scrollIntoView({ block: "center" });
        return;
      }
      state.risk = data.risk_assessment;
      state.plan = state.withheld = state.save = null;
      setTrace(data.trace);
      go("risk");
    } catch (error) {
      state.busy = false; state.errors = [error.message]; render();
    }
  }

  async function confirmProfile() {
    state.busy = true; render();
    try {
      const { data } = await api(`/api/sessions/${encodeURIComponent(state.sessionId)}/plan`, {
        method: "POST",
        body: { profile_interpretation_confirmed: true },
      });
      state.busy = false;
      state.save = null;
      setTrace(data.trace);
      if (data.status === "withheld") { state.withheld = data; state.plan = null; }
      else { state.plan = data; state.withheld = null; }
      go("plan");
    } catch (error) {
      state.busy = false; state.errors = [error.message]; render();
    }
  }

  async function savePlan() {
    state.busy = true; render();
    try {
      const { data } = await api(`/api/sessions/${encodeURIComponent(state.sessionId)}/plan-save-requests`, {
        method: "POST",
        body: { plan_id: state.plan.presented_plan.plan_id, action: "save" },
      });
      state.busy = false;
      state.save = data;
      state.saved = null;
      setTrace(data.trace);
      render();
      const target = main.querySelector(".confirmation, .save-panel .errors");
      if (target) target.scrollIntoView({ block: "center" });
    } catch (error) {
      state.busy = false; state.save = { status: "failed", detail: error.message }; render();
    }
  }

  async function showSaved() {
    state.view = "saved";
    state.savedDetail = null;
    state.errors = [];
    render();
    try {
      const { data } = await api("/api/saved-plans");
      state.saved = data.saved_plans;
    } catch (error) {
      state.saved = []; state.errors = [error.message];
    }
    render();
  }

  async function openSaved(planId) {
    try {
      const { data } = await api(`/api/saved-plans/${encodeURIComponent(planId)}`);
      state.savedDetail = { ...data.saved_plan, scope_notice: data.scope_notice };
      render();
      window.scrollTo(0, 0);
    } catch (error) {
      state.errors = [error.message]; render();
    }
  }

  // Events

  document.addEventListener("click", (event) => {
    const nav = event.target.closest("[data-nav]");
    if (nav) {
      event.preventDefault();
      if (nav.dataset.nav === "saved") { showSaved(); return; }
      state.view = "planner"; state.savedDetail = null; render(); return;
    }
    const button = event.target.closest("[data-action]");
    if (!button || button.disabled) return;
    const action = button.dataset.action;
    if (action === "start") start();
    else if (action === "add-holding") { readAboutForm(); state.draft.holdings.push({ symbol: "", value: null }); render(); const inputs = main.querySelectorAll('[data-key="symbol"]'); if (inputs.length) inputs[inputs.length - 1].focus(); }
    else if (action === "remove-holding") { readAboutForm(); state.draft.holdings.splice(Number(button.dataset.index), 1); saveDraft(); render(); }
    else if (action === "to-answers") {
      readAboutForm();
      const problems = aboutProblems();
      if (problems.length) { state.errors = problems; render(); main.querySelector(".errors").scrollIntoView({ block: "center" }); return; }
      go("answers");
    }
    else if (action === "back-about") { readAnswersForm(); go("about"); }
    else if (action === "submit-answers") submitAnswers();
    else if (action === "back-answers") go("answers");
    else if (action === "confirm") confirmProfile();
    else if (action === "back-risk") go("risk");
    else if (action === "save") savePlan();
    else if (action === "restart") { state.plan = state.save = state.withheld = null; go("about"); }
    else if (action === "open-saved") openSaved(button.dataset.plan);
    else if (action === "close-saved") { state.savedDetail = null; render(); }
  });

  main.addEventListener("change", () => {
    if (state.step === "about") readAboutForm();
    if (state.step === "answers") readAnswersForm();
  });

  // Start

  setTrace([]);
  render();
  api("/api/status")
    .then(({ data }) => {
      state.status = data;
      document.getElementById("scope-band").textContent = data.scope_notice;
      render();
    })
    .catch((error) => { state.errors = [error.message]; render(); });
})();
