// Input hygiene shared by the API routes.
const str = (v, max) => (typeof v === 'string' ? v.slice(0, max).trim() : '');
const list = (v, maxItems = 10, maxLen = 60) =>
  Array.isArray(v) ? v.slice(0, maxItems).map((x) => str(x, maxLen)).filter(Boolean) : [];

export function cleanProfile(p = {}) {
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

export function profileBlock(p) {
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

export const MAX_TURNS = 20;
export const MAX_MSG_CHARS = 4000;

export function cleanMessages(messages) {
  if (!Array.isArray(messages) || messages.length === 0 || messages.length > MAX_TURNS * 2) return null;
  const out = [];
  for (const m of messages) {
    if (!m || (m.role !== 'user' && m.role !== 'assistant') || typeof m.content !== 'string') return null;
    out.push({ role: m.role, content: m.content.slice(0, m.role === 'user' ? MAX_MSG_CHARS : 12000) });
  }
  return out;
}

export const json = (data, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });
