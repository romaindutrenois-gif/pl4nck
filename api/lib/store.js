// Minimal Upstash Redis client over REST (works on Vercel Edge, no SDK).
// If no store is configured, logging is skipped and rate limits are off.
const URL_ = process.env.UPSTASH_REDIS_REST_URL || process.env.KV_REST_API_URL;
const TOKEN = process.env.UPSTASH_REDIS_REST_TOKEN || process.env.KV_REST_API_TOKEN;

export const storeEnabled = Boolean(URL_ && TOKEN);

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
export async function rateLimit(ip) {
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

export async function saveSession(id, data) {
  if (!storeEnabled) return false;
  await cmd('SET', `session:${id}`, JSON.stringify(data));
  await cmd('ZADD', 'sessions', Date.now(), id);
  return true;
}

export async function loadSessions() {
  if (!storeEnabled) return [];
  const ids = await cmd('ZRANGE', 'sessions', 0, -1);
  if (!ids || ids.length === 0) return [];
  const raw = await cmd('MGET', ...ids.map((i) => `session:${i}`));
  return raw.filter(Boolean).map((s) => JSON.parse(s));
}
