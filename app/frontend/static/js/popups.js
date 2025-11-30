// Универсальные попапы: devOverlay и premiumPopup
import { haptics } from './haptics.js';

export function showDevOverlay() {
  haptics.impact('medium');
  const overlay = document.createElement('div');
  overlay.className = 'swipe-hint-overlay';
  overlay.innerHTML = `
    <div class="swipe-hint" role="dialog" aria-modal="true">
      <h3 class="hint-title">Скоро</h3>
      <p class="hint-text">Эта игра пока в разработке. Совсем скоро она появится в приложении!</p>
      <div class="hint-gesture"><span class="hand">🚧</span></div>
      <button class="hint-close" type="button">Понятно</button>
    </div>`;
  document.body.appendChild(overlay);
  const closeBtn = overlay.querySelector('.hint-close');
  const close = () => { haptics.impact('light'); overlay.classList.add('fade-out'); setTimeout(() => overlay.remove(), 220); };
  closeBtn?.addEventListener('click', close);
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
  const close = () => { overlay.classList.add('fade-out'); setTimeout(() => overlay.remove(), 220); };
  closeBtn?.addEventListener('click', close);
  buyBtn?.addEventListener('click', () => { haptics.impact('medium'); onBuy?.(); });
}

