document.addEventListener('DOMContentLoaded', () => {
  console.log('[index.js] DOMContentLoaded');
  if (window.Telegram && window.Telegram.WebApp) {
    Telegram.WebApp.expand(); // Full-screen mode for Telegram WebApp
  }

  // Безопасно инициализируем Telegram WebApp
  let tgUser = null;
  try {
    tgUser = window.Telegram?.WebApp?.initDataUnsafe?.user || null;
  } catch (e) {
    console.warn('Telegram WebApp user init failed', e);
    tgUser = null;
  }

  const tgCore = window.Telegram?.WebApp;

  const carousel = document.getElementById('games-row');
  const playBtn = document.getElementById('play-current');
  if (!carousel || !playBtn) return;

  // Вспомогательный: показать оверлей-попап (в разработке)
  function showDevOverlay() {
    try { tgCore?.HapticFeedback?.impactOccurred?.('medium'); } catch {}
    const overlay = document.createElement('div');
    overlay.className = 'swipe-hint-overlay'; // используем существующий стиль оверлея
    overlay.innerHTML = `
      <div class="swipe-hint" role="dialog" aria-modal="true">
        <h3 class="hint-title">Скоро</h3>
        <p class="hint-text">Эта игра пока в разработке. Совсем скоро она появится в приложении!</p>
        <div class="hint-gesture"><span class="hand">🚧</span></div>
        <button class="hint-close" type="button">Понятно</button>
      </div>`;
    document.body.appendChild(overlay);
    const closeBtn = overlay.querySelector('.hint-close');
    const close = () => {
      try { tgCore?.HapticFeedback?.impactOccurred?.('light'); } catch {}
      overlay.classList.add('fade-out'); setTimeout(() => overlay.remove(), 220);
    };
    closeBtn?.addEventListener('click', close);
  }

  // Сразу ставим карусель в начало и центрируем первую карточку относительно экрана
  const firstCard = carousel.querySelector('.game-card');
  if (firstCard) {
    // Вычисляем точный scrollLeft, чтобы центр первой карточки совпал с центром контейнера карусели
    const target = firstCard.offsetLeft + (firstCard.offsetWidth / 2) - (carousel.clientWidth / 2);
    carousel.scrollLeft = Math.max(0, target);
  } else {
    carousel.scrollLeft = 0;
  }

  function markDevGames() {
    const cards = Array.from(carousel.querySelectorAll('.game-card'));
    cards.forEach(card => { if (card.dataset.inDevelopment === '1') card.classList.add('in-development'); });
  }

  let activeCard = null;
  const updateActive = () => {
    const cards = Array.from(carousel.querySelectorAll('.game-card'));
    if (!cards.length) { activeCard = null; return; }
    const center = window.innerWidth / 2;
    let best = null, bestDist = Infinity;
    cards.forEach(card => {
      const rect = card.getBoundingClientRect();
      const c = rect.left + rect.width / 2;
      const d = Math.abs(c - center);
      if (d < bestDist) { bestDist = d; best = card; }
    });
    const prev = activeCard;
    cards.forEach(c => c.classList.toggle('is-active', c === best));
    activeCard = best;
    if (prev && best && prev !== prev) { /* защитная */ }
    if (prev && best && prev !== best) { try { tgCore?.HapticFeedback?.selectionChanged?.(); } catch {} }
  };

  markDevGames();
  updateActive();
  if (!activeCard && firstCard) {
    firstCard.classList.add('is-active');
    activeCard = firstCard;
  }

  let rafId = null;
  const onScroll = () => { if (rafId) cancelAnimationFrame(rafId); rafId = requestAnimationFrame(updateActive); };
  carousel.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll, { passive: true });

  // drag-scroll
  let isDown = false, startX = 0, scrollStart = 0, lastStep = 0;
  carousel.addEventListener('pointerdown', e => {
    isDown = true; startX = e.pageX; scrollStart = carousel.scrollLeft; lastStep = 0;
    try { tgCore?.HapticFeedback?.impactOccurred?.('soft'); } catch {}
    carousel.setPointerCapture(e.pointerId);
  });
  carousel.addEventListener('pointermove', e => {
    if (!isDown) return; const dx = e.pageX - startX; carousel.scrollLeft = scrollStart - dx; onScroll();
    const cardW = activeCard?.getBoundingClientRect()?.width || 1;
    const step = Math.floor(Math.abs(dx) / (cardW * 0.25));
    if (step > lastStep) { try { tgCore?.HapticFeedback?.selectionChanged?.(); } catch {} lastStep = step; }
  });
  const endDrag = () => { isDown = false; };
  carousel.addEventListener('pointerup', endDrag);
  carousel.addEventListener('pointerleave', endDrag);

  // Кнопка «Играть» — переход в выбранную игру
  playBtn.addEventListener('click', () => {
    if (!activeCard) return;
    const isDev = activeCard.dataset.inDevelopment === '1';
    try { tgCore?.HapticFeedback?.impactOccurred?.(isDev ? 'light' : 'medium'); } catch {}
    if (isDev) { showDevOverlay(); return; }
    const code = activeCard.dataset.code;
    let url = '/honesty';
    if (code === 'honesty') url = '/honesty';
    if (tgUser) url += `?telegram_id=${tgUser.id}`;
    window.location.href = url;
  });

  // Премиум и Профиль — если JS не сработает, сработает обычный href
  document.querySelectorAll('.buy-premium').forEach(link => {
    link.addEventListener('click', e => {
      if (!tgUser) return; // пусть работает обычный href
      e.preventDefault();
      const url = new URL(link.href, window.location.origin);
      url.searchParams.set('telegram_id', tgUser.id);
      console.log('[index.js] click Премиум →', url.toString());
      window.location.href = url.toString();
    });
  });

  document.querySelectorAll('.profile-link').forEach(link => {
    link.addEventListener('click', e => {
      if (!tgUser) return;
      e.preventDefault();
      const url = new URL(link.href, window.location.origin);
      url.searchParams.set('telegram_id', tgUser.id);
      console.log('[index.js] click Профиль →', url.toString());
      window.location.href = url.toString();
    });
  });
});