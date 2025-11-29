document.addEventListener('DOMContentLoaded', () => {
  if (window.Telegram && window.Telegram.WebApp) {
    Telegram.WebApp.expand(); // Full-screen mode for Telegram WebApp
  }

  const stack = document.getElementById('cards-stack');
  const cards = [...stack.querySelectorAll('.question-card')];
  // Shuffle order for randomness
  for (let i = cards.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    stack.appendChild(cards[j]);
    cards.splice(j, 1);
  }
  let activeCards = [...stack.querySelectorAll('.question-card')];

  // Add offset for card stack (fan effect) and force full size
  activeCards.forEach((card, idx) => {
    card.style.transform = `translate(${idx * 8}px, ${idx * 8}px) rotate(${idx * 2}deg) scale(${1 - idx * 0.02})`;
    card.style.zIndex = activeCards.length - idx;
    card.style.width = '100%';
    card.style.height = '100%';
  });

  activeCards.forEach(initCard);

  function initCard(card) {
    let startX, startY, dragging = false;
    card.addEventListener('pointerdown', e => {
      dragging = true;
      startX = e.clientX;
      startY = e.clientY;
      card.setPointerCapture(e.pointerId);
    });
    card.addEventListener('pointermove', e => {
      if (!dragging) return;
      const dx = e.clientX - startX;
      const dy = e.clientY - startY;
      card.style.transform = `translate(${dx}px, ${dy}px) rotate(${dx * 0.05}deg)`;
      card.style.transition = 'none';
    });
    const end = (e) => {
      if (!dragging) return;
      dragging = false;
      card.releasePointerCapture(e.pointerId);
      const dx = e.clientX - startX;
      const dy = e.clientY - startY;
      const threshold = 120;
      if (Math.abs(dx) > threshold || Math.abs(dy) > threshold) {
        card.style.transition = 'transform 0.35s ease, opacity 0.35s ease';
        card.style.transform = `translate(${dx * 2}px, ${dy * 2}px) rotate(${dx * 0.1}deg)`;
        card.style.opacity = '0';
        setTimeout(() => {
          card.remove();
          activeCards = [...stack.querySelectorAll('.question-card')];
          if (activeCards.length === 0) {
            showFinished();
          } else {
            // Re-apply fan effect after removal
            activeCards.forEach((c, i) => {
              c.style.transform = `translate(${i * 8}px, ${i * 8}px) rotate(${i * 2}deg) scale(${1 - i * 0.02})`;
              c.style.zIndex = activeCards.length - i;
            });
          }
        }, 380);
      } else {
        card.style.transition = 'transform 0.3s ease';
        card.style.transform = 'translate(0,0)';
      }
    };
    card.addEventListener('pointerup', end);
    card.addEventListener('pointerleave', end);
  }

  function showFinished() {
    const btn = document.getElementById('choose-other');
    btn.textContent = 'Выбрать новую категорию';
    btn.classList.add('pulse');
  }

  document.getElementById('choose-other').addEventListener('click', () => {
    window.location.href = '/honesty' + location.search;
  });
});