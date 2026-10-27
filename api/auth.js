// GET  /api/auth                                -> { username } or { username: null }
// POST /api/auth { action: 'login', username, password }
// POST /api/auth { action: 'logout' }
// There is a single account, configured with the SITE_USERNAME / SITE_PASSWORD env vars.
const { redis, currentUser, checkCredentials, createSession, destroySession, send, handler } = require('./_lib/store');

const MAX_ATTEMPTS = 10;
const ATTEMPT_WINDOW_SECONDS = 15 * 60;

function attemptKey(req) {
  const ip = String(req.headers['x-forwarded-for'] || '').split(',')[0].trim() || 'unknown';
  return `ratelimit:auth:${ip}`;
}

async function tooManyAttempts(req) {
  const key = attemptKey(req);
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
  if (body.action !== 'login') return send(res, 400, { error: 'Unknown action' });

  const username = String(body.username || '').trim();
  const password = String(body.password || '');
  if (!username || !password) return send(res, 400, { error: 'Enter your username and password.' });
  if (await tooManyAttempts(req)) {
    return send(res, 429, { error: 'Too many attempts. Wait 15 minutes and try again.' });
  }

  const account = checkCredentials(username, password);
  if (!account) return send(res, 401, { error: 'Wrong username or password.' });
  await redis('DEL', attemptKey(req));
  await createSession(res, account);
  return send(res, 200, { username: account });
});
