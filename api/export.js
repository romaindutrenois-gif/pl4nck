// Self-contained on purpose: Vercel Edge functions here must not import local files.
// Shared blocks (marked) are duplicated in chat.js, log.js and export.js: change them in all three.

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

// Private export of all sessions: /api/export?key=YOUR_ADMIN_KEY  (add &format=csv for a summary table)
export default async function handler(req) {
  const url = new URL(req.url);
  const key = process.env.ADMIN_KEY;
  if (!key || url.searchParams.get('key') !== key) return json({ error: 'forbidden' }, 403);
  if (!storeEnabled) return json({ error: 'no_store_configured' }, 500);

  const sessions = await loadSessions();
  if (url.searchParams.get('format') !== 'csv') return json(sessions);

  const cell = (v) => `"${String(v ?? '').replace(/"/g, '""').replace(/\s+/g, ' ')}"`;
  const j = (a) => (a || []).join('; ');
  const header = ['started', 'country', 'library_model', 'job', 'seniority', 'institution', 'objectives', 'asset_classes', 'models',
    'qc_knowledge', 'pain_points', 'goals', 'user_turns', 'most_useful', 'wants_kit', 'would_return', 'email', 'comment'];
  const rows = sessions.map((s) => [
    s.startedAt, s.country, s.profile.library || '', s.profile.job, s.profile.seniority, s.profile.institution,
    j(s.profile.objectives), j(s.profile.assetClasses),
    [...(s.profile.models || []), s.profile.modelsOther].filter(Boolean).join('; '),
    s.profile.qcKnowledge, j(s.profile.painPoints), j(s.profile.goals),
    s.messages.filter((m) => m.role === 'user').length,
    s.feedback.mostUseful.join('; '), s.feedback.wantsKit, s.feedback.wouldReturn, s.feedback.email, s.feedback.comment,
  ].map(cell).join(','));

  return new Response([header.join(','), ...rows].join('\n'), {
    headers: { 'content-type': 'text/csv; charset=utf-8', 'content-disposition': 'attachment; filename="sessions.csv"' },
  });
}
