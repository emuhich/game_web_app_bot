import { haptics } from '/static/js/haptics.js';
import { getVerifiedId } from '/static/js/auth.js';

document.addEventListener('DOMContentLoaded', () => {
  const stack = document.getElementById('cards-stack');
  if (!stack) return;

  const verifiedId = getVerifiedId();

  let cards = Array.from(stack.querySelectorAll('.question-card'));

  const layoutStack = () => {
    cards = Array.from(stack.querySelectorAll('.question-card'));
    cards.forEach(c => { c.classList.remove('stack-0','stack-1','stack-2'); c.style.transition = ''; });
    if (cards[0]) cards[0].classList.add('stack-0');
    if (cards[1]) cards[1].classList.add('stack-1');
    if (cards[2]) cards[2].classList.add('stack-2');
  };
  layoutStack();

  let endDisplayed = false;
  let navigating = false;
  let activePointerId = null;

  const showEndScreen = () => {
    if (endDisplayed) return;
    stack.querySelectorAll('.question-card').forEach(c => {
      try { if (activePointerId != null) c.releasePointerCapture?.(activePointerId); } catch {}
    });
    endDisplayed = true;
    if (stack) stack.style.display = 'none';
    const params = location.search || '';
    const main = document.querySelector('.play-page .page-main');
    if (!main) return;
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
      if (verifiedId) {
        const u = new URL(url, window.location.origin);
        u.searchParams.set('telegram_id', String(verifiedId));
        url = u.toString();
      }
      setTimeout(() => { window.location.replace(url); }, 10);
    };
    ['pointerdown','click','touchend'].forEach(evt => {
      btn.addEventListener(evt, navigate, { passive: true });
    });
    btn.addEventListener('keydown', e => { if ((e.key === 'Enter' || e.key === ' ') && !navigating) navigate(); });
    btn.focus();
  };

  const SWIPE_THRESHOLD_RATIO = 0.5;
  const SWIPE_OUT_DURATION_MS = 340;
  const MAX_ROT = 10;

  function springReset(card){
    card.style.transition = 'transform .45s cubic-bezier(.34,1.56,.64,1)';
    card.style.transform = 'translate(-50%,-50%)';
    const done = () => { card.style.transition=''; card.removeEventListener('transitionend', done); };
    card.addEventListener('transitionend', done);
  }

  function swipeOut(card, dir){
    haptics.impact('medium');
    const base='translate(-50%, -50%)';
    const finalX = window.innerWidth * 1.1 * dir;
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
    let lastStep = 0;

    card.addEventListener('pointerdown', e => {
      down=true; sx=e.clientX; dx=0; card.style.transition='none'; lastStep = 0; activePointerId = e.pointerId;
    });
    card.addEventListener('pointermove', e => {
      if(!down) return; dx=e.clientX - sx; const rot=Math.max(-MAX_ROT, Math.min(MAX_ROT, dx/25));
      card.style.transform = `${base} translate(${dx}px,0) rotate(${rot}deg)`;
      const w = width();
      const step = Math.floor((Math.abs(dx)/w) / 0.2);
      if (step > lastStep) { haptics.selection(); lastStep = step; }
    });
    const finish = () => {
      if(!down) return; down=false; const w=width(); const ratio=Math.abs(dx)/w; const dir=dx>0?1:-1;
      if(ratio>=SWIPE_THRESHOLD_RATIO){ swipeOut(card, dir); } else { springReset(card); }
    };
    card.addEventListener('pointerup', finish);
    card.addEventListener('pointercancel', finish);
  });

  const PLAY_HINT_KEY = 'swipe_hint_play_shown_v1';
  function showSwipeHintOverlay(){
    const host = document.querySelector('.play-page') || document.body;
    const overlay = document.createElement('div');
    overlay.className = 'swipe-hint-overlay';
    overlay.innerHTML = `
      <div class="swipe-hint" role="dialog" aria-modal="true">
        <h3 class="hint-title">Как получить следующий вопрос</h3>
        <p class="hint-text">Перетащите карточку влево или вправо и отпустите — откроется следующий вопрос.</p>
        <div class="hint-gesture"><span class="hand"> <- 👆-></span></div>
        <button class="hint-close" type="button">Понятно</button>
      </div>`;
    host.appendChild(overlay);
    const closeBtn = overlay.querySelector('.hint-close');
    const close = () => {
      overlay.classList.add('fade-out');
      setTimeout(() => overlay.remove(), 220);
      try { sessionStorage.setItem(PLAY_HINT_KEY, '1'); } catch {}
    };
    closeBtn?.addEventListener('click', close);
  }
  try { if (!sessionStorage.getItem(PLAY_HINT_KEY)) setTimeout(() => { if (!sessionStorage.getItem(PLAY_HINT_KEY)) showSwipeHintOverlay(); }, 80); } catch {}
});