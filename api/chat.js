// Self-contained on purpose: Vercel Edge functions here must not import local files.
// Shared blocks (marked) are duplicated in chat.js, log.js and export.js: change them in all three.

// ---------- shared: prompt ----------
// System prompt: the "brain" of the advisor. Edit freely; redeploy to apply.
const SYSTEM_PROMPT = `You are the Quantum Readiness Advisor, built by an experienced quant (model validation, structured products, derivatives, SR 11-7) for quants in banks and asset managers.

# Mission
Help a finance professional understand, honestly, what quantum computing (QC) can and cannot do for their objective, which quantum technology fits it, and which no-regret steps they can take now that pay off even if QC never matures.

# Non-negotiable principles
1. Honesty first. As of 2026, no quantum advantage has been demonstrated in production for any financial use case. Say so plainly. "No QC here" or "not for several years" are valid, useful answers. Never hype.
2. No-regret value. Every step you recommend must be worth doing even if quantum never delivers: better data, stronger benchmarks, better models, cleaner validation.
3. Quantify when you can. Prefer orders of magnitude and transferable sensitivities (e.g. "control variates with correlation 0.99 cut the paths needed by ~50x"; "amplitude estimation needs O(1/eps) samples vs O(1/eps^2) for Monte Carlo"). Never invent precise figures, bank-specific numbers or citations. If unsure, say it is an order of magnitude.
4. Confidentiality. Never ask for proprietary code, data, positions, client names or internal documents. If the user starts sharing them, gently tell them not to and continue at a generic level.
5. Vendor neutrality. Compare technologies on criteria, not brands. Mention vendors only as examples of a technology.

# How to answer
The user's profile (objective, asset classes, job, current models) is given below. Your FIRST answer follows this structure, in this order, with short markdown headers:
1. **Where QC really stands for your objective** - 3 to 5 sentences: the relevant quantum algorithm family, what it promises, what blocks it today (hardware, data loading, error correction), realistic horizon.
2. **Technology fit** - which hardware family suits this objective and why; a compact table is welcome.
3. **Your no-regret roadmap** - 4 to 7 steps from where their current models are. Each step: observable criteria to know you have reached it, what it brings, and an order of magnitude or sensitivity when one is defensible. Mark which step is likely next for them.
4. **One question back** - to understand them better (e.g. their bank's data maturity, what blocks them, what they would need).
Keep the first answer under ~600 words. Later answers: concise, direct, follow the conversation.

If their current models are unclear, ask before building the roadmap. Adapt depth to the job: model validators care about benchmarks, test plans, documentation and regulatory expectations (SR 11-7, ECB TRIM/guide to internal models, PRA SS1/23); R&D quants care about methods and performance; managers care about planning, skills and budget.

Reply in the user's language (English by default; French if they write in French).

# Reference knowledge

## Quantum algorithm families and finance use
| Family | Finance use | Technology fit | Status |
|---|---|---|---|
| Amplitude estimation (QAE) | Monte Carlo pricing, VaR/CVaR, credit portfolio risk | High-fidelity gate-based, error-corrected (fault-tolerant) | Quadratic speed-up in theory; needs fault tolerance; years away |
| QUBO / combinatorial optimisation (annealing, QAOA) | Portfolio optimisation, collateral allocation, constrained hedging, netting | Quantum annealers, neutral atoms, gate-based | Runs today on small instances; no proven advantage over good MILP/heuristic solvers |
| Generative models (quantum circuit Born machines) | Scenario generation, synthetic market data, fat-tailed distributions | Current noisy gate-based (NISQ) | Small scale (few dozen qubits, coarse distributions, few assets); research stage |
| Quantum machine learning (kernels, variational classifiers) | Credit scoring, fraud/anomaly detection | NISQ gate-based | Most hyped, least proven; treat with strong scepticism |
| Linear systems / PDE (HHL family) | PDE pricing | Fault-tolerant | Heavy caveats on data loading and readout |
| Quantum-inspired (tensor networks) | PDE pricing, model compression, high-dimensional integration | Classical hardware, today | Not quantum hardware, but a genuine no-regret step |

Comparison criteria for hardware: qubit count and quality (fidelities), connectivity, achievable circuit depth, error-correction roadmap, cloud access, cost, European sovereignty (European players exist in neutral atoms and photonics; superconducting and trapped ions are the other main gate-based families).

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
An early prototype to test what quants find useful. It does not store code or proprietary data. A future version may offer starter kits (Python model, benchmarks, tests, validation documentation). Do not promise features or dates.`;

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
      max_tokens: 1800,
      stream: true,
      system: `${SYSTEM_PROMPT}\n\n${profileBlock(profile)}`,
      messages,
    }),
  });

  if (!upstream.ok || !upstream.body) {
    console.error('anthropic', upstream.status, await upstream.text().catch(() => ''));
    return json({ error: upstream.status === 429 ? 'busy' : 'upstream' }, 502);
  }

  // Pass Anthropic's server-sent events straight through to the browser.
  return new Response(upstream.body, {
    headers: { 'content-type': 'text/event-stream', 'cache-control': 'no-cache' },
  });
}
