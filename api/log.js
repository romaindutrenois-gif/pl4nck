import { saveSession } from './_lib/store.js';
import { cleanProfile, cleanMessages, json } from './_lib/validate.js';

export const config = { runtime: 'edge' };

const str = (v, max) => (typeof v === 'string' ? v.slice(0, max).trim() : '');

// Stores one session (overwritten on each update). Only called after consent.
export default async function handler(req) {
  if (req.method !== 'POST') return json({ error: 'method_not_allowed' }, 405);
  let b;
  try { b = await req.json(); } catch { return json({ error: 'bad_request' }, 400); }

  const id = str(b?.sessionId, 64);
  if (!/^[a-f0-9-]{16,64}$/i.test(id) || b?.consent !== true) return json({ ok: false }, 400);

  const f = b?.feedback || {};
  const record = {
    id,
    updatedAt: new Date().toISOString(),
    startedAt: str(b?.startedAt, 40),
    consentVersion: str(b?.consentVersion, 20),
    country: req.headers.get('x-vercel-ip-country') || '',
    lang: str(b?.lang, 20),
    profile: cleanProfile(b?.profile),
    messages: cleanMessages(b?.messages) || [],
    feedback: {
      mostUseful: Array.isArray(f.mostUseful) ? f.mostUseful.slice(0, 8).map((x) => str(x, 60)) : [],
      wantsKit: str(f.wantsKit, 20),
      wouldReturn: str(f.wouldReturn, 20),
      comment: str(f.comment, 1500),
      email: str(f.email, 120),
    },
  };

  try {
    const stored = await saveSession(id, record);
    return json({ ok: true, stored });
  } catch (e) {
    console.error('log', e);
    return json({ ok: false }, 500);
  }
}
