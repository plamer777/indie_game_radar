# Indie Game Radar

Async, long-running worker that discovers promising indie games from Steam, enriches metadata via IGDB, analyzes community signals (Reddit, reviews, activity), ranks candidates, and publishes curated posts to Telegram.

## Features
- Fully async stack: httpx, Motor (MongoDB), Redis cache, structlog JSON logging
- Sources: Steam Store & WebAPI (details, reviews, news, achievements, players), IGDB (OAuth via Twitch), Reddit (asyncpraw), Speedrun.com
- Ranking & filtering: multi-signal scoring + heuristics; LLM-assisted filtering and copy editing (OpenAI)
- Daily allocation runs 08:00–16:00 UTC; posts are scheduled across 08:00–22:00 UTC using a content mix strategy
- Persistence in MongoDB; reusable repositories pattern; Redis caching

## Architecture overview
- Entry point: `main.py` launches the `Orchestrator`
- Composition root: `src/container.py` wires clients, repositories, and services
- Orchestrator (`src/orchestrators/core_orchestrator.py`):
  - Starts the harvester loop (Steam/IGDB/Reddit/Speedrun) and ranking loop
  - Allocates posts daily and schedules publications during the posting window
- Services:
  - `APIHarvesterService` — collects game data, news, reviews, Reddit posts, speedrun leaderboards; stores in Mongo
  - `RankEngineService` — scores and filters games, discounts, news, Reddit posts, reviews, leaderboards
  - `PublisherService` — renders text and publishes messages/photos/videos to Telegram
- Storage & cache: MongoDB (Motor), Redis (asyncio client)
- Logging: structured JSON via structlog

## Project layout
```
.
├── main.py
├── src/
│   ├── container.py
│   ├── config/
│   │   ├── settings.py          # loads required secrets from .env (pydantic-settings)
│   │   └── constants.py         # runtime constants (scoring, windows, limits)
│   ├── clients/                 # Steam, IGDB, Reddit, Telegram, Speedrun
│   ├── db/
│   │   ├── mongo.py             # motor client and (optional) index creation helper
│   │   └── repositories/        # Mongo repositories (games, publications, etc.)
│   ├── orchestrators/           # core orchestrator + content allocation strategy
│   ├── services/
│   │   ├── data_service/        # APIHarvesterService
│   │   ├── rank_service/        # RankEngineService + filters/rankers/adapters
│   │   └── publisher_service/   # PublisherService + renderers/editors
│   ├── managers/cache.py        # RedisCache
│   └── utils/logging.py         # structlog JSON configuration
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Prerequisites
- Python 3.11+ (Docker image uses 3.13-slim)
- MongoDB
- Redis

## Installation (local)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```
Fill `.env` with your own credentials (see below).

## Configuration (required .env)
The application reads the following variables via `src/config/settings.py`:
- `MONGO_URI`
- `IGDB_CLIENT_ID`, `IGDB_CLIENT_SECRET`
- `STEAM_API_KEY`
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- `OPEN_AI_KEY`
- `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`

Example:
```env
MONGO_URI=mongodb://localhost:27017

IGDB_CLIENT_ID=...
IGDB_CLIENT_SECRET=...

STEAM_API_KEY=...

TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=@your_channel_or_chat

OPEN_AI_KEY=...

REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
REDDIT_USER_AGENT=igr/0.1 by <your_name>
```

Notes:
- MongoDB database name and Redis URL are defined in `config/constants.py` (defaults: `indie_game_radar`, `redis://localhost:6379/0`).
- There is no HTTP server; the worker runs indefinitely. The Dockerfile exposes port 8000 but it is not used by the app.

## Running (local)
Ensure MongoDB and Redis are running and accessible per your `.env`.
```bash
python main.py
```
Behavior:
- Harvester loop runs continuously and aligns its cycles with 12:00 UTC
- Ranking runs periodically (default: every 10 minutes)
- Allocation window: 08:00–16:00 UTC; posts are scheduled across morning/day/evening (08:00–22:00 UTC) according to `TIME_PRIORITIES`
- Logs are structured JSON to stdout

## Docker
Build locally:
```bash
docker build -t indie-game-radar .
docker run --rm --env-file .env --network host indie-game-radar  # on Linux; gives direct access to localhost services
```

Using docker-compose (prebuilt image):
```bash
docker compose up -d
```
`docker-compose.yml` uses `network_mode: host` (Linux only). If you are on macOS/Windows or use remote Mongo/Redis, adjust networking and connection URIs accordingly.

## Operations and tuning
- Change scoring weights, filters, time windows, and limits in `src/config/constants.py`
- Posting cadence and allocation are governed by `DEFAULT_DAILY_POSTS`, `TIME_WINDOWS`, `TIME_PRIORITIES`, and the orchestrator

## Troubleshooting
- Missing/invalid `.env` values: `pydantic-settings` will fail on import with a clear error
- MongoDB connection errors: verify `MONGO_URI` and that Mongo is reachable from the app container/host
- IGDB 401/403: check `IGDB_CLIENT_ID`/`IGDB_CLIENT_SECRET` and Twitch application permissions
- Telegram errors (e.g., 400): verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` (use a bot to retrieve chat ID if needed)
- Reddit credentials: ensure the app is created in Reddit and `REDDIT_USER_AGENT` is unique and descriptive

## License
Private
