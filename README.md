# Tests

## Running tests

Install dev dependencies and run tests:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-asyncio
pytest -q
```

## What is covered

- Unit tests for services (users, honesty) with DAO mocking
- Integration tests for DAO using in-memory SQLite DB (async)
- Basic router smoke test

## Notes

- The test DB uses SQLite in-memory and creates schema from SQLAlchemy models at startup.
- If your app requires Postgres-only features, adapt tests to use a test Postgres instance.

# Руководство: добавление фронтовых страниц и шаблонов (Telegram Mini App)

Ниже — краткий, практичный порядок, как добавить новую страницу (шаблон + JS + стиль) в текущем фронтенде. Мы уже используем модульный JS, безопасную авторизацию и единый базовый шаблон.

## Где лежат файлы
- Шаблоны: `app/frontend/templates/`
- Общие стили: `app/frontend/static/css/webapp.css`
- Скрипты (модули): `app/frontend/static/js/`
- Маршруты фронтенда: `app/frontend/pages/router.py`
- Базовый шаблон: `app/frontend/templates/base.html`

## 1) Создать шаблон страницы
1. В `app/frontend/templates/` создайте файл, например, `my_page.html`.
2. Структура шаблона:
   - расширяет базовый шаблон `base.html`
   - подключает общий CSS (у нас веб‑стили уже в `base.html` или страницах)
   - блок content — ваша разметка
   - в блок scripts подключите модульную страницу `my_page.js`

Пример:

```
{% extends 'base.html' %}
{% block title %}Моя страница{% endblock %}
{% block styles %}
<link rel="stylesheet" href="/static/css/webapp.css?v=10">
{% endblock %}
{% block content %}
<div class="page my-page">
  <header class="page-header">
    <h2 class="page-title">Заголовок</h2>
  </header>
  <main class="page-main">
    <!-- ваша разметка -->
  </main>
</div>
{% endblock %}
{% block scripts %}
<script type="module" src="/static/js/haptics.js"></script>
<script type="module" src="/static/js/auth.js"></script>
<script type="module" src="/static/js/my_page.js?v=1"></script>
{% endblock %}
```

Примечания:
- `base.html` уже подключает Telegram SDK (`telegram-web-app.js`) и общий инициализатор (`telegram_init.js`), плюс глобальные модули `haptics.js` и `auth.js`. Если вы их подключаете в `base.html`, повторно добавлять их на странице можно не делать — оставьте только модуль страницы.
- Используйте cache‑busting параметр `?v=...` для обновления кэша мини‑аппа после деплоя.

## 2) Создать модульный скрипт для страницы
В `app/frontend/static/js/` создайте `my_page.js`. Рекомендуется:
- Обеспечить безопасную авторизацию: вызвать `ensureAuth()` на старте (по возможности).
- Использовать только проверенный `telegram_id` из `getVerifiedId()` и/или серверную сессию.
- Использовать haptics через `haptics` модуль.

Пример:

```
import { ensureAuth, getVerifiedId } from '/static/js/auth.js';
import { haptics } from '/static/js/haptics.js';

document.addEventListener('DOMContentLoaded', async () => {
  await ensureAuth();
  const verifiedId = getVerifiedId();

  // ваша логика страницы
  const btn = document.getElementById('do-something');
  btn?.addEventListener('click', () => {
    haptics.impact('medium');
    // пример перехода с verified id
    const url = new URL('/premium', window.location.origin);
    if (verifiedId) url.searchParams.set('telegram_id', verifiedId);
    window.location.href = url.toString();
  });
});
```

Примечания:
- Не используйте `initDataUnsafe` в коде страницы. Всегда опирайтесь на результат `/api/auth` (который кладёт `telegram_id` в сессию и `window.__verifiedAuth`).
- Для запросов `fetch` к API, при необходимости, добавляйте `credentials: 'include'`, если приложение работает на другом домене и нужно отправлять cookies.

## 3) Прописать роут
Добавьте маршрут в `app/frontend/pages/router.py`:

```
@router_webapp.get('/my-page', response_class=HTMLResponse)
async def my_page(request: Request, telegram_id: Optional[int] = None):
    ctx = await _get_user_context(request, telegram_id)  # фолбэк на сессию
    return templates.TemplateResponse('my_page.html', {"request": request, **ctx})
```

Примечания:
- Хелпер `_get_user_context(request, telegram_id)` сначала возьмёт `telegram_id` из параметра, а если его нет — из сессии (после `/api/auth`). Это даёт стабильный доступ к профилю и подписке.

## 4) Работа с изображениями и производительностью
- Для критически важной первой картинки используйте `loading="eager" fetchpriority="high" decoding="async"`.
- Для остальных — `loading="lazy" fetchpriority="low" decoding="async"`.
- Указывайте `width` и `height` на `<img>`, чтобы браузер резервировал пространство и уменьшал «скачки» контента.

## 5) Haptics и UX микро‑взаимодействия
- Используйте модуль `haptics.js`:
  - `haptics.impact('light' | 'medium' | 'soft' | 'rigid')`
  - `haptics.selection()`
  - `haptics.notify('success' | 'error')`
- На свайпы/перемещения — `selection()`; на клики — `impact('medium')`; на успешные операции — `notify('success')`.

## 6) Безопасность Telegram WebApp
- На старте мини‑аппа отправляйте сырую строку `Telegram.WebApp.initData` на `/api/auth` (это делает `telegram_init.js`).
- Сервер проверяет подпись (HMAC‑SHA256 WebAppData + BOT_TOKEN) и TTL `auth_date` ≤ 1 час.
- Используйте только проверенный идентификатор пользователя из сессии/`window.__verifiedAuth`.
- Никогда не доверяйте `initDataUnsafe`.

## 7) Кэш и обновление мини‑аппа
- При изменении JS/CSS увеличивайте версию `?v=...` в шаблоне, чтобы Telegram Mini App подхватил свежие файлы.
- В самом Telegram клиенте иногда нужен перезапуск мини‑аппа, чтобы сбросить кэш.

## 8) Быстрый чеклист при добавлении новой страницы
- [ ] Создан шаблон `my_page.html` и подключён модуль `my_page.js`.
- [ ] В `my_page.js` есть вызов `ensureAuth()` и используются только проверенные данные.
- [ ] Роут добавлен в `router.py` и использует `_get_user_context`.
- [ ] Картинки оптимизированы (`loading`, `fetchpriority`, `decoding`, размеры).
- [ ] Вибрации подключены через `haptics.js`.
- [ ] Версии скриптов обновлены (`?v=`), мини‑апп перезапущен.

## 9) Пример быстрой проверки
Локально запустить тесты и сервер (команды адаптируйте под ваш окружение):

```bash
pytest -q
uvicorn app.main:app --reload
```

Откройте Mini App и проверьте:
- Главная: первая картинка игр загружается сразу, остальные — лениво.
- Категории: выбор → переход работает, попап премиума показывается по условиям.
- Премиум: выбор плана, открытие `openInvoice`, обработка `invoiceClosed`.
- Игра: свайпы, анимации и микро‑взаимодействия работают.
