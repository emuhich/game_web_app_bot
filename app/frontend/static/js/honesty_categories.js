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

  // Функция вычисления активной карточки: ближайшая к центру вьюпорта
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
    // Обновим визуально (можно добавить класс .is-active)
    cards.forEach(c => c.classList.toggle('is-active', c === best));
    activeCard = best;
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

  // Drag-scroll для мыши/тача
  let isDown = false, startX = 0, scrollL = 0;
  row.addEventListener('pointerdown', e => {
    isDown = true; startX = e.pageX; scrollL = row.scrollLeft;
    row.setPointerCapture(e.pointerId);
    row.style.cursor = 'grabbing';
  });
  row.addEventListener('pointermove', e => {
    if (!isDown) return;
    e.preventDefault();
    const dx = e.pageX - startX;
    row.scrollLeft = scrollL - dx;
    onScroll();
  });
  const end = () => { isDown = false; row.style.cursor = 'grab'; };
  row.addEventListener('pointerup', end);
  row.addEventListener('pointerleave', end);

  // Нажатие большой кнопки "Выбрать"
  chooseBtn.addEventListener('click', () => {
    if (!activeCard) return;
    const id = activeCard.dataset.id;
    const premium = activeCard.dataset.premium === 'true';
    const adult = activeCard.dataset.adult === 'true';

    // TODO: проверки premium/adult → редирект на гейтинг, если нужно

    const base = `/honesty/play/${id}`;
    const params = [];
    if (tgUser) params.push(`telegram_id=${tgUser.id}`);
    const url = base + (params.length ? `?${params.join('&')}` : '');
    window.location.href = url;
  });
});