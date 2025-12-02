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

```bash
pytest -q
uvicorn app.main:app --reload
```

Откройте Mini App и проверьте:
- Главная: первая картинка игр загружается сразу, остальные — лениво.
- Категории: выбор → переход работает, попап премиума показывается по условиям.
- Премиум: выбор плана, открытие `openInvoice`, обработка `invoiceClosed`.
- Игра: свайпы, анимации и микро‑взаимодействия работают.

# Продакшн‑деплой: домен, HTTPS и Docker (Ubuntu 22.04)

Ниже — пошаговая инструкция, как поднять приложение в проде на сервере с Ubuntu 22.04, доменом `flashq.online`, Docker и Nginx.

## 1. Подготовка домена (DNS)

1. Купите домен (например, `flashq.online`) у любого регистратора.
2. В панели регистратора создайте A‑запись:
   - Тип: `A`
   - Имя / Host: `@` (корень зоны) или пусто, в зависимости от регистратора
   - Значение: `195.225.110.249` (публичный IP сервера)
   - TTL: 300 (по умолчанию).
3. (Опционально) добавьте A‑запись для `www` → `195.225.110.249`, если хотите поддерживать и `www.flashq.online`.
4. Проверьте, что DNS обновился:

```bash
nslookup flashq.online
# или
dig +short flashq.online
```

Ожидаемый ответ: `195.225.110.249`.

## 2. Установка Nginx на сервере

Все команды ниже выполняются на сервере по SSH (Ubuntu 22.04).

```bash
sudo apt update
sudo apt install nginx -y
```

Проверьте, что Nginx запущен:

```bash
sudo systemctl status nginx
```

Если используете `ufw` (firewall), откройте HTTP/HTTPS:

```bash
sudo ufw allow 'Nginx Full'
sudo ufw reload
```

## 3. Настройка обратного прокси Nginx → Docker (fastapi)

Приложение внутри Docker слушает порт `8000` и проброшено наружу как `127.0.0.1:8000` (см. `docker-compose.yml`: `ports: "8000:8000"`).

Создайте конфиг сайта для Nginx:

```bash
sudo nano /etc/nginx/sites-available/flashq
```

Базовая HTTP‑конфигурация (до добавления HTTPS):

```nginx
server {
    listen 80;
    server_name flashq.online;

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}
```

Если вы хотите, чтобы работал и `www.flashq.online`, можно указать оба имени:

```nginx
server_name flashq.online www.flashq.online;
```

Активируйте конфиг и перезапустите Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/flashq /etc/nginx/sites-enabled/flashq
sudo nginx -t
sudo systemctl reload nginx
```

Проверьте, что HTTP‑версия открывается:

```bash
curl -I http://flashq.online
```

Если Docker‑контейнер `fastapi` запущен, вы должны получить ответ 200/301.

## 4. Установка HTTPS с сертификатом от RuCenter (без Certbot)

Если SSL‑сертификат выдаёт RuCenter (или другой провайдер), вы получаете файлы:

- `your_domain.crt` — основной сертификат (для `www.flashq.online`),
- `your_domain.key` — приватный ключ,
- `ca_bundle.crt` или `intermediate.crt` — цепочка промежуточных сертификатов.

### 4.1. Копирование сертификатов на сервер

Скопируйте файлы на сервер (пример с `scp`):

```bash
scp your_domain.crt your_domain.key ca_bundle.crt user@195.225.110.249:/tmp/
```

На сервере создайте каталог и перенесите файлы:

```bash
sudo mkdir -p /etc/ssl/flashq.online

sudo cp /tmp/your_domain.crt /etc/ssl/flashq.online/flashq.online.crt
sudo cp /tmp/your_domain.key /etc/ssl/flashq.online/flashq.online.key
sudo cp /tmp/ca_bundle.crt /etc/ssl/flashq.online/ca_bundle.crt

sudo chmod 600 /etc/ssl/flashq.online/flashq.online.key
```

Имена файлов можно адаптировать, главное — последовательно использовать их в конфиге Nginx.

### 4.2. Обновление конфига Nginx для HTTPS

Откройте конфиг `/etc/nginx/sites-available/flashq` и замените содержимое на следующее:

```nginx
# HTTP → редирект на HTTPS
server {
    listen 80;
    server_name flashq.online;

    return 301 https://$host$request_uri;
}

# HTTPS
server {
    listen 443 ssl;
    server_name flashq.online;

    ssl_certificate           /etc/ssl/flashq.online/flashq.online.crt;
    ssl_certificate_key       /etc/ssl/flashq.online/flashq.online.key;
    ssl_trusted_certificate   /etc/ssl/flashq.online/ca_bundle.crt;

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}
```

(Опционально) если вы добавили A‑запись для `www.flashq.online`, можно указать оба домена:

```nginx
server_name flashq.online www.flashq.online;
```

Проверьте конфигурацию и перезапустите Nginx:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

Проверьте HTTPS:

```bash
curl -I https://flashq.online
```

Ожидаемый ответ: `HTTP/2 200` (или `301` → `200`).

> Обновление такого сертификата делается вручную: когда RuCenter выдаёт новый сертификат, нужно заменить файлы в `/etc/ssl/flashq.online/` и выполнить `nginx -t && systemctl reload nginx`.

## 5. Настройка `.env` для продакшена (BASE_SITE и хосты БД/Redis)

В корне проекта есть файл `.env`, который читает `app/config.py`. Для продакшена важно:

1. Указать домен с HTTPS:

```env
BASE_SITE=https://flashq.online
```

2. Настроить хосты БД и Redis для Docker‑сети (см. `docker-compose.yml`, имена сервисов `database` и `redis`):

```env
DB_HOST=database
DB_PORT=5432
REDIS_HOST=redis
REDIS_PORT=6379
```

3. Убедиться, что заданы ключевые переменные:

```env
BOT_TOKEN=...                 # токен Telegram-бота
ADMIN_USERNAME=admin          # логин админа
ADMIN_PASSWORD=supersecret    # пароль админа
YOOKASSA_SHOP_ID=...
YOOKASSA_SECRET_KEY=...
# и другие ваши настройки
```

После изменения `.env` перезапустите Docker‑сервисы:

```bash
docker compose down
docker compose up -d --build
```

При старте контейнера:
- выполнятся миграции Alembic (`alembic upgrade head`),
- запустится `create_admin.py`, который создаст/обновит админа из `ADMIN_USERNAME`/`ADMIN_PASSWORD`,
- поднимется Gunicorn c приложением FastAPI на `0.0.0.0:8000`.

## 6. Обновление webhook Telegram и Mini App

В коде используется `settings.BASE_SITE` для построения URL вебхука, например:

```python
webhook_url = settings.get_webhook_url()  # вернет https://flashq.online/webhook
```

После того как:
- домен `flashq.online` настроен на сервер,
- Nginx + HTTPS работают,
- `.env` содержит `BASE_SITE=https://flashq.online`,

нужно убедиться, что у бота настроен корректный webhook:

1. Через Bot API:

```bash
curl -X POST \
  "https://api.telegram.org/bot$BOT_TOKEN/setWebhook" \
  -d "url=https://flashq.online/webhook"
```

2. Проверить:

```bash
curl "https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo"
```

Должен быть `"url": "https://flashq.online/webhook"` и `last_error_date`/`last_error_message` либо отсутствуют, либо не критичны.

**Важно для WebApp:**
- Мини‑апп в настройках BotFather должен использовать HTTPS‑URL с этим доменом (например, `https://flashq.online/`).
- Telegram WebApp по HTTP не работает (кроме `localhost`), поэтому `BASE_SITE` всегда должен быть `https://...`.

## 7. Docker‑сервис и healthchecks

`docker-compose.yml` уже содержит healthchecks и зависимости:

- Postgres (`db`) проверяется через `pg_isready`.
- Redis (`redis`) — через `redis-cli ping`.
- FastAPI (`fastapi`) — через запрос к `/health` внутри контейнера:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://127.0.0.1:8000/health"]
  interval: 10s
  timeout: 5s
  retries: 10
```

Адрес `http://127.0.0.1:8000/health` здесь — это **внутренний** loopback внутри контейнера `fastapi`, а не внешний домен. В проде его менять не нужно: внешние пользователи ходят на `https://www.flashq.online`, а Docker healthcheck проверяет, живо ли приложение изнутри контейнера.

## 8. Медиа‑файлы и volume для админки

Загружаемые через админ‑панель изображения сохраняются в `app/media` внутри проекта. В Docker это путь `/api/app/media`. В `docker-compose.yml` уже настроен bind‑mount:

```yaml
fastapi:
  ...
  volumes:
    - ./app/media:/api/app/media
```

Благодаря этому:
- медиа‑файлы не теряются при пересборке образа,
- их можно бэкапить и просматривать прямо на хосте в директории `app/media`.

Убедитесь, что на сервере папка существует:

```bash
mkdir -p app/media
```
