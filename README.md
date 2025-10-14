# Indie Game Radar

Async service that discovers promising indie games from Steam, enriches data from IGDB, scores them, and publishes top picks to Telegram.

## Features
- Fully async stack: httpx, Motor (MongoDB), Redis cache.
- IGDB official OAuth (Twitch), retries, rate limiting, JSON logging.
- Automatic scoring and filtering, periodic scheduler (asyncio).

## Requirements
- Python 3.11+
- MongoDB
- Redis

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` from example and fill secrets:
```bash
cp .env.example .env
```

## Run
- One-shot run:
```bash
ONE_SHOT=true python main.py
```
- Periodic run (every RUN_INTERVAL_SECONDS):
```bash
python main.py
```

## Environment (.env)
See `.env.example` for all variables.

## Notes
- Logs are JSON to stdout.
- Adjust scoring weights in `config/constants.py`.
- Change thresholds and intervals in `config/settings.py` via env vars.
