import asyncio
import json

import httpx

from app.config import settings


async def main():
    """Простой CLI‑тест: создаёт платёж в YooKassa и печатает сырой ответ.

    Перед запуском укажи тестовые креды в переменных окружения или .env:
    YOOKASSA_SHOP_ID=...
    YOOKASSA_SECRET_KEY=...
    """
    if not settings.YOOKASSA_SHOP_ID or not settings.YOOKASSA_SECRET_KEY:
        print("[ERROR] YOOKASSA_SHOP_ID / YOOKASSA_SECRET_KEY не заданы в конфиге")
        return

    auth = (settings.YOOKASSA_SHOP_ID, settings.YOOKASSA_SECRET_KEY)

    body = {
        "amount": {"value": "2.00", "currency": "RUB"},
        "confirmation": {"type": "embedded"},
        "capture": True,
        "description": "Test payment from yookassa_test.py",
        "metadata": {"source": "cli-test"},
    }

    headers = {
        "Idempotence-Key": "cli-test-payment",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            "https://api.yookassa.ru/v3/payments",
            json=body,
            auth=auth,
            headers=headers,
        )

    print("Status:", resp.status_code)
    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text}
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

