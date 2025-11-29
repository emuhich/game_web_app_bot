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

  const carousel = document.getElementById('games-carousel');
  if (carousel) {
    // Горизонтальный скролл колесом мыши
    carousel.addEventListener('wheel', e => {
      if (Math.abs(e.deltaX) < Math.abs(e.deltaY)) {
        carousel.scrollBy({ left: e.deltaY, behavior: 'smooth' });
        e.preventDefault();
      }
    }, { passive: false });

    // drag-scroll
    let isDown = false, startX, scrollStart;
    carousel.addEventListener('pointerdown', e => {
      isDown = true;
      startX = e.pageX;
      scrollStart = carousel.scrollLeft;
      carousel.setPointerCapture(e.pointerId);
    });
    carousel.addEventListener('pointermove', e => {
      if (!isDown) return;
      const dx = e.pageX - startX;
      carousel.scrollLeft = scrollStart - dx;
    });
    const endDrag = () => {
      isDown = false;
    };
    carousel.addEventListener('pointerup', endDrag);
    carousel.addEventListener('pointerleave', endDrag);
  }

  // Кнопка "Играть" — вообще не меняем поведение submit, только логируем факт клика
  const playButtons = document.querySelectorAll('.enter-btn');
  console.log('[index.js] найдено кнопок Играть:', playButtons.length);
  playButtons.forEach(btn => {
    console.log('[index.js] кнопка Играть:', btn);
    btn.addEventListener('click', () => {
      console.log('[index.js] click по кнопке Играть');
      // Ничего не трогаем: форма сама отправится на /honesty
      // Если нужно будет добавить telegram_id, сделаем это на сервере из initData
    });
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