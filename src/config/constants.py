from __future__ import annotations

import re

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
FILTER_MAX_YEARS_SINCE_RELEASE = 1  # allow older only if score very high
FILTER_MIN_SCORE_FOR_OLD_TITLES = 0.85
FILTER_MAX_PRICE = 40.0  # USD-equivalent heuristic
SCORE_PUBLISH_THRESHOLD = 0.5
# ---------------------------------------------------------------------------------------------------------------------
# Retry defaults
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_BASE_DELAY = 0.5
DEFAULT_RETRY_MAX_DELAY = 5.0
DEFAULT_RETRY_JITTER = 0.2
TOO_MANY_REQUESTS_DELAY = 90
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
RANKED_GAMES_COLLECTION = "ranked_games"
REDDIT_POSTS_COLLECTION = "reddit_posts"
RANKED_REDDIT_POSTS_COLLECTION = "ranked_reddit_posts"
IGDB_META_COLLECTION = "igdb_meta"
GAME_PUBLICATIONS_COLLECTION = "game_publications"
NEWS_PUBLICATIONS_COLLECTION = "news_publications"
DISCOUNT_PUBLICATIONS_COLLECTION = "discount_publications"
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
# Reddit client
GAMEDEV_SUBREDDITS = [
    # Общие по разработке
    "gamedev", "indiedev", "gameDevClassifieds", "IndieGaming", "IndieDev",
    "GameDesign", "GameDevelopment", "Unity3D", "UnrealEngine", "Godot",
    # Арт, визуалы, музыка
    "GameAudio", "PixelArt", "IndieArt", "GameAssets", "3Dmodeling",
    # Продвижение и маркетинг
    "IndieDevMarket", "IndieDevFeedback", "PlayMyGame", "ScreenshotSaturday",
    # Технические и экспериментальные
    "GamePhysics", "GameAI", "ProceduralGeneration", "TechArt",
    # Продакшн и релизы
    "DevBlogs", "GameLaunch", "GameUpdates", "IndieDevShowcase",
    # Обсуждения и мета
    "GameIndustry", "GameDevHumor", "LearnGameDev",
]

REDDIT_STEAM_URL_RE = re.compile(r"https?://store\.steampowered\.com/app/(\d+)", re.IGNORECASE)
DEFAULT_POSTS_LIMIT = 20
# ---------------------------------------------------------------------------------------------------------------------
# Orchestrator
ORCH_FETCH_GAME_CONCURRENCY = 10
ORCH_FETCH_META_CONCURRENCY = 2
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
GAME_RANKER_RECENCY_DELTA_DAYS = 180
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

# ----------------------------------------------------------------------
# NEWS RANKER CONFIG
# ----------------------------------------------------------------------

# --- Общие лимиты ---
MIN_NEWS_CONTENT_LENGTH = 300

# --- Источники ---
SOURCE_WEIGHT_EXTERNAL = 1.0
SOURCE_WEIGHT_INTERNAL = 0.75
SOURCE_WEIGHT_COMMUNITY = 0.85

# --- Медиа бонус ---
MEDIA_BONUS = 0.1

# --- Инфоценность ---
SHORT_TEXT_THRESHOLD = 600
INFO_VALUE_GAME_QUALITY_THRESHOLD = 0.4
GAME_QUALITY_REDUCTION_FACTOR = 0.5

# ----------------------------------------------------------------------
# 🧩 Технические апдейты / changelog-и
# ----------------------------------------------------------------------

# Минимальное количество маркеров списков ([list], [*], <li>) для триггера
TECH_LIST_TOKEN_THRESHOLD = 2

# Доля строк, которые выглядят как пункты списка ("-", "*", короткие <10 слов)
TECH_LIST_LINE_RATIO = 0.25

# Комбинированная плотность (чем больше, тем вероятнее changelog)
TECH_LIST_DENSITY_THRESHOLD = 1.3

# Коэффициент ослабления контентного веса для changelog-постов
TECHNICAL_POST_MULTIPLIER = 0.35  # было бы 1.0 — оставляем 35% от исходного

# Дополнительное ослабление влияния рейтинга игры
GAME_QUALITY_TECH_MULTIPLIER = 0.5

# ----------------------------------------------------------------------
# 🔑 Ключевые слова
# ----------------------------------------------------------------------

HIGH_VALUE_KEYWORDS = [
    "release", "launch", "announced", "expansion", "major update",
    "roadmap", "reveal", "coming soon", "out now", "available now",
    "trailer", "gameplay", "feature", "early access", "demo available",
    "release date", "dlc", "content update", "chapter", "season"
]

MEDIUM_VALUE_KEYWORDS = [
    "update", "patch", "balance", "improvement", "development update",
    "performance", "stability", "refactor", "upgrade", "enhancement"
]

LOW_VALUE_KEYWORDS = [
    "bugfix", "hotfix", "minor", "small update", "tweak", "fixes",
    "small changes", "balance tweaks", "patch notes", "adjustments"
]

DEVLOG_KEYWORDS = ["devlog", "patch notes", "bug fix"]

# ---------------------------------------------------------------------------------------------------------------------
# Reddit Ranker
# ==========================================================
# ⚙️ Основные веса для итогового Reddit-рейтинга
# ==========================================================

REDDIT_WEIGHT_FRESHNESS = 0.25          # свежесть поста
REDDIT_WEIGHT_SOURCE = 0.15             # качество сабреддита / источника
REDDIT_WEIGHT_ENGAGEMENT = 0.35         # вовлеченность (апвоуты, комменты, награды)
REDDIT_WEIGHT_CONTENT_RICHNESS = 0.15   # информативность и насыщенность контента
REDDIT_WEIGHT_DEV_SIGNAL = 0.05         # наличие признаков developer-origin поста
REDDIT_WEIGHT_GAME_QUALITY = 0.05       # качество игры, к которой относится пост

# ==========================================================
# 📅 Время и свежесть
# ==========================================================

REDDIT_MAX_POST_AGE_DAYS = 14           # посты старше 14 дней почти не учитываются
REDDIT_RECENCY_BOOST_MAX = 1.3          # максимум бонуса за новизну игры
REDDIT_RECENCY_BOOST_DECAY_DAYS = 7     # за сколько дней бонус спадает

# ==========================================================
# 🔼 Вовлеченность: апвоуты, комменты, награды и медиа
# ==========================================================

REDDIT_UPVOTE_WEIGHT = 1.0              # базовый вес апвоутов
REDDIT_DOWNVOTE_WEIGHT = -0.5           # штраф за дизлайки
REDDIT_COMMENT_WEIGHT = 1.5             # вес комментариев
REDDIT_AWARD_WEIGHT = 10.0              # вес за каждую Reddit-награду
REDDIT_CROSSPOST_WEIGHT = 2.0           # вес за кросспосты (вирусность)
REDDIT_MEDIA_WEIGHT = 15.0              # бонус за наличие изображения или видео

# ==========================================================
# 🧠 Контент и информативность
# ==========================================================

REDDIT_MAX_CONTENT_LENGTH = 3000        # нормализация длины текста
REDDIT_MIN_CONTENT_LENGTH = 150         # минимальная длина для нормального скоринга
REDDIT_MEDIA_BONUS = 0.15               # добавка к content_richness при наличии медиа
REDDIT_MEDIA_INFO_BONUS = 0.10          # добавка к info_value за медиа
REDDIT_TECHNICAL_POST_MULTIPLIER = 1.2  # бонус для тех. контента (patch notes и т.п.)
REDDIT_LOW_VALUE_MULTIPLIER = 0.6       # штраф для "мусорных" постов
REDDIT_GAME_QUALITY_REDUCTION_FACTOR = 0.8  # снижение влияния game_quality при слабом info_value
REDDIT_GAME_QUALITY_TECH_MULTIPLIER = 1.1   # усиление game_quality при техничных постах
REDDIT_INFO_VALUE_GAME_QUALITY_THRESHOLD = 0.4  # порог низкого инфо-контента

# ==========================================================
# 🧩 Subreddit / источник
# ==========================================================

REDDIT_SUBREDDIT_HIGH_WEIGHT = 1.0      # известные dev-сабреддиты
REDDIT_SUBREDDIT_DEFAULT_WEIGHT = 0.7   # обычные сабреддиты

# ==========================================================
# 🧾 Детекция changelog / технических постов
# ==========================================================

REDDIT_TECH_LIST_TOKEN_THRESHOLD = 3
REDDIT_TECH_LIST_LINE_RATIO = 0.25
REDDIT_TECH_LIST_DENSITY_THRESHOLD = 0.5

# ==========================================================
# 🧠 Ключевые слова (поиск смысла и типа контента)
# ==========================================================

REDDIT_DEV_FLAIR_KEYWORDS = [
    "dev", "developer", "progress", "update", "devlog", "patch", "release", "prototype"
]

REDDIT_DEVLOG_KEYWORDS = [
    "devlog", "development", "update", "patch", "progress", "prototype", "build", "changelog",
    "release notes", "new feature", "mechanic", "alpha", "beta", "milestone"
]

REDDIT_HIGH_VALUE_KEYWORDS = [
    "update", "progress", "feature", "release", "demo", "mechanic", "new level", "alpha", "beta",
    "devlog", "gameplay", "build", "patch notes", "visual overhaul"
]

REDDIT_MEDIUM_VALUE_KEYWORDS = [
    "concept", "design", "story", "balance", "performance", "optimization", "feedback"
]

REDDIT_LOW_VALUE_KEYWORDS = [
    "meme", "rant", "help", "question", "giveaway", "promotion"
]

REDDIT_TECH_KEYWORDS = [
    "bug", "fix", "error", "issue", "crash", "patch", "update", "changelog", "build", "version"
]

REDDIT_HIGH_QUALITY_SUBREDDITS = [
    "gamedev", "indiedev", "gamedevelopment", "godot", "unity3d", "unrealengine", "indiegaming", "indiedevfeedback"
]

REDDIT_HIGH_VALUE_DOMAINS = ["store.steampowered.com", "itch.io", "github.com", "rawg.io", "self.gamedev"]

# ==========================================================
# 🔒 Универсальные границы
# ==========================================================

REDDIT_CLAMP_MIN = 0.0
REDDIT_CLAMP_MAX = 1.0

# ---------------------------------------------------------------------------------------------------------------------
# News filter
NEWS_FILTER_GAME_RELEASE_DATE_DELTA_DAYS = 180
NEWS_FILTER_GAME_RATING_MIN = 0.4
NEWS_FILTER_LOW_VALUE_KEYWORDS = [
    "hotfix", "update", "patch", "version", "dev log", "minor changes",
    "bugfix", "roadmap", "announcement", "delay", "sale", "stream", "podcast"
]

NEWS_FILTER_IMPORTANT_KEYWORDS = [
    "release", "launch", "trailer", "new gameplay", "feature",
    "partnership", "publisher", "collaboration", "major update"
]
NEWS_FILTER_TIME_WINDOW_HOURS = 96
NEWS_FILTER_SIMILARITY_THRESHOLD = 0.75
NEWS_FILTER_DUPLICATION_THRESHOLD = 0.92
# ---------------------------------------------------------------------------------------------------------------------
# GameFilter tuning
PRICE_CAP_RELAX_SCORE_DELTA = 0.15  # allow higher price if score exceeds threshold by this delta
PRICE_CAP_STRICT_FACTOR = 0.8       # strict cap factor when score is near threshold
IGDB_FLOOR_RELAX_DELTA = 0.2        # relax IGDB floors if score exceeds threshold by this delta

# Discount filter
LOW_PRICE_THRESHOLD = 10.0        # игры дешевле $10
MID_PRICE_THRESHOLD = 30.0        # игры дешевле $30
HIGH_PRICE_THRESHOLD = 60.0       # игры дешевле $60

LOW_PRICE_DROP_PERCENT = 20.0     # требуемая скидка для дешёвых игр
MID_PRICE_DROP_PERCENT = 15.0     # требуемая скидка для средних игр
HIGH_PRICE_DROP_PERCENT = 10.0    # требуемая скидка для дорогих игр
PREMIUM_PRICE_DROP_PERCENT = 5.0  # требуемая скидка для премиум-игр

DISCOUNT_FILTER_DAYS_LIMIT = 10
DISCOUNT_PUBLICATION_DAYS_LIMIT = 30
DISCOUNT_FILTER_GAME_RELEASE_DATE_DELTA_DAYS = 180
DISCOUNT_FILTER_GAME_RATING_MIN = 0.4
# ---------------------------------------------------------------------------------------------------------------------
# Reddit Post filter
REDDIT_FILTER_BAD_FLAIRS = [
    "question", "hiring", "looking for", "help", "feedback request",
    "tutorial", "showcase", "free", "promo", "giveaway"
]

REDDIT_FILTER_MIN_CONTENT_LENGTH = 80          # минимальная длина текста поста
REDDIT_FILTER_MIN_RANK_SCORE = 0.7             # минимальный рейтинг для публикации
REDDIT_FILTER_SIMILARITY_THRESHOLD = 0.65      # минимальная семантическая близость к игре
REDDIT_FILTER_TIME_WINDOW_HOURS = 96
REDDIT_FILTER_GAME_RELEASE_DATE_DELTA_DAYS = 180
REDDIT_FILTER_GAME_RATING_MIN = 0.4
# ---------------------------------------------------------------------------------------------------------------------
# Publication
DEFAULT_DAILY_POSTS = 6
TIME_WINDOWS = {
    "morning": (8, 12),  # 8:00 - 12:00
    "day": (12, 18),  # 12:00 - 18:00
    "evening": (18, 22),  # 18:00 - 22:00
}

# Базовые приоритеты по времени суток
TIME_PRIORITIES = {
    "morning": {"news": 0.4, "reddit_posts": 0.2, "games": 0.25, "discounts": 0.15},
    "day": {"news": 0.2, "games": 0.2, "discounts": 0.2, "reddit_posts": 0.4},
    "evening": {"news": 0.1, "games": 0.4, "discounts": 0.4, "reddit_posts": 0.1},
}