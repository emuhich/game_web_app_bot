import { haptics } from '/static/js/haptics.js';
import { getVerifiedId } from '/static/js/auth.js';
import { showDevOverlay } from '/static/js/popups.js';

document.addEventListener('DOMContentLoaded', () => {
  const stack = document.getElementById('cards-stack');
  if (!stack) return;

  const verifiedId = getVerifiedId();

  let navigating = false;
  let endDisplayed = false;

  const SWIPE_THRESHOLD_RATIO = 0.5;
  const SWIPE_OUT_DURATION_MS = 340;
  const MAX_ROT = 10;

  // Показываем подсказку о свайпе только при первом заходе в игру
  try {
    const HINT_KEY = 'honesty_swipe_hint_shown_v1';
    const already = window.localStorage.getItem(HINT_KEY);
    if (!already) {
      // Небольшая задержка, чтобы не мигало вместе с анимацией первой карточки
      setTimeout(() => {
        showDevOverlay();
        window.localStorage.setItem(HINT_KEY, '1');
      }, 300);
    }
  } catch (e) {
    console.warn('Не удалось сохранить флаг показа подсказки свайпа', e);
  }

  const relayout = () => {
    const cards = Array.from(stack.querySelectorAll('.question-card'));
    cards.forEach(c => {
      c.classList.remove('stack-0','stack-1','stack-hidden','dragging');
      c.style.transition = '';
      c.style.opacity = '';
      c.style.pointerEvents = 'none';
      c.style.transform = 'translate(-50%, -58%)';
      c.style.willChange = 'transform';
    });
    if (cards[0]) { cards[0].classList.add('stack-0'); cards[0].style.pointerEvents = 'auto'; cards[0].style.opacity = '1'; }
    if (cards[1]) { cards[1].classList.add('stack-1'); cards[1].style.opacity = '1'; }
    for (let i = 2; i < cards.length; i++) { cards[i].classList.add('stack-hidden'); cards[i].style.opacity = '0'; }
  };

  const showEndScreen = () => {
    if (endDisplayed) return;
    endDisplayed = true;
    const main = document.querySelector('.play-page .page-main');
    stack.style.display = 'none';
    const end = document.createElement('div');
    end.className = 'end-screen fade-in';
    end.innerHTML = `
      <p class="end-text">Вопросы в карточке кончились. Перейдём к следующей теме?</p>
      <button type="button" class="next-game-btn" id="next-game-btn">Новая игра</button>
    `;
    main.appendChild(end);
    const btn = end.querySelector('#next-game-btn');
    haptics.notify('success');
    const navigate = () => {
      if (navigating) return;
      navigating = true;
      haptics.impact('light');
      let url = '/honesty';
      if (verifiedId) { const u = new URL(url, window.location.origin); u.searchParams.set('telegram_id', String(verifiedId)); url = u.toString(); }
      setTimeout(() => { window.location.replace(url); }, 10);
    };
    ['pointerdown','click','touchend'].forEach(evt => btn.addEventListener(evt, navigate, { passive: true }));
    btn.addEventListener('keydown', e => { if ((e.key === 'Enter' || e.key === ' ') && !navigating) navigate(); });
    btn.focus();
  };

  const springReset = (card) => {
    card.style.transition = 'transform .45s cubic-bezier(.34,1.56,.64,1)';
    card.style.transform = 'translate(-50%, -58%)';
    const done = () => { card.style.transition=''; card.classList.remove('dragging'); card.removeEventListener('transitionend', done); };
    card.addEventListener('transitionend', done);
  };

  const swipeOut = (card, dir) => {
    haptics.impact('medium');
    const base='translate(-50%, -58%)';
    const finalX = window.innerWidth * 1.1 * dir;
    const rot = dir>0?MAX_ROT:-MAX_ROT;
    card.style.transition = `transform ${SWIPE_OUT_DURATION_MS}ms ease-out, opacity ${SWIPE_OUT_DURATION_MS}ms ease-out`;
    card.style.transform = `${base} translate(${finalX}px,0) rotate(${rot}deg)`;
    card.style.opacity = '0';
    const onEnd = () => {
      card.removeEventListener('transitionend', onEnd);
      card.remove();
      relayout();
      const nextTop = stack.querySelector('.question-card.stack-0');
      if (!nextTop) { showEndScreen(); return; }
      bindTopCard();
      nextTop.style.transition='transform .3s ease-out';
      nextTop.style.transform='translate(-50%,-58%) scale(1.02)';
      setTimeout(()=>{ nextTop.style.transform='translate(-50%,-58%)'; nextTop.style.transition=''; }, 300);
    };
    card.addEventListener('transitionend', onEnd);
  };

  const bindTopCard = () => {
    // Снимаем обработчики у всех карт
    Array.from(stack.querySelectorAll('.question-card')).forEach(c => {
      c.onpointerdown = null; c.onpointermove = null; c.onpointerup = null; c.onpointercancel = null;
    });
    const top = stack.querySelector('.question-card.stack-0');
    if (!top) return;
    let down=false, sx=0, dx=0, lastStep=0;
    const base='translate(-50%, -58%)';
    top.onpointerdown = (e) => {
      // Игнорируем любые события не на верхней карте
      if (e.currentTarget !== top) return;
      down = true; sx = e.clientX; dx = 0; lastStep = 0; top.style.transition='none'; top.classList.add('dragging');
      top.setPointerCapture?.(e.pointerId);
    };
    top.onpointermove = (e) => {
      if (!down) return;
      if (e.currentTarget !== top) return;
      dx = e.clientX - sx; const rot = Math.max(-MAX_ROT, Math.min(MAX_ROT, dx/25));
      top.style.transform = `${base} translate(${dx}px,0) rotate(${rot}deg)`;
      const w = top.offsetWidth || 1; const step = Math.floor((Math.abs(dx)/w) / 0.2);
      if (step > lastStep) { haptics.selection(); lastStep = step; }
    };
    const finish = (e) => {
      if (!down) return;
      if (e && e.currentTarget !== top) return;
      down=false; top.classList.remove('dragging');
      const w = top.offsetWidth || 1; const ratio = Math.abs(dx)/w; const dir = dx>0?1:-1;
      if (ratio >= SWIPE_THRESHOLD_RATIO) { swipeOut(top, dir); } else { springReset(top); }
    };
    top.onpointerup = finish;
    top.onpointercancel = finish;
  };

  const init = () => { relayout(); bindTopCard(); };
  init();
});