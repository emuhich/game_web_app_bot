// Простая обёртка над Telegram.WebApp.HapticFeedback с безопасными вызовами
export const haptics = {
  impact(level = 'light') {
    try { window.Telegram?.WebApp?.HapticFeedback?.impactOccurred?.(level); } catch {}
  },
  selection() {
    try { window.Telegram?.WebApp?.HapticFeedback?.selectionChanged?.(); } catch {}
  },
  notify(type = 'success') {
    try { window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred?.(type); } catch {}
  }
};

