// GET  /api/auth                                   -> { username } or { username: null }
// POST /api/auth { action: 'register', username, password }
// POST /api/auth { action: 'login', username, password }
// POST /api/auth { action: 'logout' }
const crypto = require('crypto');
const { redis, currentUser, createSession, destroySession, hashPassword, send, handler } = require('./_lib/store');

const USERNAME_RE = /^[a-z0-9._-]{3,32}$/;
const MAX_ATTEMPTS = 10;
const ATTEMPT_WINDOW_SECONDS = 15 * 60;

function attemptKey(req, username) {
  const ip = String(req.headers['x-forwarded-for'] || '').split(',')[0].trim() || 'unknown';
  return `ratelimit:auth:${ip}:${username}`;
}

async function tooManyAttempts(req, username) {
  const key = attemptKey(req, username);
  const count = await redis('INCR', key);
  if (count === 1) await redis('EXPIRE', key, ATTEMPT_WINDOW_SECONDS);
  return count > MAX_ATTEMPTS;
}

module.exports = handler(async (req, res) => {
  if (req.method === 'GET') {
    return send(res, 200, { username: await currentUser(req) });
  }
  if (req.method !== 'POST') return send(res, 405, { error: 'Method not allowed' });

  const body = req.body || {};
  if (body.action === 'logout') {
    await destroySession(req, res);
    return send(res, 200, { ok: true });
  }

  const username = String(body.username || '').trim().toLowerCase();
  const password = String(body.password || '');
  if (!USERNAME_RE.test(username)) {
    return send(res, 400, { error: 'Username must be 3-32 characters: letters, numbers, dot, dash or underscore.' });
  }
  if (password.length < 8 || password.length > 200) {
    return send(res, 400, { error: 'Password must be at least 8 characters.' });
  }
  if (await tooManyAttempts(req, username)) {
    return send(res, 429, { error: 'Too many attempts. Wait 15 minutes and try again.' });
  }

  if (body.action === 'register') {
    const salt = crypto.randomBytes(16).toString('hex');
    const record = JSON.stringify({ salt, hash: await hashPassword(password, salt), created: Date.now() });
    const created = await redis('SET', `user:${username}`, record, 'NX');
    if (created !== 'OK') return send(res, 409, { error: 'That username is taken.' });
    await createSession(res, username);
    return send(res, 200, { username });
  }

  if (body.action === 'login') {
    const record = JSON.parse((await redis('GET', `user:${username}`)) || 'null');
    const expected = record ? Buffer.from(record.hash, 'hex') : crypto.randomBytes(64);
    const actual = Buffer.from(await hashPassword(password, record ? record.salt : 'none'), 'hex');
    if (!record || !crypto.timingSafeEqual(expected, actual)) {
      return send(res, 401, { error: 'Wrong username or password.' });
    }
    await redis('DEL', attemptKey(req, username));
    await createSession(res, username);
    return send(res, 200, { username });
  }

  return send(res, 400, { error: 'Unknown action' });
});
