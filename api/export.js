import { loadSessions, storeEnabled } from './_lib/store.js';
import { json } from './_lib/validate.js';

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
  const header = ['started', 'country', 'job', 'seniority', 'institution', 'objectives', 'asset_classes', 'models',
    'qc_knowledge', 'pain_points', 'goals', 'user_turns', 'most_useful', 'wants_kit', 'would_return', 'email', 'comment'];
  const rows = sessions.map((s) => [
    s.startedAt, s.country, s.profile.job, s.profile.seniority, s.profile.institution,
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
