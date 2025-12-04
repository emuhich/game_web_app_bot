import { haptics } from '/static/js/haptics.js';
import { ensureAuth, getVerifiedId } from '/static/js/auth.js';
import { showVpnBlockerPopup } from '/static/js/popups.js';

const YOO_WIDGET_TIMEOUT_MS = 5000; // увеличили таймаут до 10с
let vpnPopupShown = false;
let yooWidgetTimeoutId = null;
let yooWidgetPollId = null;
let yooScriptLoaded = false;

function showVpnNoticeOnce(onReload) {
  if (vpnPopupShown) return;
  vpnPopupShown = true;
  showVpnBlockerPopup(onReload);
}

function clearYooWidgetWatchers() {
  if (yooWidgetTimeoutId) {
    clearTimeout(yooWidgetTimeoutId);
    yooWidgetTimeoutId = null;
  }
  if (yooWidgetPollId) {
    clearInterval(yooWidgetPollId);
    yooWidgetPollId = null;
  }
}

function waitForWidget(timeoutMs = YOO_WIDGET_TIMEOUT_MS) {
  return new Promise((resolve, reject) => {
    // Уже доступен
    if (typeof window.YooMoneyCheckoutWidget === 'function') {
      return resolve(true);
    }

    const script = document.querySelector('script[src*="checkout-widget"]');
    if (script) {
      // Фиксируем факт загрузки скрипта браузером
      script.addEventListener('load', () => { yooScriptLoaded = true; }, { once: true });
      script.addEventListener('error', () => {
        clearYooWidgetWatchers();
        reject(new Error('Не удалось загрузить скрипт YooKassa'));
      }, { once: true });
    }

    let elapsed = 0;
    const step = 200;
    yooWidgetPollId = setInterval(() => {
      elapsed += step;
      if (typeof window.YooMoneyCheckoutWidget === 'function') {
        clearYooWidgetWatchers();
        resolve(true);
      } else if (elapsed >= timeoutMs) {
        clearYooWidgetWatchers();
        reject(new Error('Виджет YooKassa не появился в отведённое время'));
      }
    }, step);

    yooWidgetTimeoutId = setTimeout(() => {
      // Резервный таймер, если по какой-то причине setInterval не сработал
      if (typeof window.YooMoneyCheckoutWidget !== 'function') {
        clearYooWidgetWatchers();
        reject(new Error('Таймаут ожидания виджета YooKassa'));
      }
    }, timeoutMs + 500);
  });
}

async function refreshPremiumStatusUI() {
  try {
    const res = await fetch('/api/premium/status');
    if (!res.ok) return;
    const data = await res.json();

    if (!window.__verifiedAuth) {
      window.__verifiedAuth = { ok: true, telegram_id: data.telegram_id, profile: {} };
    }
    window.__verifiedAuth.profile = {
      ...(window.__verifiedAuth.profile || {}),
      premium_active: !!data.premium_active,
      premium_expire_date: data.premium_expire_date || null,
    };

    if (!data.premium_active) return;

    const card = document.querySelector('.premium-card-inner');
    if (!card) return;

    const statusEl = card.querySelector('.premium-status');
    const subtextEl = card.querySelector('.premium-subtext');
    const expireEl = card.querySelector('.premium-expire');
    const plansEl = card.querySelector('.premium-plans');
    const actionsEl = card.querySelector('.premium-actions');

    if (statusEl) {
      statusEl.textContent = 'У тебя уже есть премиум';
    }
    if (subtextEl) {
      subtextEl.textContent = 'Новая подписка станет доступна после окончания текущей.';
    }

    if (plansEl) plansEl.style.display = 'none';
    if (actionsEl) actionsEl.style.display = 'none';

    if (data.premium_expire_date) {
      const d = new Date(data.premium_expire_date);
      const formatted = d.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
      });
      if (expireEl) {
        expireEl.textContent = `Активен до ${formatted}`;
      } else {
        const p = document.createElement('p');
        p.className = 'premium-expire';
        p.textContent = `Активен до ${formatted}`;
        subtextEl?.insertAdjacentElement('afterend', p);
      }
    }
  } catch (e) {
    console.error('[premium] refreshPremiumStatusUI error', e);
  }
}

async function startPayment(telegramId, durationDays) {
  try {
    await waitForWidget();
  } catch (e) {
    console.warn('[premium] YooMoneyCheckoutWidget недоступен:', e);
    showVpnNoticeOnce(() => window.location.reload());
    return;
  }

  clearYooWidgetWatchers();

  const res = await fetch('/api/premium/payment', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ telegram_id: telegramId, duration_days: durationDays }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || 'Ошибка при создании платежа');
  }

  const payment = await res.json();
  const token = payment.confirmation_token;
  if (!token) {
    throw new Error('Нет confirmation_token от YooKassa');
  }

  const overlay = document.getElementById('payment-form');
  const containerId = 'payment-form-inner';
  const container = document.getElementById(containerId);
  if (!overlay || !container) {
    alert('Контейнер для оплаты не найден на странице');
    return;
  }
  overlay.style.display = 'flex';

  const returnUrl = window.location.href;
  const tg = window.Telegram?.WebApp;

  const checkout = new window.YooMoneyCheckoutWidget({
    confirmation_token: token,
    return_url: returnUrl,
    error_callback: function (error) {
      console.error('Payment error', error);
      haptics?.notify?.('error');
      // При ошибке скрываем оверлей, чтобы пользователь мог попробовать ещё раз
      overlay.style.display = 'none';
      tg?.showPopup?.({
        title: 'Ошибка оплаты',
        message: 'Не удалось провести оплату. Попробуйте ещё раз.',
        buttons: [{ type: 'ok' }],
      });
    },
    success_callback: async function () {
      // YooKassa перенаправит на return_url после завершения, но для WebApp покажем явный popup
      haptics?.notify?.('success');
      tg?.showPopup?.({
        title: 'Успешно',
        message: 'Оплата прошла, премиум будет активирован в течение минуты.',
        buttons: [{ type: 'ok' }],
      });
      try {
        await refreshPremiumStatusUI();
      } finally {
        overlay.style.display = 'none';
      }
    },
  });

  checkout.render(containerId);
}

// Инициализация страницы премиума

document.addEventListener('DOMContentLoaded', () => {
  // Наблюдаем за появлением виджета, но не мешаем клику
  try {
    const script = document.querySelector('script[src*="checkout-widget"]');
    if (script) {
      script.addEventListener('load', () => { yooScriptLoaded = true; }, { once: true });
      script.addEventListener('error', () => {
        console.error('[premium] Ошибка загрузки скрипта YooKassa');
        showVpnNoticeOnce(() => window.location.reload());
      }, { once: true });
    }
  } catch {}

  const buyBtn = document.getElementById('premium-buy');
  if (!buyBtn) return;

  buyBtn.addEventListener('click', async () => {
    try {
      const auth = await ensureAuth();
      if (!auth?.ok) {
        alert('Не удалось авторизоваться через Telegram WebApp');
        return;
      }
      const telegramId = getVerifiedId();
      if (!telegramId) {
        alert('Не удалось определить Telegram ID');
        return;
      }
      const durationBtn = document.querySelector('.premium-plan.is-active');
      const durationDays = durationBtn ? durationBtn.dataset.duration : '365';
      await startPayment(telegramId, durationDays);
    } catch (e) {
      console.error('[premium] Ошибка оплаты:', e);
      alert(e.message || 'Ошибка оплаты');
    }
  });

  // При заходе на страницу сразу обновим UI премиума по статусу
  refreshPremiumStatusUI();
});
