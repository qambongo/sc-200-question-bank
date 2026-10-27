// Vercel Routing Middleware: every page needs a signed-in session. Anyone without
// one is sent to /login.html. The API routes check the session themselves.
import { next } from '@vercel/functions';
import store from './api/_lib/store.js';

export const config = {
  runtime: 'nodejs',
  matcher: ['/((?!api/|login\\.html$|assets/site\\.css$).*)'],
};

export default async function middleware(request) {
  let username = null;
  try {
    username = await store.currentUser({ headers: { cookie: request.headers.get('cookie') || '' } });
  } catch (err) {
    console.error(err);
  }
  if (username) return next();

  const url = new URL(request.url);
  const login = new URL('/login.html', url);
  if (url.pathname !== '/') login.searchParams.set('next', url.pathname + url.search);
  return Response.redirect(login, 307);
}
