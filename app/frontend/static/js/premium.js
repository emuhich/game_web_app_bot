import { haptics } from '/static/js/haptics.js';
import { getVerifiedId, ensureAuth } from '/static/js/auth.js';

document.addEventListener('DOMContentLoaded', async () => {
  await ensureAuth();
  const tg = window.Telegram?.WebApp;
  const verifiedId = getVerifiedId();

  const planButtons = Array.from(document.querySelectorAll('.premium-plan'));
  const buyBtn = document.getElementById('premium-buy');

  planButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      planButtons.forEach(b => b.classList.remove('is-active'));
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
      const params = new URLSearchParams({ telegram_id: String(verifiedId), duration_days: duration });
      const res = await fetch(`/api/premium/invoice?${params.toString()}`);
      if (!res.ok) throw new Error('Ошибка при создании счёта');
      const data = await res.json();
      if (!data.invoice_url) throw new Error('invoice_url не получен');
      tg?.openInvoice(data.invoice_url);
    } catch (e) {
      console.error(e);
      tg?.showAlert?.('Не удалось создать платёж. Попробуй позже.');
      haptics.impact('light');
    }
  });

  if (tg && tg.onEvent) {
    tg.onEvent('invoiceClosed', ({ status }) => {
      if (status === 'paid') {
        haptics.notify('success');
        tg.showPopup({
          title: 'Успешно',
          message: 'Платёж принят! Подписка будет активирована в течение нескольких секунд.',
          buttons: [{ type: 'ok' }]
        });
        setTimeout(() => { window.location.reload(); }, 1500);
      } else if (status === 'cancelled') {
        haptics.impact('soft');
      } else if (status === 'failed') {
        haptics.notify('error');
      }
    });
  }
});

