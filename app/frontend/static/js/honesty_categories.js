document.addEventListener('DOMContentLoaded', () => {
  const tg = window.Telegram?.WebApp;
  if (tg) tg.expand();

  const verifiedId = window.__verifiedAuth?.telegram_id || null;

  const row = document.getElementById('categories-row');
  const chooseBtn = document.getElementById('choose-current');
  if (!row || !chooseBtn) return;

  let activeCard = null;
  const tgCore = window.Telegram?.WebApp;

  const updateActiveCard = () => {
    const cards = Array.from(row.querySelectorAll('.category-card'));
    if (!cards.length) { activeCard = null; return; }
    const viewportCenter = window.innerWidth / 2;
    let best = null, bestDist = Infinity;
    cards.forEach(card => {
      const rect = card.getBoundingClientRect();
      const cardCenter = rect.left + rect.width / 2;
      const dist = Math.abs(cardCenter - viewportCenter);
      if (dist < bestDist) { bestDist = dist; best = card; }
    });
    const prev = activeCard;
    cards.forEach(c => c.classList.toggle('is-active', c === best));
    activeCard = best;
    if (prev && best && prev !== best) { try { tgCore?.HapticFeedback?.selectionChanged?.(); } catch {} }
  };

  updateActiveCard();

  let rafId = null;
  const onScroll = () => {
    if (rafId) cancelAnimationFrame(rafId);
    rafId = requestAnimationFrame(updateActiveCard);
  };
  row.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll, { passive: true });

  let isDown = false, startX = 0, scrollL = 0, lastStep = 0;
  row.addEventListener('pointerdown', e => {
    isDown = true; startX = e.pageX; scrollL = row.scrollLeft; lastStep = 0;
    row.setPointerCapture(e.pointerId);
    row.style.cursor = 'grabbing';
  });
  row.addEventListener('pointermove', e => {
    if (!isDown) return;
    e.preventDefault();
    const dx = e.pageX - startX;
    row.scrollLeft = scrollL - dx;
    onScroll();
    const cardW = activeCard?.getBoundingClientRect()?.width || 1;
    const step = Math.floor(Math.abs(dx) / (cardW * 0.25));
    if (step > lastStep) { try { tgCore?.HapticFeedback?.selectionChanged?.(); } catch {} lastStep = step; }
  });
  const end = () => { isDown = false; row.style.cursor = 'grab'; };
  row.addEventListener('pointerup', end);
  row.addEventListener('pointerleave', end);

  function showPremiumPopup() {
    const overlay = document.createElement('div');
    overlay.className = 'premium-popup-overlay';
    overlay.innerHTML = `
      <div class="premium-popup" role="dialog" aria-modal="true">
        <button type="button" class="premium-popup-close" aria-label="Закрыть">×</button>
        <h3 class="premium-popup-title">Премиум категория</h3>
        <p class="premium-popup-text">Эта категория доступна только с премиум-подпиской. Оформи премиум, чтобы открыть все премиум-вопросы и категории.</p>
        <div class="premium-popup-actions">
          <button type="button" class="premium-popup-buy">Купить премиум</button>
        </div>
      </div>`;
    document.body.appendChild(overlay);

    const closeBtn = overlay.querySelector('.premium-popup-close');
    const buyBtn = overlay.querySelector('.premium-popup-buy');

    const close = () => {
      overlay.classList.add('fade-out');
      setTimeout(() => overlay.remove(), 220);
    };

    closeBtn?.addEventListener('click', close);

    buyBtn?.addEventListener('click', () => {
      try { tgCore?.HapticFeedback?.impactOccurred?.('medium'); } catch {}
      const url = new URL('/premium', window.location.origin);
      if (verifiedId) url.searchParams.set('telegram_id', verifiedId);
      window.location.href = url.toString();
    });
  }

  chooseBtn.addEventListener('click', async () => {
    try { tgCore?.HapticFeedback?.impactOccurred?.('light'); } catch {}
    if (!activeCard) return;
    const id = activeCard.dataset.id;
    const base = `/honesty/play/${id}`;
    const params = [];
    if (verifiedId) params.push(`telegram_id=${verifiedId}`);
    const url = base + (params.length ? `?${params.join('&')}` : '');

    // сначала пробуем запросить доступ к вопросам через API
    try {
      const res = await fetch(url, { method: 'GET' });
      if (res.status === 402) {
        // требуется премиум — показываем попап и не переходим в вопросы
        showPremiumPopup();
        return;
      }
      if (!res.ok) {
        // другие ошибки — можно показать alert или просто не переходить
        return;
      }
      // доступ разрешён — переходим обычным образом
      window.location.href = url;
    } catch (e) {
      console.error('Ошибка при запросе категории:', e);
    }
  });
});