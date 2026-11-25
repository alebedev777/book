# Персонализированные детские книги (Telegram Mini App)

Монорепозиторий: FastAPI + Celery + MinIO + Postgres, Telegram-бот (Aiogram), React Mini App.

## Требования

- **Рекомендуется:** Docker Desktop (весь стек).
- Локальный venv: **Python 3.11+** (`backend/pyproject.toml`). На macOS со встроенным Python 3.9 используйте Docker или `brew install python@3.12`, затем `python3.12 -m venv backend/.venv`.

Если `pip install` падает с ошибкой `cacert.pem` — удалите сломанный venv (`rm -rf backend/.venv`) и создайте заново после появления сети и рабочего Python 3.11+.

## Быстрый старт

1. Скопируйте `.env.example` → `.env`, задайте `BOT_TOKEN`, при необходимости `OPENAI_API_KEY` и `OPENAI_BASE_URL` (если ходите через прокси).
2. Поднимите весь стек из **корня репозитория**:

```bash
docker compose up --build
```

Сервисы: `postgres`, `redis`, `minio`, `api`, `worker`, `beat`, `bot`. Статическая Mini App в nginx: `docker compose --profile miniapp up --build`.

Если порты заняты (например Langfuse на 5432), задайте в `.env`:

```bash
BOOK_POSTGRES_PORT=5433
BOOK_REDIS_PORT=6380
BOOK_MINIO_PORT=9002
BOOK_API_PORT=8000
BOOK_MINIAPP_PORT=5173
```

3. Backend локально (через [uv](https://docs.astral.sh/uv/)):

```bash
cd backend && uv sync && uv run uvicorn app.main:app --reload --port 8000
```

4. Mini App (локально с hot reload):

```bash
cd miniapp && npm install && npm run dev
```

С телефона `/ создание заказа` API должен быть доступен публично: в `miniapp/.env` задайте `VITE_API_URL` (см. ниже).

## Проверка в Telegram (локальный mini app)

Telegram открывает Web App **только по HTTPS** (кроме тестов в десктопном клиенте). Типовой сценарий:

1. Поднимите API и worker (`docker compose up` или uvicorn + celery локально).
2. Запустите mini app: `cd miniapp && npm run dev` (порт 5173).
3. Два туннеля (пример с [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/)):

```bash
cloudflared tunnel --url http://127.0.0.1:5173
cloudflared tunnel --url http://127.0.0.1:8000
```

4. В **корневом `.env`**:
   - `MINI_APP_URL=https://<url-туннеля-5173>/` (со слэшем на конце)
   - перезапустите `bot` (контейнер или `uv run python bot/main.py`)
5. В **`miniapp/.env`** (для Vite): `VITE_API_URL=https://<url-туннеля-8000>` и **перезапустите** `npm run dev` (URL вшивается при старте).
6. В [@BotFather](https://t.me/BotFather): `/mybots` → ваш бот → **Bot Settings → Menu Button** (или Web App) → URL = тот же `MINI_APP_URL`.
7. В Telegram: `/start` → «Создать книгу». `initData` пойдёт на API; заказ обработает worker.

Альтернатива туннелю для фронта: `docker compose --profile miniapp up --build` и туннель на порт `BOOK_MINIAPP_PORT` (nginx), но для разработки удобнее Vite.

## OpenAI через прокси

- `OPENAI_BASE_URL` — база API без `/images` (для RouterAI: `https://routerai.ru/api/v1`).
- Картинки: `POST {OPENAI_BASE_URL}/images` (как в [доке RouterAI](https://routerai.ru/docs/guides/overview/multimodal/image-generation)).
- `OPENAI_VISION_MODEL` — отдельная модель для разбора фото ребёнка (если chat-модель без vision).

## API

- `GET /health`
- `GET /api/themes`, `GET /api/styles`
- `POST /api/orders` (multipart: init_data, theme, style, child_name, photo, consent)
- `GET /api/orders/{id}?init_data=...`

Без `OPENAI_API_KEY` worker генерирует демо-книгу (заглушки текста и картинок) для проверки пайплайна.

## Локальная генерация в `output/` (без БД)

Проверка промптов и картинок одной командой — ключи из корневого `.env`:

```bash
cd backend && uv run python scripts/generate_book_local.py
```

Другой файл/имя/тема:

```bash
uv run python scripts/generate_book_local.py /path/to/photo.jpg --name Андрей --age 10 --theme patience --style disney
```

Результат: `output/<uuid>/` — `book.pdf`, `cover.jpg`, `hero_reference.jpg`, `pages/*.jpg`, `story.json`.

## Langfuse (локально)

1. Подними Langfuse (у вас уже может быть стек на `localhost:3000`).
2. В UI: **Project → Settings → API Keys** → скопируй `pk-lf-…` и `sk-lf-…` в `.env`:
   - `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`
   - `LANGFUSE_BASE_URL=http://127.0.0.1:3000` (или `LANGFUSE_HOST` — то же самое)
3. Перезапусти **worker** и **api** (трассы идут из Celery при генерации книги).
4. В Langfuse: трасса `generate_book` → вложенные `story_text`, `character_vision`, `hero_reference`, `cover_image`, `page_image`, вызовы chat через OpenAI SDK.
5. Промпт сказки — chat prompt `story` (метка `production`). Файлы `shared/prompts/story_system.md` и `story_user.md` — fallback и исходник для публикации:

```bash
cd backend && uv run python scripts/push_prompts.py
```

Пустые ключи — трассировка и Langfuse-промпты отключены, текст берётся из файлов.

## Деплой на VPS

Пошагово: [docs/DEPLOY-VPS.md](docs/DEPLOY-VPS.md) (Docker, nginx, Let's Encrypt). **Нужен домен** на IP сервера — Telegram требует HTTPS.

## Структура

- `backend/` — API, worker, PDF, генерация
- `bot/` — long polling, кнопка WebApp
- `miniapp/` — мастер заказа
- `shared/` — темы, стили, промпты