// Универсальные попапы: devOverlay и premiumPopup
import {haptics} from './haptics.js';

export function showDevOverlay() {
    // Обучающий попап: как играть в карточки (свайпы)
    try {
        haptics.impact('medium');
    } catch {
    }

    const overlay = document.createElement('div');
    overlay.className = 'swipe-hint-overlay';
    overlay.innerHTML = `
    <div class="swipe-hint" role="dialog" aria-modal="true">
      <h3 class="hint-title">Как играть</h3>
      <p class="hint-text">Смахивай карточки влево или вправо, чтобы переходить к следующему вопросу.</p>
      <div class="hint-gesture"><span class="hand">👆</span><span class="arrow">⇄</span></div>
      <button class="hint-close" type="button">Понятно</button>
    </div>`;

    document.body.appendChild(overlay);

    const closeBtn = overlay.querySelector('.hint-close');
    const close = () => {
        try {
            haptics.impact('light');
        } catch {
        }
        overlay.classList.add('fade-out');
        setTimeout(() => overlay.remove(), 220);
    };

    closeBtn?.addEventListener('click', close);

    // закрытие по клику вне окна
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) close();
    });
}

export function showInDevelopmentPopup() {
    try {
        haptics.impact('light');
    } catch {
    }

    const overlay = document.createElement('div');
    overlay.className = 'swipe-hint-overlay';
    overlay.innerHTML = `
    <div class="swipe-hint" role="dialog" aria-modal="true">
      <h3 class="hint-title">В разработке</h3>
      <p class="hint-text">Эта игра пока недоступна. Следите за обновлениями!</p>
      <button class="hint-close" type="button">Ок</button>
    </div>`;
    document.body.appendChild(overlay);

    const closeBtn = overlay.querySelector('.hint-close');
    const close = () => {
        try {
            haptics.impact('light');
        } catch {
        }
        overlay.classList.add('fade-out');
        setTimeout(() => overlay.remove(), 220);
    };

    closeBtn?.addEventListener('click', close);
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) close();
    });
}

export function showPremiumPopup(onBuy) {
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
        haptics.impact('medium');
        onBuy?.();
    });
}

export function showVpnBlockerPopup(onReload) {
    // Глобальный защитный флаг, чтобы попап показывался только один раз во всём приложении
    if (typeof window !== 'undefined') {
        if (window.__vpnPopupShown) return;
        window.__vpnPopupShown = true;
    }

    try {
        haptics.impact('light');
    } catch {}

    const overlay = document.createElement('div');
    overlay.className = 'premium-popup-overlay vpn-popup-overlay';
    overlay.innerHTML = `
    <div class="premium-popup vpn-popup" role="dialog" aria-modal="true">
      <button type="button" class="premium-popup-close" aria-label="Закрыть">×</button>
      <h3 class="premium-popup-title">Проблема с оплатой</h3>
      <p class="premium-popup-text">Платёжный виджет не загрузился. Отключи VPN или прокси и обнови страницу.</p>
      <div class="premium-popup-actions">
        <button type="button" class="premium-popup-buy vpn-popup-refresh">Обновить страницу</button>
      </div>
    </div>`;
    document.body.appendChild(overlay);

    const closeBtn = overlay.querySelector('.premium-popup-close');
    const refreshBtn = overlay.querySelector('.vpn-popup-refresh');
    const close = () => {
        overlay.classList.add('fade-out');
        setTimeout(() => overlay.remove(), 220);
    };

    closeBtn?.addEventListener('click', () => {
        try { haptics.impact('light'); } catch {}
        close();
    });
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) close();
    });

    refreshBtn?.addEventListener('click', () => {
        try { haptics.impact('medium'); } catch {}
        close();
        if (typeof onReload === 'function') {
            onReload();
        } else {
            window.location.reload();
        }
    });
}

// Делаем функцию доступной глобально, чтобы её можно было вызывать из inline-скриптов шаблонов
if (typeof window !== 'undefined') {
    window.showVpnBlockerPopup = showVpnBlockerPopup;
}
