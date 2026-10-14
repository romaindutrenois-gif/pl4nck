import { SYSTEM_PROMPT } from './_lib/prompt.js';
import { rateLimit } from './_lib/store.js';
import { cleanProfile, profileBlock, cleanMessages, json } from './_lib/validate.js';

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
