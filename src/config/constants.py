from __future__ import annotations
# ---------------------------------------------------------------------------------------------------------------------
# Filtering thresholds and heuristics
FILTER_NAME_BLACKLIST_TOKENS = [
    "soundtrack",
    "dlc",
    "ost",
    "demo",
    "beta",
    "test",
]
FILTER_GENRE_BLACKLIST = [
    "education",
    "tutorial",
]
FILTER_REQUIRE_HEADER_IMAGE = True
FILTER_MAX_YEARS_SINCE_RELEASE = 8  # allow older only if score very high
FILTER_MIN_SCORE_FOR_OLD_TITLES = 0.85
FILTER_MAX_PRICE = 40.0  # USD-equivalent heuristic
FILTER_MIN_IGDB_RATING_COUNT = 10
FILTER_MIN_POPULARITY_SUM = 10  # follows + hypes floor
# ---------------------------------------------------------------------------------------------------------------------
# Retry defaults
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_BASE_DELAY = 0.5
DEFAULT_RETRY_MAX_DELAY = 5.0
DEFAULT_RETRY_JITTER = 0.2
# ---------------------------------------------------------------------------------------------------------------------
# Data model constraints
CURRENCY_CODE_LEN = 3
PERCENT_MAX = 100
RATIO_MIN = 0.0
RATIO_MAX = 1.0
ZERO = 0
MIN_STEAM_APPID = 1
# ---------------------------------------------------------------------------------------------------------------------
# Mongo index directions
ASC = 1
DESC = -1
# ---------------------------------------------------------------------------------------------------------------------
# Repository defaults
UNPUBLISHED_QUERY_LIMIT_DEFAULT = 100
LOOKUP_LIMIT_ONE = 1
GAMES_COLLECTION = "games"
IGDB_META_COLLECTION = "igdb_meta"
GAME_PUBLICATIONS_COLLECTION = "game_publications"
NEWS_PUBLICATIONS_COLLECTION = "news_publications"
APPS_COLLECTION = "steam_apps"
GAME_SNAPSHOTS_COLLECTION = "game_snapshots"
STATIC_FIELDS = ['created_at']
IGNORED_FIELDS = ['updated_at']
# ---------------------------------------------------------------------------------------------------------------------
# Telegram
DEFAULT_TELEGRAM_CHANNEL = "telegram"
SUMMARY_MAX_LEN = 500
WEBSITES_MAX = 2
PRICE_FREE_LABEL = "Free to Play"
PRICE_UNKNOWN_LABEL = "Unknown price"
WEBSITE_SEPARATOR = " | "
SCORE_DECIMALS = 2
TOP_GAMES_TO_PUBLISH = 1
TOP_NEWS_TO_PUBLISH = 1
# ---------------------------------------------------------------------------------------------------------------------
# IGDB queries
IGDB_SEARCH_LIMIT = 1
# ---------------------------------------------------------------------------------------------------------------------
# Steam
STEAM_PRICE_DIVISOR = 100.0
REVIEW_DAY_RANGE = 30
NEWS_COUNT = 20

SECONDS_IN_DAY = 86400
SECONDS_IN_HOUR = 3600
SECONDS_IN_MINUTE = 60

# Интервалы для анализа новостей (в днях)
NEWS_WINDOW_30D = 30
NEWS_WINDOW_90D = 90

# Округление числовых метрик
ROUND_PRECISION = 1
# ---------------------------------------------------------------------------------------------------------------------
# Orchestrator
ORCH_FETCH_GAME_CONCURRENCY = 10
ORCH_FETCH_META_CONCURRENCY = 5
ORCH_SCORE_CONCURRENCY = 20
ORCH_CANDIDATES_LIMIT_DEFAULT = 200
ORCH_NEWS_RANKING_BATCH_SIZE = 50
ORCH_RANKING_INTERVAL = SECONDS_IN_MINUTE * 10
# ---------------------------------------------------------------------------------------------------------------------
# Scheduler
SCHED_MIN_SLEEP_SECONDS = 1
SCHED_FIXED_HOURS_DEFAULT = [8, 12, 16, 20, 23]
# ---------------------------------------------------------------------------------------------------------------------
# Ranker normalization and buckets
RECENCY_YEAR_DENOMINATOR = 365.0
UNKNOWN_RECENCY_BASE = 0.2
POPULARITY_LOG_NORMALIZER = 5000
RATING_COUNT_LOG_NORMALIZER = 1000
DISCOUNT_NORMALIZE_MAX = 80.0
POPULARITY_HYPE_WEIGHT = 0.7
RATING_COUNT_BLEND_BASE = 0.5
RATING_COUNT_BLEND_SCALE = 0.5

REVIEW_VOLUME_NORMALIZER = 1000
NEWS_DECAY_DAYS = 60
NEWS_ACTIVITY_NORMALIZER = 5



# Weights for scoring games
# IGDB часть
WEIGHT_RATING = 0.10
WEIGHT_POPULARITY = 0.10
WEIGHT_RECENCY = 0.05

# Пользовательские сигналы (усиленные)
WEIGHT_USER_SENTIMENT = 0.35  # (reviews + recommendations)
WEIGHT_TREND = 0.10
WEIGHT_ACTIVITY = 0.10

# Контекст
WEIGHT_PRICE_ATTRACTIVENESS = 0.05
WEIGHT_DISCOUNT = 0.03
WEIGHT_NEWS = 0.02

# Прочие параметры
VOLATILITY_MAX_PENALTY = 0.12
VOLATILITY_SENSITIVITY = 0.5
MIN_SNAPSHOTS_REQUIRED = 5

PRICE_BUCKETS_USD = [5, 10, 15, 25]
PRICE_BUCKET_SCORES = [1.0, 0.85, 0.75, 0.5, 0.3]

# === Recommendations ===
RECOMMENDATION_LOG_SCALE = 10.0  # делитель при лог-нормализации

# === Recency boost ===
RECENT_GAME_AGE_DAYS = 180       # игра считается новой 6 месяцев
RECENCY_BASE_BOOST = 1.2         # максимальный буст в начале
RECENCY_FADE_DIVISOR = 900.0     # скорость затухания
RECENCY_MAX_BOOST = 1.2          # верхний предел буста

# === Aggregation (review vs recommendations) ===
REVIEW_WEIGHT = 0.6
RECOMMENDATION_WEIGHT = 0.4

# === IGDB factor ===
IGDB_FULL_DATA_FACTOR = 1.0
IGDB_PARTIAL_DATA_FACTOR = 0.5

# News ranker
# --- Общие настройки ---
MAX_NEWS_AGE_DAYS = 7  # после этого считается устаревшей

# --- Веса компонентов ---
WEIGHT_FRESHNESS = 0.30
WEIGHT_SOURCE = 0.20
WEIGHT_CONTENT_RICHNESS = 0.25
WEIGHT_GAME_QUALITY = 0.25

# --- Усиление для новинок ---
RECENCY_BOOST_MAX = 1.2
RECENCY_BOOST_DECAY_DAYS = 180

# --- Порог насыщенности контента ---
MAX_CONTENT_LENGTH = 1500


# ---------------------------------------------------------------------------------------------------------------------
# GameFilter tuning
PRICE_CAP_RELAX_SCORE_DELTA = 0.15  # allow higher price if score exceeds threshold by this delta
PRICE_CAP_STRICT_FACTOR = 0.8       # strict cap factor when score is near threshold
IGDB_FLOOR_RELAX_DELTA = 0.2        # relax IGDB floors if score exceeds threshold by this delta
# ---------------------------------------------------------------------------------------------------------------------