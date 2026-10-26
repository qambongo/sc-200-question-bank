// GET    /api/progress                      -> { progress: { <questionId>: "1:<ts>" | "0:<ts>" } }
// POST   /api/progress { set: { id: value } } -> saves answers (merged into the stored hash)
// DELETE /api/progress                      -> erases all saved answers
const { redis, currentUser, send, handler } = require('./_lib/store');

const ID_RE = /^[a-f0-9]{10}$/;
const VALUE_RE = /^[01]:\d{1,12}$/;
const MAX_PER_REQUEST = 2000;

module.exports = handler(async (req, res) => {
  const username = await currentUser(req);
  if (!username) return send(res, 401, { error: 'Sign in to save progress.' });
  const key = `progress:${username}`;

  if (req.method === 'GET') {
    const flat = (await redis('HGETALL', key)) || [];
    const progress = {};
    for (let i = 0; i < flat.length; i += 2) progress[flat[i]] = flat[i + 1];
    return send(res, 200, { progress });
  }

  if (req.method === 'POST') {
    const entries = Object.entries((req.body && req.body.set) || {});
    if (entries.length > MAX_PER_REQUEST) return send(res, 413, { error: 'Too many answers in one request.' });
    if (!entries.every(([id, v]) => ID_RE.test(id) && VALUE_RE.test(String(v)))) {
      return send(res, 400, { error: 'Invalid progress data.' });
    }
    if (entries.length) await redis('HSET', key, ...entries.flatMap(([id, v]) => [id, String(v)]));
    return send(res, 200, { saved: entries.length });
  }

  if (req.method === 'DELETE') {
    await redis('DEL', key);
    return send(res, 200, { ok: true });
  }

  return send(res, 405, { error: 'Method not allowed' });
});
