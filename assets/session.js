/* Shows the signed-in user and a Sign out button in the top navigation.
   window.sessionUser resolves to the username (or null) for page scripts that need it. */
window.sessionUser = fetch('/api/auth', { credentials: 'same-origin' })
  .then(res => res.json())
  .then(data => data.username || null)
  .catch(() => null);

async function signOutOfSite() {
  try {
    await fetch('/api/auth', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'logout' }),
    });
  } catch (e) {}
  location.href = 'login.html';
}

window.sessionUser.then(username => {
  const slot = document.querySelector('.site-nav-end');
  if (!slot || !username || slot.dataset.session === 'custom') return;
  const chip = document.createElement('span');
  chip.className = 'user-chip';
  const avatar = document.createElement('span');
  avatar.className = 'avatar';
  avatar.textContent = username.charAt(0);
  const name = document.createElement('span');
  name.className = 'name';
  name.textContent = username;
  chip.append(avatar, name);
  const out = document.createElement('button');
  out.type = 'button';
  out.className = 'btn-secondary btn-sm';
  out.textContent = 'Sign out';
  out.onclick = signOutOfSite;
  slot.replaceChildren(chip, out);
});
