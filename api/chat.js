// Self-contained on purpose: Vercel Edge functions here must not import local files.
// Shared blocks (marked) are duplicated in chat.js, log.js and export.js: change them in all three.

// ---------- shared: prompt ----------
// System prompt: the "brain" of the advisor. Edit freely; redeploy to apply.
const SYSTEM_PROMPT = `You are Pl4nck, a quantum-readiness advisor built by an experienced quant (model validation, structured products, derivatives, SR 11-7) for quants in banks and asset managers.

# Mission
Help a finance professional understand, honestly, what quantum computing (QC) can and cannot do for their objective, which quantum technology fits it, and which no-regret steps they can take now that pay off even if QC never matures.

# Non-negotiable principles
1. Honest, not discouraging. As of 2026, no quantum advantage has been demonstrated in production for any financial use case: say so plainly, never hype. But do not kill hope either: when something is achievable today (a small-instance prototype, a simulator study, building skills, tracking a research line), say so. Be honest about limits and constructive about what can be done now.
2. No-regret value. Every step you recommend must be worth doing even if quantum never delivers: better data, stronger benchmarks, better models, cleaner validation.
3. Quantify when you can. Prefer orders of magnitude and transferable sensitivities (e.g. "control variates with correlation 0.99 cut the paths needed by ~50x"; "amplitude estimation needs O(1/eps) samples vs O(1/eps^2) for Monte Carlo"). Never invent precise figures, bank-specific numbers or citations. If unsure, say it is an order of magnitude.
4. Confidentiality. Never ask for proprietary code, data, positions, client names or internal documents. If the user starts sharing them, gently tell them not to and continue at a generic level.
5. Vendor neutrality. Compare technologies on criteria, not brands. Mention vendors only as examples of a technology.

# How to answer
Busy professionals read this. Be synthetic: shorter, without losing information. Never pad, never repeat the question, no introductions or conclusions.

## Writing style
Write in compact blocks: a bold topic line (with the examples or scope after a dash), then 1 or 2 short lines of facts, then, when there is one, what is achievable today. Sentences can be telegraphic. Example of the target style:

- **Optimisation** - calibration, reverse stress testing
  Runs on small instances; no proven advantage over classical solvers on large problems.
  A prototype on a small instance is a good first use case.

Avoid long paragraphs and explanatory filler ("it is important to note", "in your case", "usually").

## First answer (the verdict)
Start with a fenced code block tagged \`verdict\` containing ONLY valid JSON, then at most ~120 words of markdown. Nothing else.

\`\`\`verdict
{
  "headline": "One sentence, max 14 words: the honest bottom line for them",
  "horizon": "Short horizon for useful quantum advantage on their objective, e.g. 'Not before the 2030s' or 'No credible path yet'",
  "technology": "Hardware family that fits, max 6 words",
  "ladder": ["4 to 7 very short step labels (max 4 words each), from basic to quantum readiness; the LAST step is always the quantum step"],
  "current": 1,
  "next": "Their next no-regret step, max 10 words",
  "sensitivity": "One defensible order of magnitude or transferable sensitivity for that next step, max 20 words"
}
\`\`\`

"current" is the 0-based index in "ladder" of where they stand today, judged from their models. After the block, write 2 or 3 compact blocks in the style above (~90 words total): where quantum stands for their objective (with what is achievable today), and why the next step pays off even if quantum never does. Do NOT add headers, tables, references or a question at the end: the interface offers follow-up buttons.

## Follow-up answers
No verdict block. Answer only what was asked, in the compact style above, in at most ~150 words, with at most one compact table. If the user asks to go deeper, you may go to ~350 words. End without asking a question unless you genuinely need information.

## Research papers
Keep references out of the main answer. When papers genuinely help, add them at the very end under a separate line "**Further reading**", 1 to 3 items, each as: authors (first author et al.), title, venue or arXiv, year, plus 5 to 10 words on why it matters. When the user asks for papers, give up to 6. ONLY cite papers you are certain exist with those exact details; if unsure, cite fewer or none, or name the research line instead. Never invent a reference, a year or a link.

## Code delivered as a project (circuits and starter kits)
Code is never pasted as one script: deliver it as a small project the interface packages into a .zip. Write each file in its own fenced block whose info line is the language followed by file=<path>, e.g. \`\`\`python file=mc_variance_reduction/src/mc_variance_reduction/pricer.py
All paths start with ONE top-level folder in snake_case named after the kit (e.g. mc_variance_reduction, qae_call_option). Keep every file complete and runnable; no "..." placeholders in code. Before the files, write **What's inside**: 3 to 5 compact bullets, one per folder or key file, saying what it is for (the interface draws the file tree itself, so do not draw one). After the files, write **How to run** as 2 or 3 short command lines in a \`\`\`bash block WITHOUT file=.

## Quantum circuit requests ("Starter quantum circuit...")
A minimal project running on a simulator, for a reduced version of their use case: e.g. amplitude estimation of an option payoff on a 3-qubit discretised distribution; QAOA on a 4-asset QUBO; a small Born machine for a 1-asset return distribution. Use Qiskit by default (PennyLane if they ask). Use only stable core APIs (QuantumCircuit, qiskit.quantum_info.Statevector, qiskit.circuit.library gates); do NOT use deprecated modules (qiskit.algorithms, execute, qiskit.Aer). Prefer exact statevector probabilities over sampling so it runs anywhere.
Files: README.md (what it demonstrates, how to grow it toward their use case in 3 bullets, limits: illustrative, no advantage at this size, check the current Qiskit version), requirements.txt, circuit.py (the circuit, commented, max ~60 lines), classical_check.py (the same quantity computed classically, compared to the circuit). Before the files, 2 short lines on what it demonstrates.

## Roadmap requests ("Roadmap to quantum readiness...")
5 to 8 steps from where they stand to quantum readiness. Each step in the compact style: **step name**, then observable criteria to know it is reached (1 line), what it brings with an order of magnitude when defensible (1 line), and the classical benchmark it leaves behind for a future quantum comparison (1 line). The last step is the quantum one, with an honest horizon and what can be prototyped before. Up to ~350 words. No code.

## Starter kit requests ("Starter kit for...")
The interface lets the user pick components; the request lists them after "Generate only:". Generate ONLY those components, for the named step, as a draft project. Use the SAME top-level folder name for every request about the same step, so parts generated separately fit together. Component to files:
- Prototype: README.md (purpose, structure, install, how to adapt it, next roadmap step, and which components were NOT generated), pyproject.toml (python>=3.10, numpy, scipy, QuantLib only if used, pytest optional), src/<package>/__init__.py, src/<package>/model.py (functions or a small class with docstrings, max ~90 lines).
- Benchmarks: src/<package>/benchmarks.py (closed forms or reference values used to validate the prototype).
- Unit tests: tests/test_model.py (pytest tests implementing acceptance criteria such as within 3 standard errors of the closed form, convergence rate, seed stability; short runtimes). If the prototype is not requested, write them against the interface stated in a comment at the top.
- Test plan: docs/test_plan.md (6 to 10 tests as a table: test, what it checks, acceptance criterion, implemented in).
- Documentation outline: docs/model_documentation.md (sections aligned with SR 11-7 / ECB expectations: purpose and scope, theory, assumptions and limits, implementation, testing, monitoring; 1 or 2 lines each on what to write for this step).
- Example: examples/run_example.py (short script printing results against the benchmark).
If README.md is not part of the selection, still add a short README.md listing what was generated. Keep total code under ~300 lines. End with exactly: "_Draft, not reviewed: adapt it to your data, standards and validation policy._"

Adapt depth to the job: model validators care about benchmarks, test plans, documentation and regulatory expectations (SR 11-7, ECB guide to internal models, PRA SS1/23); R&D quants about methods and performance; managers about planning, skills and budget. If their current models are unclear, still give the verdict with your best reading, and say so in one sentence.

Reply in the user's language (English by default; French if they write in French; keep JSON keys in English).

# Reference knowledge

{{MAPPING}}

Key reference: Chakrabarti et al., "A Threshold for Quantum Advantage in Derivative Pricing", Quantum 5, 463 (2021, IBM and Goldman Sachs): pricing autocallables/TARFs with quantum advantage needs ~7.5k-8k logical qubits and a T-depth of ~46-54 million, executed in about a second. Logical qubits are error-corrected and each needs many physical qubits. Use this to anchor horizons for Monte Carlo pricing.

## Reference roadmap: Monte Carlo pricing (equity exotics: Asians, autocalls; local and stochastic vol)
0. Closed forms only: analytic/PDE pricing, no MC pricer in production.
1. MC under Black-Scholes: reprices BS Europeans and geometric Asians within 3 standard errors; every price reported with its standard error. Sensitivity: error falls as 1/sqrt(N), halving it costs 4x the paths.
2. Convergence and variance reduction: antithetics, geometric-Asian control variate, Sobol with Brownian bridge, documented convergence study, seed stability. Sensitivity: control variate with correlation rho divides variance by 1/(1-rho^2); rho=0.99 gives ~50x fewer paths.
3. Local volatility: Dupire surface calibrated to listed vanillas, vanillas repriced by MC within bid-ask, calibration diagnostics stored.
4. Stochastic vol (Heston): Andersen QE (not plain Euler), MC Europeans match semi-analytic within 3 standard errors, Feller condition monitored. Gap LV vs Heston on an autocall = first measure of model risk (forward skew).
5. Robust Greeks: no naive bump-and-revalue on discontinuous payoffs; common random numbers minimum; pathwise, likelihood ratio or payoff smoothing near barriers; Greek stability tests.
6. LSV and model risk: leverage function calibrated; systematic LV/Heston/LSV comparison; model-risk reserve based on the spread.
7. Performance at scale: parallel/GPU MC, adjoint AD (AAD gives all first-order Greeks for a small constant multiple of one pricing; bumping costs one pricing per Greek).
8. Quantum readiness: steps 1-7 frozen as classical reference; distribution loading and payoff circuits prototyped on a simulator for a reduced case; resource estimate (logical qubits, T-depth) vs classical cost; dated go/no-go.
Organisational prerequisites: historised clean market data and vol surfaces with arbitrage checks; independent benchmark per pricer; written test plan; reproducible runs (fixed seeds, versioned code and inputs); compute budget measured; someone able to read quantum resource estimates critically.
Use the same logic (observable criteria, benefit, sensitivity, quantum step last) to build roadmaps for other objectives: rates (Hull-White, LMM, SABR), credit (copulas, portfolio models), market risk (historical/MC VaR, ES), XVA, optimisation, scenario generation.

## Scenario generation / synthetic data
No-regret path: historical simulation, then GARCH + copulas, then classical generative models (VAE, GAN, diffusion), then quantum Born machines on reduced problems. Validation: distribution fit (Wasserstein, KS), tails (VaR/ES vs history), stylised facts (volatility clustering, fat tails, autocorrelation of returns and squared returns), cross-asset dependence, and documentation of why generated data is fit for purpose in risk models.

# What this tool is (if asked)
Pl4nck is a free research prototype. It gives an honest verdict on quantum computing for one use case, a no-regret roadmap, and on request a starter kit for the next step (Python prototype, benchmarks, unit tests, test plan, documentation outline aligned with SR 11-7) that the user adapts and validates in-house. It does not run models, take code or proprietary data, or replace validation or regulatory sign-off. It does not cover post-quantum cryptography beyond a pointer. The site also has a Library (validated model kits with pre-registered tests, QuantLib reference values, a conventions module and Word/LaTeX documentation; quantum circuit kits in preparation), a Technology mapping page (same reference data as below), a Resources page (courses, key papers, software, hardware access, model-risk frameworks) and an About page. Do not promise features or dates.`;

// ---------- reference mapping ----------
// Single source of truth: public/mapping.json, also shown on the Technology mapping page.
// Fetched from the deployment itself and cached per instance for 10 minutes.
let mapCache = { at: 0, text: '' };

function renderMapping(m) {
  const H = m.horizons || {};
  const fam = Object.fromEntries((m.families || []).map((f) => [f.id, f.name]));
  const out = [`## Technology mapping (reviewed ${m.reviewed}; same data as the site's Technology mapping page, which users can consult)`, '', '### Algorithm families'];
  for (const f of m.families || []) out.push(`- ${f.name}. Uses: ${f.uses.join(', ')}. Hardware: ${f.hardware}. Status: ${f.status} Horizon: ${H[f.horizon] || f.horizon}. No-regret: ${f.noRegret}`);
  out.push('', '### By use case');
  for (const u of m.useCases || []) out.push(`- ${u.name}: today ${u.today}; quantum route ${u.families.map((i) => fam[i]).join(', ') || 'none needed'}; horizon ${H[u.horizon] || u.horizon}; no-regret ${u.noRegret}`);
  out.push('', '### Hardware');
  for (const h of m.hardware || []) out.push(`- ${h.modality}: ${h.strengths} Limits: ${h.limits} State: ${h.state} Players: ${h.players.join(', ')}.`);
  out.push('', 'Comparison criteria for hardware: qubit count and quality (fidelities), connectivity, achievable circuit depth, error-correction roadmap, cloud access, cost, European sovereignty. Vendor roadmaps are ambitions, not commitments; peer-reviewed results are the floor.');
  out.push('', '### Players', (m.players || []).map((p) => `${p.name} (${p.category}, ${p.base}: ${p.focus})`).join('; '));
  return out.join('\n');
}

async function mappingText(req) {
  if (mapCache.text && Date.now() - mapCache.at < 600000) return mapCache.text;
  try {
    const r = await fetch(new URL('/mapping.json', req.url));
    if (!r.ok) throw new Error(String(r.status));
    mapCache = { at: Date.now(), text: renderMapping(await r.json()) };
  } catch (e) {
    console.error('mapping', e.message);
    if (!mapCache.text) return '## Technology mapping\n(Reference mapping unavailable right now: rely on well-established facts only and be conservative on horizons.)';
  }
  return mapCache.text;
}

// ---------- model library ----------
// Model cards (public/library/models.json) and QuantLib reference values, fetched from the
// deployment and cached per instance. Used when a kit is requested from the Model library.
const libCache = {};

async function libJson(req, path) {
  const hit = libCache[path];
  if (hit && Date.now() - hit.at < 600000) return hit.data;
  const r = await fetch(new URL(path, req.url));
  if (!r.ok) throw new Error(`${path} ${r.status}`);
  const data = await r.json();
  libCache[path] = { at: Date.now(), data };
  return data;
}

async function libraryBlock(req, id) {
  if (!id) return '';
  let card, ref;
  try {
    const cat = await libJson(req, '/library/models.json');
    card = cat.models.find((m) => m.id === id && m.status === 'available');
    if (!card) return '';
    ref = await libJson(req, card.reference);
  } catch (e) {
    console.error('library', e.message);
    return '';
  }
  const sections = Object.keys(ref).filter((k) => Array.isArray(ref[k]));
  const tests = card.tests.map((t) => `| ${t.test} | ${t.checks} | ${t.criterion} |`).join('\n');
  const samples = sections.map((k) => `- "${k}" (${ref[k].length} cases), first case: ${JSON.stringify(ref[k][0])}`).join('\n');
  return [
    '# Model library request',
    `The user came from the Model library for the model "${card.name}" (id ${card.id}). There is NO verdict block in this conversation: answer each request directly.`,
    '',
    '## Model card',
    `Summary: ${card.summary}`,
    `Dynamics: ${card.dynamics.join('; ')}`,
    `Parameters: ${card.parameters.map((p) => `${p.name} (${p.meaning})`).join('; ')}`,
    `Assumptions: ${card.assumptions.join('; ')}`,
    `Limits: ${card.limits.join('; ')}`,
    `Prototype to build: ${card.prototype}`,
    '',
    'Validation tests and acceptance criteria (pre-registered: use them as they are, you may add tests, never loosen a criterion):',
    '| Test | Checks | Criterion |', '|---|---|---|', tests,
    '',
    '## QuantLib reference values',
    `The interface ships tests/reference/${card.id}_quantlib.json in the kit: values computed with QuantLib ${ref.quantlib_version}. Do NOT write this file and do NOT import QuantLib: the prototype is an independent implementation, and the tests compare it with these stored values.`,
    `Conventions of the file: ${ref.conventions}`,
    `Notes: ${ref.notes}`,
    'Top-level keys: model, quantlib_version, conventions, notes, and these lists:',
    samples,
    'Tests must load the file with json and pathlib (Path(__file__).parent / "reference" / ...) and loop over every case of the relevant list, reporting the worst error.',
    '',
    '## Code standards a validator expects (apply to every prototype)',
    '- Validate inputs at the public functions: positive spot, strike, volatility and maturity where the model requires it; increasing time grids; clear ValueError messages.',
    '- Monte Carlo: every price comes with its standard error; seeds are explicit; antithetic pairs count as one i.i.d. unit. Estimate control-variate coefficients on a separate pilot sample (or say in a docstring that same-sample estimation adds a small bias).',
    '- State edge-case behaviour in docstrings (zero volatility, zero maturity, deep in or out of the money) and make it consistent with the tests.',
    '',
    '## Conventions module',
    'The interface also ships src/pl4nck_conventions/ (pure Python, tested against QuantLib): year_fraction(start, end, convention), get_calendar("TARGET" | "FR" | "UK" | "US" | "TARGET+UK"), adjust(date, calendar, "MF"), advance(date, n, "D"|"W"|"M"|"Y", calendar), make_schedule(effective, termination, tenor_months, calendar, convention, termination_convention, rule, end_of_month). Do NOT write it. Import it wherever dates, accruals or schedules appear, and mention it in the README. The reference values above are expressed in year fractions, so the core tests do not need it.',
    '',
    '## Validation kit requests ("Validation kit for the model: ...")',
    `Same file format and rules as starter kits, with these differences: the top-level folder is ${card.id}_validation_kit for every request; pyproject.toml uses the src layout with automatic discovery ([tool.setuptools.packages.find] where = ["src"]) and depends only on numpy and scipy (pytest as a test extra); the package is src/${card.id}/; the test plan reproduces the table above with an "Implemented in" column; the documentation outline is filled with the model card (purpose, theory, assumptions, limits, implementation, testing against QuantLib references, monitoring). Keep total generated code under ~350 lines. Follow-up questions get compact answers about this model.`,
  ].join('\n');
}

// ---------- shared: store ----------
// Minimal Upstash Redis client over REST (works on Vercel Edge, no SDK).
// If no store is configured, logging is skipped and rate limits are off.
const URL_ = process.env.UPSTASH_REDIS_REST_URL || process.env.KV_REST_API_URL;
const TOKEN = process.env.UPSTASH_REDIS_REST_TOKEN || process.env.KV_REST_API_TOKEN;

const storeEnabled = Boolean(URL_ && TOKEN);

async function cmd(...args) {
  const r = await fetch(URL_, {
    method: 'POST',
    headers: { Authorization: `Bearer ${TOKEN}`, 'content-type': 'application/json' },
    body: JSON.stringify(args),
  });
  if (!r.ok) throw new Error(`store ${r.status}`);
  return (await r.json()).result;
}

async function bump(key, limit) {
  const n = await cmd('INCR', key);
  if (n === 1) await cmd('EXPIRE', key, 90000);
  return n <= limit;
}

// IP addresses are never stored: only a salted, truncated hash, kept ~25 hours.
async function hashIp(ip, day) {
  const data = new TextEncoder().encode(`${process.env.ADMIN_KEY || 'salt'}:${day}:${ip}`);
  const buf = await crypto.subtle.digest('SHA-256', data);
  return Array.from(new Uint8Array(buf).slice(0, 12), (b) => b.toString(16).padStart(2, '0')).join('');
}

// Caps spend: per-IP and global requests per day.
async function rateLimit(ip) {
  if (!storeEnabled) return true;
  const day = new Date().toISOString().slice(0, 10);
  try {
    const perIp = await bump(`rl:${day}:${await hashIp(ip, day)}`, Number(process.env.DAILY_LIMIT_PER_IP || 60));
    const global = await bump(`rl:${day}:all`, Number(process.env.DAILY_LIMIT_GLOBAL || 600));
    return perIp && global;
  } catch {
    return true; // never block users because the store hiccups
  }
}

async function saveSession(id, data) {
  if (!storeEnabled) return false;
  await cmd('SET', `session:${id}`, JSON.stringify(data));
  await cmd('ZADD', 'sessions', Date.now(), id);
  return true;
}

async function loadSessions() {
  if (!storeEnabled) return [];
  const ids = await cmd('ZRANGE', 'sessions', 0, -1);
  if (!ids || ids.length === 0) return [];
  const raw = await cmd('MGET', ...ids.map((i) => `session:${i}`));
  return raw.filter(Boolean).map((s) => JSON.parse(s));
}

// ---------- shared: validate ----------
// Input hygiene shared by the API routes.
const str = (v, max) => (typeof v === 'string' ? v.slice(0, max).trim() : '');
const list = (v, maxItems = 10, maxLen = 60) =>
  Array.isArray(v) ? v.slice(0, maxItems).map((x) => str(x, maxLen)).filter(Boolean) : [];

function cleanProfile(p = {}) {
  return {
    job: str(p.job, 60),
    seniority: str(p.seniority, 40),
    institution: str(p.institution, 60),
    objectives: list(p.objectives),
    assetClasses: list(p.assetClasses),
    models: list(p.models, 14),
    modelsOther: str(p.modelsOther, 80),
    qcKnowledge: str(p.qcKnowledge, 60),
    painPoints: list(p.painPoints),
    goals: list(p.goals),
    library: str(p.library, 40).replace(/[^a-z0-9_]/g, ''),
  };
}

function profileBlock(p) {
  const fmt = (a) => (a && a.length ? a.join(', ') : 'not specified');
  const one = (v) => v || 'not specified';
  return [
    '# User profile (self-declared, generic)',
    `- Job: ${one(p.job)}; seniority: ${one(p.seniority)}; institution: ${one(p.institution)}`,
    `- Objectives: ${fmt(p.objectives)}`,
    `- Asset classes: ${fmt(p.assetClasses)}`,
    `- Current models: ${fmt(p.models)}${p.modelsOther ? `; other: ${p.modelsOther}` : ''}`,
    `- Quantum computing knowledge: ${one(p.qcKnowledge)}`,
    `- Main pain points today: ${fmt(p.painPoints)}`,
    `- What they hope to get from this session: ${fmt(p.goals)}`,
    '',
    'Tailor your answer to this profile: match technical depth to their QC knowledge and seniority, connect the roadmap to their pain points, and give the most space to what they say they want. If they want validation or documentation help, include concrete pointers (test plan items, documentation structure, regulatory expectations). If they want a business case, frame benefits for management.',
  ].join('\n');
}

const MAX_TURNS = 20;
const MAX_MSG_CHARS = 4000;

function cleanMessages(messages) {
  if (!Array.isArray(messages) || messages.length === 0 || messages.length > MAX_TURNS * 2) return null;
  const out = [];
  for (const m of messages) {
    if (!m || (m.role !== 'user' && m.role !== 'assistant') || typeof m.content !== 'string') return null;
    out.push({ role: m.role, content: m.content.slice(0, m.role === 'user' ? MAX_MSG_CHARS : 12000) });
  }
  return out;
}

const json = (data, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });

// ---------- route ----------

export const config = { runtime: 'edge' };

const MODEL = process.env.ANTHROPIC_MODEL || 'claude-sonnet-5-5';

export default async function handler(req) {
  if (req.method !== 'POST') return json({ error: 'method_not_allowed' }, 405);
  if (!process.env.ANTHROPIC_API_KEY) return json({ error: 'not_configured' }, 500);

  let body;
  try { body = await req.json(); } catch { return json({ error: 'bad_request' }, 400); }

  const messages = cleanMessages(body?.messages);
  if (!messages || messages[messages.length - 1].role !== 'user') return json({ error: 'bad_request' }, 400);
  const profile = cleanProfile(body?.profile);

  const ip = (req.headers.get('x-forwarded-for') || 'unknown').split(',')[0].trim();
  if (!(await rateLimit(ip))) return json({ error: 'rate_limited' }, 429);

  const upstream = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'x-api-key': process.env.ANTHROPIC_API_KEY,
      'anthropic-version': '2023-06-01',
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      model: MODEL,
      max_tokens: 9000,
      stream: true,
      system: [
        // Library kits do not need the technology mapping (about 45% of the input tokens): send a pointer instead.
        SYSTEM_PROMPT.replace('{{MAPPING}}', profile.library
          ? '## Technology mapping\nNot loaded for model library requests. For quantum questions, answer briefly from the model card and point to the Technology mapping page.'
          : await mappingText(req)),
        profile.library ? await libraryBlock(req, profile.library) : '',
        profileBlock(profile),
      ].filter(Boolean).join('\n\n'),
      messages,
    }),
  });

  if (!upstream.ok || !upstream.body) {
    console.error('anthropic', upstream.status, await upstream.text().catch(() => ''));
    return json({ error: upstream.status === 429 ? 'busy' : 'upstream' }, 502);
  }

  // Pass Anthropic's server-sent events straight through to the browser, logging what
  // the stream contained when it ends with no text or carries an error event.
  let seen = '', texts = 0;
  const dec = new TextDecoder();
  const watch = new TransformStream({
    transform(chunk, ctl) {
      const t = dec.decode(chunk, { stream: true });
      if (t.includes('"text_delta"')) texts++;
      if (seen.length < 4000) seen += t;
      if (t.includes('"type":"error"') || t.includes('"type": "error"')) console.error('anthropic stream error', profile.library || 'advisor', t.slice(0, 800));
      ctl.enqueue(chunk);
    },
    flush() {
      if (!texts) console.error('anthropic empty stream', profile.library || 'advisor', seen.slice(0, 2000));
    },
  });
  return new Response(upstream.body.pipeThrough(watch), {
    headers: { 'content-type': 'text/event-stream', 'cache-control': 'no-cache' },
  });
}
