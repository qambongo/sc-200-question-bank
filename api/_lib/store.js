// Shared helpers for the auth and progress endpoints.
// Data lives in Upstash Redis (provisioned through the Vercel Marketplace), reached
// over its REST API so the functions need no npm dependencies.
const crypto = require('crypto');

const SESSION_COOKIE = 'sp_session';
const SESSION_TTL_SECONDS = 60 * 60 * 24 * 30;

function redisConfig() {
  const url = process.env.KV_REST_API_URL || process.env.UPSTASH_REDIS_REST_URL;
  const token = process.env.KV_REST_API_TOKEN || process.env.UPSTASH_REDIS_REST_TOKEN;
  if (!url || !token) throw Object.assign(new Error('Progress storage is not configured'), { status: 503 });
  return { url, token };
}

async function redis(...command) {
  const { url, token } = redisConfig();
  const res = await fetch(url, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(command),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok || data.error) throw new Error(`Redis ${command[0]} failed: ${data.error || res.status}`);
  return data.result;
}

function parseCookies(header) {
  const out = {};
  (header || '').split(';').forEach(part => {
    const i = part.indexOf('=');
    if (i > 0) out[part.slice(0, i).trim()] = decodeURIComponent(part.slice(i + 1).trim());
  });
  return out;
}

function sessionCookie(token, maxAge) {
  return `${SESSION_COOKIE}=${token}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${maxAge}`;
}

function sessionToken(req) {
  const token = parseCookies(req.headers.cookie)[SESSION_COOKIE];
  return token && /^[a-f0-9]{64}$/.test(token) ? token : null;
}

async function currentUser(req) {
  const token = sessionToken(req);
  if (!token) return null;
  return (await redis('GET', `session:${token}`)) || null;
}

async function createSession(res, username) {
  const token = crypto.randomBytes(32).toString('hex');
  await redis('SET', `session:${token}`, username, 'EX', SESSION_TTL_SECONDS);
  res.setHeader('Set-Cookie', sessionCookie(token, SESSION_TTL_SECONDS));
}

async function destroySession(req, res) {
  const token = sessionToken(req);
  if (token) await redis('DEL', `session:${token}`);
  res.setHeader('Set-Cookie', sessionCookie('', 0));
}

function hashPassword(password, salt) {
  return new Promise((resolve, reject) => {
    crypto.scrypt(password, salt, 64, (err, key) => (err ? reject(err) : resolve(key.toString('hex'))));
  });
}

function send(res, status, body) {
  res.setHeader('Cache-Control', 'no-store');
  res.status(status).json(body);
}

function handler(fn) {
  return async (req, res) => {
    try {
      await fn(req, res);
    } catch (err) {
      if (!err.status) console.error(err);
      send(res, err.status || 500, { error: err.status ? err.message : 'Server error, please try again' });
    }
  };
}

module.exports = { redis, currentUser, createSession, destroySession, hashPassword, send, handler };
