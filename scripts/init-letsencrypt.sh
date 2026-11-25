#!/usr/bin/env bash
# Первичная выдача Let's Encrypt для nginx (Docker volumes certbot_conf / certbot_www).
# Запуск из корня репозитория на VPS, после того как DEPLOY_DOMAIN смотрит на сервер.
#
#   export DEPLOY_DOMAIN=book.example.com
#   ./scripts/init-letsencrypt.sh you@example.com
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

COMPOSE=(docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile miniapp)

DOMAIN="${DEPLOY_DOMAIN:-}"
EMAIL="${1:-}"

if [[ -z "$DOMAIN" ]]; then
  echo "Задайте DEPLOY_DOMAIN в .env или в окружении." >&2
  exit 1
fi
if [[ -z "$EMAIL" ]]; then
  echo "Usage: DEPLOY_DOMAIN=$DOMAIN ./scripts/init-letsencrypt.sh you@example.com" >&2
  exit 1
fi

STAGING="${LETSENCRYPT_STAGING:-0}"
CERT_PATH="/etc/letsencrypt/live/$DOMAIN"

echo "→ Временный сертификат (чтобы nginx поднялся на 443)…"
"${COMPOSE[@]}" run --rm --entrypoint sh certbot -c "
  set -e
  if [ ! -f '$CERT_PATH/fullchain.pem' ]; then
    mkdir -p '$CERT_PATH'
    openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
      -keyout '$CERT_PATH/privkey.pem' \
      -out '$CERT_PATH/fullchain.pem' \
      -subj '/CN=localhost'
  fi
"

echo "→ Сборка и запуск приложения + nginx (временный сертификат)…"
"${COMPOSE[@]}" up -d --build postgres redis minio api worker beat bot miniapp nginx

echo "→ Запрос боевого сертификата Let's Encrypt…"
CERTBOT_ARGS=(certonly --webroot -w /var/www/certbot -d "$DOMAIN" --email "$EMAIL" --rsa-key-size 4096 --agree-tos --no-eff-email --force-renewal)
if [[ "$STAGING" == "1" ]]; then
  CERTBOT_ARGS+=(--staging)
fi

# entrypoint сервиса — цикл renew, он не выполняет аргументы run.
"${COMPOSE[@]}" run --rm --entrypoint certbot certbot "${CERTBOT_ARGS[@]}"

echo "→ certbot (автопродление)…"
"${COMPOSE[@]}" up -d certbot

echo "→ Перезагрузка nginx с боевым сертификатом…"
"${COMPOSE[@]}" exec nginx nginx -s reload

echo "Готово. Проверка: curl -s https://$DOMAIN/health"