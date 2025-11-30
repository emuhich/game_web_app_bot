document.addEventListener('DOMContentLoaded', () => {
  const stack = document.getElementById('cards-stack');
  if (!stack) return;

  let cards = Array.from(stack.querySelectorAll('.question-card'));

  const layoutStack = () => {
    cards = Array.from(stack.querySelectorAll('.question-card'));
    cards.forEach(c => { c.classList.remove('stack-0','stack-1','stack-2'); c.style.transition = ''; });
    if (cards[0]) cards[0].classList.add('stack-0');
    if (cards[1]) cards[1].classList.add('stack-1');
    if (cards[2]) cards[2].classList.add('stack-2');
  };
  layoutStack();

  let endDisplayed = false; // перемещено вверх для использования
  let navigating = false; // предотвратить двойной переход
  let activePointerId = null; // отслеживание pointerId для безопасного release

  // Плавный апдейт трансформа при перетаскивании
  let rafScheduled = false;
  let currentDx = 0;
  let targetDx = 0;
  function scheduleTransform(card, rotFn) {
    if (rafScheduled) return;
    rafScheduled = true;
    requestAnimationFrame(() => {
      rafScheduled = false;
      const dx = targetDx;
      const rot = rotFn(dx);
      const base = 'translate(-50%, -50%)';
      card.style.transform = `${base} translate(${dx}px, 0) rotate(${rot}deg)`;
    });
  }

  const showEndScreen = () => {
    if (endDisplayed) return; // защита от повторного вызова
    // принудительно снимаем pointer capture со всех старых карт (на случай залипания)
    stack.querySelectorAll('.question-card').forEach(c => {
      try { c.releasePointerCapture?.(activePointerId); } catch {}
    });
    endDisplayed = true;
    if (stack) stack.style.display = 'none';
    const params = location.search || '';
    const main = document.querySelector('.play-page .page-main');
    if (!main) return;
    const end = document.createElement('div');
    end.className = 'end-screen fade-in';
    end.innerHTML = `\n    <p class="end-text">Вопросы в карточке кончились. Перейдем к следующей теме?</p>\n    <button type="button" class="next-game-btn" id="next-game-btn">Новая игра</button>\n  `;
    main.appendChild(end);
    const btn = end.querySelector('#next-game-btn');
    const navigate = () => {
      if (navigating) return;
      navigating = true;
      try { window.Telegram?.WebApp?.HapticFeedback?.impactOccurred?.('light'); } catch {}
      const url = '/honesty' + params;
      setTimeout(() => { window.location.replace(url); }, 10); // replace вместо href
    };
    // Мульти-события для надежности первого срабатывания
    ['pointerdown','click','touchend'].forEach(evt => {
      btn.addEventListener(evt, navigate, { passive: true });
    });
    btn.addEventListener('keydown', e => { if ((e.key === 'Enter' || e.key === ' ') && !navigating) navigate(); });
    btn.focus();
  };

  const removeTopCard = (top, dir = 1) => {
    const base = 'translate(-50%, -50%)';
    const flyX = dir * (window.innerWidth * 0.9);
    top.classList.remove('dragging');
    top.style.transition = 'transform 0.42s cubic-bezier(.16,.84,.44,1), opacity 0.3s ease-out';
    top.style.transform = `${base} translate(${flyX}px, 0) rotate(${dir>0?12:-12}deg)`;
    top.style.opacity = '0';
    setTimeout(() => {
      try { if (activePointerId !== null) top.releasePointerCapture(activePointerId); } catch {}
      top.remove();
      layoutStack();
      // лёгкая анимация "появления" следующей карты
      const next = stack.querySelector('.question-card.stack-0');
      if (next) {
        next.style.transition = 'transform 0.35s cubic-bezier(.16,.84,.44,1), box-shadow 0.35s';
        next.style.transform = 'translate(-50%, -50%) scale(1.02)';
        setTimeout(() => { next.style.transform = 'translate(-50%, -50%)'; }, 360);
      }
      if (stack.querySelectorAll('.question-card').length === 0) {
        showEndScreen();
        return;
      }
    }, 420);
  };

  // === Упрощённая механика свайпа (без превью-теней и дерганий) ===
  const SWIPE_THRESHOLD_RATIO = 0.5; // 50% ширины
  const SWIPE_OUT_DURATION_MS = 340;
  const MAX_ROT = 10;

  function springReset(card){
    card.style.transition = 'transform .45s cubic-bezier(.34,1.56,.64,1)';
    card.style.transform = 'translate(-50%,-50%)';
    const done = () => { card.style.transition=''; card.removeEventListener('transitionend', done); };
    card.addEventListener('transitionend', done);
  }

  function swipeOut(card, dir){
    const base='translate(-50%, -50%)';
    const finalX = window.innerWidth * 1.1 * dir; // финальная точка за пределами экрана
    const rot = dir>0?MAX_ROT:-MAX_ROT;
    card.style.transition = `transform ${SWIPE_OUT_DURATION_MS}ms ease-out, opacity ${SWIPE_OUT_DURATION_MS}ms ease-out`;
    card.style.transform = `${base} translate(${finalX}px,0) rotate(${rot}deg)`;
    card.style.opacity = '0';
    const onEnd = () => {
      card.removeEventListener('transitionend', onEnd);
      card.remove();
      layoutStack();
      const remaining = stack.querySelectorAll('.question-card').length;
      if (!remaining){ showEndScreen(); return; }
      const next = stack.querySelector('.question-card.stack-0');
      if (next){
        next.style.transition='transform .3s ease-out';
        next.style.transform='translate(-50%,-50%) scale(1.02)';
        setTimeout(()=>{ next.style.transform='translate(-50%,-50%)'; next.style.transition=''; }, 300);
      }
    };
    card.addEventListener('transitionend', onEnd);
  }

  cards.forEach(card => {
    let down=false, sx=0, dx=0;
    const base='translate(-50%, -50%)';
    const width = () => card.offsetWidth||1;

    card.addEventListener('pointerdown', e => {
      down=true; sx=e.clientX; dx=0; card.style.transition='none';
    });
    card.addEventListener('pointermove', e => {
      if(!down) return; dx=e.clientX - sx; const rot=Math.max(-MAX_ROT, Math.min(MAX_ROT, dx/25));
      card.style.transform = `${base} translate(${dx}px,0) rotate(${rot}deg)`;
    });
    const finish = () => {
      if(!down) return; down=false; const w=width(); const ratio=Math.abs(dx)/w; const dir=dx>0?1:-1;
      if(ratio>=SWIPE_THRESHOLD_RATIO){ swipeOut(card, dir); } else { springReset(card); }
    };
    card.addEventListener('pointerup', finish);
    card.addEventListener('pointercancel', finish);
  });
  // === Конец упрощённой механики свайпа ===
});