import { haptics } from '/static/js/haptics.js';
import { getVerifiedId, ensureAuth } from '/static/js/auth.js';

// Загружаем скрипт YooKassa виджета динамически, если он ещё не подключен
function loadYooKassaScript() {
  return new Promise((resolve, reject) => {
    if (window.YooKassaCheckoutWidget) {
      resolve();
      return;
    }
    const script = document.createElement('script');
    script.src = 'https://yookassa.ru/checkout-widget/v1/checkout-widget.js';
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('Не удалось загрузить виджет оплаты'));
    document.head.appendChild(script);
  });
}

async function refreshPremiumStatusUI() {
  try {
    const res = await fetch('/api/premium/status');
    if (!res.ok) return;
    const data = await res.json();

    // Обновляем глобальный кэш авторизации, чтобы другие части фронта видели актуальный премиум
    if (!window.__verifiedAuth) {
      window.__verifiedAuth = { ok: true, telegram_id: data.telegram_id, profile: {} };
    }
    window.__verifiedAuth.profile = {
      ...(window.__verifiedAuth.profile || {}),
      premium_active: !!data.premium_active,
      premium_expire_date: data.premium_expire_date || null,
    };

    if (!data.premium_active) return;

    // Обновляем DOM на странице премиума
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
  await loadYooKassaScript();

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

  const containerId = 'payment-container';
  let container = document.getElementById(containerId);
  if (!container) {
    container = document.createElement('div');
    container.id = containerId;
    container.className = 'payment-container-overlay';
    document.body.appendChild(container);
  }

  const checkout = new window.YooKassaCheckoutWidget({
    confirmation_token: token,
    error_callback: function (error) {
      console.error('Payment error', error);
      haptics.notify('error');
    },
    success_callback: async function () {
      haptics.notify('success');
      const tg = window.Telegram?.WebApp;
      tg?.showPopup?.({
        title: 'Успешно',
        message: 'Оплата прошла, премиум скоро активируется.',
        buttons: [{ type: 'ok' }],
      });
      // После успешной оплаты пробуем обновить статус премиума и UI
      await refreshPremiumStatusUI();
    },
  });

  checkout.render(containerId);
}

document.addEventListener('DOMContentLoaded', async () => {
  await ensureAuth();
  const tg = window.Telegram?.WebApp;
  const verifiedId = getVerifiedId();

  const planButtons = Array.from(document.querySelectorAll('.premium-plan'));
  const buyBtn = document.getElementById('premium-buy');

  planButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      planButtons.forEach((b) => b.classList.remove('is-active'));
      btn.classList.add('is-active');
      haptics.selection();
    });
  });

  if (!buyBtn) return;

  buyBtn.addEventListener('click', async () => {
    haptics.impact('medium');
    const active = document.querySelector('.premium-plan.is-active');
    const duration = active?.dataset.duration || '365';

    if (!verifiedId) {
      tg?.showAlert?.('Авторизация не выполнена');
      haptics.impact('rigid');
      return;
    }

    try {
      await startPayment(verifiedId, duration);
    } catch (e) {
      console.error(e);
      tg?.showAlert?.('Не удалось создать платёж. Попробуй позже.');
      haptics.impact('light');
    }
  });
});
