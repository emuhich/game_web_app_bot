document.addEventListener('DOMContentLoaded', () => {
  const tg = window.Telegram?.WebApp;
  if (tg) tg.expand();

  let tgUser = null;
  try { tgUser = tg?.initDataUnsafe?.user || null; } catch (e) { tgUser = null; }

  const row = document.getElementById('categories-row');
  const chooseBtn = document.getElementById('choose-current');
  if (!row || !chooseBtn) return;

  // Храним текущую активную карточку
  let activeCard = null;

  // Хаптик: отклик при смене активной карточки
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

  // Первичный расчет
  updateActiveCard();

  // Обновляем при скролле/ресайзе
  let rafId = null;
  const onScroll = () => {
    if (rafId) cancelAnimationFrame(rafId);
    rafId = requestAnimationFrame(updateActiveCard);
  };
  row.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll, { passive: true });

  // Drag-scroll для мыши/тача с хаптиком по шагам
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
    // Хаптик: каждые ~25% ширины карточки
    const cardW = activeCard?.getBoundingClientRect()?.width || 1;
    const step = Math.floor(Math.abs(dx) / (cardW * 0.25));
    if (step > lastStep) { try { tgCore?.HapticFeedback?.selectionChanged?.(); } catch {} lastStep = step; }
  });
  const end = () => { isDown = false; row.style.cursor = 'grab'; };
  row.addEventListener('pointerup', end);
  row.addEventListener('pointerleave', end);

  // Нажатие большой кнопки "Выбрать"
  chooseBtn.addEventListener('click', () => {
    const tg = window.Telegram?.WebApp; try { tg?.HapticFeedback?.impactOccurred?.('light'); } catch {}
    if (!activeCard) return;
    const id = activeCard.dataset.id;
    const base = `/honesty/play/${id}`;
    const params = [];
    if (tgUser) params.push(`telegram_id=${tgUser.id}`);
    window.location.href = base + (params.length ? `?${params.join('&')}` : '');
  });
});