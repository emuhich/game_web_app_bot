import { haptics } from '/static/js/haptics.js';
import { getVerifiedId } from '/static/js/auth.js';
import { showDevOverlay } from '/static/js/popups.js';

document.addEventListener('DOMContentLoaded', () => {
  console.log('[index.js] DOMContentLoaded');
  if (window.Telegram && window.Telegram.WebApp) {
    Telegram.WebApp.expand(); // Full-screen mode for Telegram WebApp
  }

  const tgCore = window.Telegram?.WebApp;
  const verifiedId = getVerifiedId();

  const carousel = document.getElementById('games-row');
  const playBtn = document.getElementById('play-current');
  if (!carousel || !playBtn) return;

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
    if (prev && best && prev !== best) { haptics.selection(); }
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
    haptics.impact('soft');
    carousel.setPointerCapture(e.pointerId);
  });
  carousel.addEventListener('pointermove', e => {
    if (!isDown) return; const dx = e.pageX - startX; carousel.scrollLeft = scrollStart - dx; onScroll();
    const cardW = activeCard?.getBoundingClientRect()?.width || 1;
    const step = Math.floor(Math.abs(dx) / (cardW * 0.25));
    if (step > lastStep) { haptics.selection(); lastStep = step; }
  });
  const endDrag = () => { isDown = false; };
  carousel.addEventListener('pointerup', endDrag);
  carousel.addEventListener('pointerleave', endDrag);

  // Кнопка «Играть» — переход в выбранную игру
  playBtn.addEventListener('click', () => {
    if (!activeCard) return;
    const isDev = activeCard.dataset.inDevelopment === '1';
    haptics.impact(isDev ? 'light' : 'medium');
    if (isDev) { showDevOverlay(); return; }
    const code = activeCard.dataset.code;
    let url = '/honesty';
    if (code === 'honesty') url = '/honesty';
    if (verifiedId) url += `?telegram_id=${verifiedId}`;
    window.location.href = url;
  });

  // Премиум и Профиль — если JS не сработает, сработает обычный href
  document.querySelectorAll('.buy-premium').forEach(link => {
    link.addEventListener('click', e => {
      if (!verifiedId) return; // без verifiedId пусть работает обычный href
      e.preventDefault();
      const url = new URL(link.href, window.location.origin);
      url.searchParams.set('telegram_id', verifiedId);
      window.location.href = url.toString();
    });
  });

  document.querySelectorAll('.profile-link').forEach(link => {
    link.addEventListener('click', e => {
      if (!verifiedId) return; // без verifiedId пусть работает обычный href
      e.preventDefault();
      const url = new URL(link.href, window.location.origin);
      url.searchParams.set('telegram_id', verifiedId);
      window.location.href = url.toString();
    });
  });
});