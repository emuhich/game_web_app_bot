// Расширенная инициализация Telegram Mini App с поддержкой полноэкранного режима (Bot API 8.0)
(function(){
  const MAX_RETRIES = 12;
  const RETRY_DELAY = 160; // ms
  let attempt = 0;

  function isFsEnabled(tg){
    try {
      const fs = tg.isFullscreen !== undefined ? tg.isFullscreen : tg.isFullscreen?.();
      return !!fs;
    } catch { return false; }
  }

  function updateSafeArea(){
    const tg = window.Telegram?.WebApp; if (!tg) return;
    const root = document.documentElement; if (!root) return;
    const sa = tg.safeAreaInset || tg.contentSafeAreaInset || {};
    if (sa.top != null) root.style.setProperty('--safe-top', sa.top + 'px');
    if (sa.bottom != null) root.style.setProperty('--safe-bottom', sa.bottom + 'px');
    if (sa.left != null) root.style.setProperty('--safe-left', sa.left + 'px');
    if (sa.right != null) root.style.setProperty('--safe-right', sa.right + 'px');
  }

  function tryFullscreen(){
    const tg = window.Telegram?.WebApp; if (!tg) return false;
    try {
      tg.ready?.();
      tg.setHeaderColor?.('bg_color'); // скрываем заголовок

      // Сначала поднимаем BottomSheet (если открыт как панель)
      if (tg.expand && !tg.isExpanded) {
        tg.expand();
      }

      // Если доступен API 8.0 и метод requestFullscreen — просим полноэкран
      if (tg.isVersionAtLeast?.('8.0') && tg.requestFullscreen) {
        if (!isFsEnabled(tg)) {
          tg.requestFullscreen();
        }
      }

      updateSafeArea();
      return true;
    } catch (e) {
      console.warn('[telegram_init] fullscreen attempt error', e);
      return false;
    }
  }

  function controlBackButton(){
    const tg = window.Telegram?.WebApp; if (!tg) return;
    const path = location.pathname;
    const isRoot = ROOT_PATHS.includes(path);
    if (backHandler) tg.BackButton.offClick?.(backHandler);
    if (isRoot) { tg.BackButton.hide(); backHandler = null; return; }
    tg.BackButton.show();
    const isHonesty = path === '/honesty' || path.startsWith('/honesty/play');
    backHandler = () => {
      try { tg.HapticFeedback?.impactOccurred?.('soft'); } catch {}
      if (isHonesty) { window.location.replace('/'); return; }
      if (history.length > 1) { history.back(); } else { tg.close(); }
    };
    tg.BackButton.onClick(backHandler);
  }

  function scheduleRetries(){
    const timer = setInterval(() => {
      attempt++;
      const ok = tryFullscreen();
      if (ok && isFsEnabled(window.Telegram.WebApp)) {
        try { window.Telegram.WebApp.HapticFeedback?.impactOccurred?.('light'); } catch {}
        clearInterval(timer); maybeSetupFallbackButton();
      } else if (attempt >= MAX_RETRIES) {
        clearInterval(timer); maybeSetupFallbackButton();
      }
    }, RETRY_DELAY);
  }

  function maybeSetupFallbackButton(){
    const tg = window.Telegram?.WebApp; if (!tg) return;
    // Если не удалось автоматически — показываем MainButton для ручного входа в fullscreen
    if (tg.isVersionAtLeast?.('8.0') && tg.requestFullscreen && !isFsEnabled(tg)) {
      tg.MainButton?.setText('Открыть на весь экран');
      tg.MainButton?.show();
      tg.MainButton?.onClick(() => {
        tryFullscreen();
        if (isFsEnabled(tg)) tg.MainButton?.hide();
      });
    } else {
      tg.MainButton?.hide();
    }
  }

  function updateOrientationOverlay() {
    const isLandscape = window.innerWidth > window.innerHeight;
    let overlay = document.querySelector('.orientation-overlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.className = 'orientation-overlay';
      overlay.innerHTML = '<div class="box"><h3 class="title">Поверните устройство вертикально</h3><p class="text">Приложение работает только в портретном режиме.</p></div>';
      document.body.appendChild(overlay);
    }
    if (isLandscape) {
      overlay.classList.add('show');
    } else {
      overlay.classList.remove('show');
    }
  }

  const ROOT_PATHS = ['/']; // оставляем только абсолютный корень как место без BackButton
  let backHandler = null;
  let backDebounce = null;

  function attachEvents(){
    const tg = window.Telegram?.WebApp; if (!tg) return;
    tg.onEvent?.('fullscreenChanged', () => { updateSafeArea(); controlBackButton(); updateOrientationOverlay(); });
    tg.onEvent?.('viewportChanged', () => { updateSafeArea(); controlBackButton(); updateOrientationOverlay(); });
    tg.onEvent?.('themeChanged', () => { controlBackButton(); });
    window.addEventListener('resize', updateOrientationOverlay, { passive: true });
    window.addEventListener('orientationchange', updateOrientationOverlay, { passive: true });
    window.addEventListener('popstate', () => {
      if (backDebounce) clearTimeout(backDebounce);
      backDebounce = setTimeout(controlBackButton, 50);
    });
  }

  // Старт
  function init(){
    attachEvents();
    controlBackButton();
    updateOrientationOverlay();
    const ok = tryFullscreen();
    if (!ok || !isFsEnabled(window.Telegram?.WebApp)) scheduleRetries(); else maybeSetupFallbackButton();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

document.addEventListener('DOMContentLoaded', async () => {
  const tg = window.Telegram?.WebApp;
  try { tg?.expand?.(); } catch {}

  // Отправляем сырые данные initData на сервер для проверки подписи и TTL
  let verified = null;
  try {
    const initData = tg?.initData || '';
    if (initData) {
      const res = await fetch('/api/auth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ initData }),
      });
      if (res.ok) {
        verified = await res.json();
        // Сохраняем глобально: другие части фронта читают только это
        window.__verifiedAuth = {
          ok: true,
          telegram_id: verified.telegram_id,
          profile: verified.profile,
        };
        try { tg.HapticFeedback?.impactOccurred?.('light'); } catch {}
      } else {
        console.warn('[auth] /api/auth failed with status', res.status);
        window.__verifiedAuth = { ok: false };
      }
    } else {
      console.warn('[auth] initData is empty');
      window.__verifiedAuth = { ok: false };
    }
  } catch (e) {
    console.error('[auth] failed', e);
    window.__verifiedAuth = { ok: false };
  }
});
