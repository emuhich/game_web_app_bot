// Общая авторизация: читает window.__verifiedAuth, если нет — пытается вызвать /api/auth
export async function ensureAuth() {
  if (window.__verifiedAuth?.ok) return window.__verifiedAuth;
  const tg = window.Telegram?.WebApp;
  const initData = tg?.initData || '';
  if (!initData) return { ok: false };
  try {
    const res = await fetch('/api/auth', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ initData })
    });
    if (!res.ok) return { ok: false };
    const data = await res.json();
    window.__verifiedAuth = { ok: true, telegram_id: data.telegram_id, profile: data.profile };
    return window.__verifiedAuth;
  } catch {
    return { ok: false };
  }
}

export function getVerifiedId() {
  return window.__verifiedAuth?.telegram_id || null;
}

