# Деплой на VPS (Docker + nginx + Let's Encrypt)

Telegram Mini App открывается только по **HTTPS**. Нужен **домен** (A-запись на IP сервера). На голый IP Let's Encrypt сертификат не выдадут.

Один домен: mini app и API на одном origin (проще для Telegram и CORS).

| URL | Сервис |
|-----|--------|
| `https://ваш-домен/` | mini app |
| `https://ваш-домен/api/...` | FastAPI |
| `https://ваш-домен/health` | healthcheck |

Схема: **nginx** (80/443) → контейнеры `miniapp` и `api`; сертификаты в volume `certbot_conf`, продление — контейнер **certbot**.

---

## 1. Домен

```text
A   book   →   153.76.117.51
```

Проверка:

```bash
dig +short book.ваш-домен.ru
```

---

## 2. Сервер: Docker

```bash
ssh root@153.76.117.51

apt-get update && apt-get install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sh
systemctl enable --now docker

ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

Postgres, Redis и MinIO наружу не публикуем — только nginx на 80/443.

---

## 3. Клонирование и `.env`

```bash
mkdir -p /opt/book && cd /opt/book
git clone https://github.com/alebedev777/book.git .
cp .env.example .env
nano .env
```

Обязательно (один и тот же домен):

```bash
DEPLOY_DOMAIN=book.ваш-домен.ru

BOT_TOKEN=...
MINI_APP_URL=https://book.ваш-домен.ru/
VITE_API_URL=https://book.ваш-домен.ru
API_PUBLIC_URL=https://book.ваш-домен.ru

OPENAI_API_KEY=...    # пусто = демо-книга
RATE_LIMIT_ACTIVE_ORDERS=1
```

---

## 4. Первый запуск и SSL

**Не поднимайте nginx вручную до сертификата** — без файлов в `/etc/letsencrypt` он не стартует. Используйте скрипт:

```bash
chmod +x scripts/init-letsencrypt.sh
set -a && source .env && set +a
./scripts/init-letsencrypt.sh ваш@email.com
```

Скрипт:

1. Создаёт однодневный временный сертификат в volume.
2. Собирает и поднимает стек (включая nginx).
3. Запрашивает боевой сертификат Let's Encrypt (webroot).
4. Делает `nginx -s reload`.

Тестовый стенд LE (лимиты мягче): `LETSENCRYPT_STAGING=1 ./scripts/init-letsencrypt.sh ...`

Проверка:

```bash
curl -s https://book.ваш-домен.ru/health
```

Дозапуск / обновление образов:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile miniapp up -d --build
```

Логи:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile miniapp logs -f api worker bot nginx
```

После смены `VITE_API_URL`:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile miniapp up -d --build miniapp bot
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile miniapp exec nginx nginx -s reload
```

---

## 5. Telegram

[@BotFather](https://t.me/BotFather) → Menu Button / Web App → URL = `MINI_APP_URL`.  
В боте: `/start` → «Создать книгу».

---

## 6. Обновление кода

```bash
cd /opt/book
git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile miniapp up -d --build
```

---

## 7. Продление сертификата

Контейнер `certbot` раз в 12 часов вызывает `certbot renew`. После обновления nginx лучше перезагрузить (можно в cron на хосте):

```bash
0 4 * * * cd /opt/book && docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile miniapp exec -T nginx nginx -s reload
```

---

## 8. Типичные проблемы

| Симптом | Что проверить |
|---------|----------------|
| nginx не стартует | Сначала `init-letsencrypt.sh`; DNS на IP; `docker logs book-nginx-1` |
| certbot refused | Порт 80 снаружи, `DEPLOY_DOMAIN` совпадает с DNS, нет лишнего nginx на хосте |
| Mini app не открывается | HTTPS в браузере; `MINI_APP_URL` в BotFather |
| initData / 401 | Открывать из Telegram, не по прямой ссылке в Safari |

---

## Свои сертификаты (без certbot)

Положите `fullchain.pem` и `privkey.pem` в volume `certbot_conf` по пути `live/$DEPLOY_DOMAIN/` (как у Let's Encrypt) и перезапустите nginx.

Конфиг шаблона: `infra/templates/edge.conf.template`.