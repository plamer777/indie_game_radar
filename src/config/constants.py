from __future__ import annotations
import re

# ---------------------------------------------------------------------------------------------------------------------
# Base client settings
BASE_CLIENT_MIN_INCREASE_DIFF_SEC = 10
BASE_CLIENT_INCREASE_STEP = 0.1

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
DEFAULT_DUPLICATION_THRESHOLD = 0.9
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
LEADERBOARD_COLLECTION = "leaderboards"
RANKED_GAMES_COLLECTION = "ranked_games"
REDDIT_POSTS_COLLECTION = "reddit_posts"
RANKED_REDDIT_POSTS_COLLECTION = "ranked_reddit_posts"
IGDB_META_COLLECTION = "igdb_meta"
GAME_PUBLICATIONS_COLLECTION = "game_publications"
REVIEW_PUBLICATIONS_COLLECTION = "review_publications"
NEWS_PUBLICATIONS_COLLECTION = "news_publications"
REDDIT_PUBLICATIONS_COLLECTION = "reddit_publications"
CHECKED_ENTITIES_COLLECTION = "checked_entities"
DISCOUNT_PUBLICATIONS_COLLECTION = "discount_publications"
GAME_LEADERBOARD_PUBLICATIONS_COLLECTION = "leaderboard_publications"
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
# Speedrun.com
BASE_SPEEDRUN_URL = "https://www.speedrun.com/api/v1"
SPEEDRUN_CLIENT_TIMEOUT = 10.0
# ---------------------------------------------------------------------------------------------------------------------
# Harvester
SPEEDRUN_GAME_RELEASE_MAX_DELTA_DAYS = 14

# ---------------------------------------------------------------------------------------------------------------------
# Reddit client
GAMEDEV_SUBREDDITS = [
    # Общие по разработке
    "gamedev", "indiedev", "gameDevClassifieds", "IndieGaming", "IndieDev",
    "GameDesign", "GameDevelopment", "Unity3D", "UnrealEngine", "Godot", "SoloDevelopment", "DestroyMyGame",
    "indiegames", "IndieGameDevs", "DevBlogs"
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

GAME_MEME_SUBREDDITS = [
    "gamingmemes",              # общий саб с игровыми мемами
    "gamememes",                # ещё один крупный саб по игровым мемам
    "pcmasterrace",             # мемы, юмор про ПК-геймеров и платформу
    "justgamedevthings",        # мемы/юмор про разработку игр (геймдев) :contentReference[oaicite:0]{index=0}
    "IndieDev",                 # инди-разработка, там иногда мемы появляются :contentReference[oaicite:1]{index=1}
    "gamedevmemes",             # нишевой саб, мемы про разработку (может быть малочисленным)
    "gamingcirclejerk",         # саркастические/ироничные игровые мемы :contentReference[oaicite:2]{index=2}
    "gametheorymemes",          # мемы про гейм/фильм-теорию, можно перекрестно использовать :contentReference[oaicite:3]{index=3}
    "LeagueOfMemes",            # пример сабреддита, посвященный конкретной игровой серии (для разнообразия) :contentReference[oaicite:4]{index=4}
    "ProgrammerHumor",          # разработчики/программирование: контент может пересекаться с геймдевом :contentReference[oaicite:5]{index=5}
]

REDDIT_STEAM_URL_RE = re.compile(r"https?://store\.steampowered\.com/app/(\d+)", re.IGNORECASE)
DEFAULT_GAME_RELATED_POSTS_LIMIT = 20
DEFAULT_GAME_DEV_STORY_POSTS_LIMIT = 1000
DEFAULT_GAME_MEME_POSTS_LIMIT = 100

GAME_MEME_OVERSAMPLE_FACTOR = 10
GAMEDEV_DISCUSSION_QUERIES = [
    # 🎮 Общие обсуждения разработки игр
    "game development",
    "solo dev",
    "indie dev",
    "indie game dev",
    "indie developer",
    "making a game",
    "how to make a game",
    "developing my game",
    "working on my game",
    "building a game",
    "my first game",
    "solo game developer",
    "learning game dev",
    "game dev looks like",

    # 💡 Опыт, истории, фейлы, инсайты
    "my game dev journey",
    "what I learned from making a game",
    "mistakes I made developing a game",
    "things I wish I knew about game dev",
    "lessons from indie development",
    "my first Steam release",
    "postmortem game dev",
    "behind the scenes game dev",
    "indie game story",
    "how I made my first game",
    "success story game dev",
    "failed game project",
    "indie dev experience",
    "worst thing game dev",
    "game solo dev",
    "my first solo dev game",
    "passion for game dev"

    # 🧠 Технические / производственные темы
    "game engine choice",
    "unity vs unreal",
    "game optimization tips",
    "level design lessons",
    "learning Godot",
    "making pixel art game",
    "creating game mechanics",

    # 💰 Маркетинг, релизы, сообщество
    "indie game marketing",
    "promoting my game",
    "launching on Steam",
    "getting wishlists",
    "finding players for my game",
    "getting feedback for my game",
    "Steam launch lessons",
    "indie dev tips",
]
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
REDDIT_DOWNVOTE_WEIGHT = 0.5           # штраф за дизлайки
REDDIT_COMMENT_WEIGHT = 1.5             # вес комментариев
REDDIT_GAME_DEV_STORY_COMMENT_WEIGHT = 2.0            # вес комментариев
REDDIT_AWARD_WEIGHT = 10.0              # вес за каждую Reddit-награду
REDDIT_CROSSPOST_WEIGHT = 2.0           # вес за кросспосты (вирусность)
REDDIT_MEDIA_WEIGHT = 15.0              # бонус за наличие изображения или видео

# ==========================================================
# 🧠 Контент и информативность
# ==========================================================

REDDIT_MAX_CONTENT_LENGTH = 3000        # нормализация длины текста
REDDIT_MIN_CONTENT_LENGTH = 300         # минимальная длина для нормального скоринга
REDDIT_GAME_DEV_STORY_MIN_CONTENT_LENGTH = 1000         # минимальная длина для нормального скоринга
REDDIT_MEDIA_BONUS = 0.15               # добавка к content_richness при наличии медиа
REDDIT_MEDIA_INFO_BONUS = 0.10          # добавка к info_value за медиа
REDDIT_TECHNICAL_POST_MULTIPLIER = 1.2  # бонус для тех. контента (patch notes и т.п.)
REDDIT_LOW_VALUE_MULTIPLIER = 0.6       # штраф для "мусорных" постов
REDDIT_GAME_QUALITY_REDUCTION_FACTOR = 0.8  # снижение влияния game_quality при слабом info_value
REDDIT_GAME_QUALITY_TECH_MULTIPLIER = 1.1   # усиление game_quality при техничных постах
REDDIT_INFO_VALUE_GAME_QUALITY_THRESHOLD = 0.4  # порог низкого инфо-контента

REDDIT_DEV_WEIGHT_FRESHNESS = 0.2
REDDIT_DEV_WEIGHT_SOURCE = 0.2
REDDIT_DEV_WEIGHT_ENGAGEMENT = 0.4
REDDIT_DEV_WEIGHT_STORYTELLING = 0.2

REDDIT_DEV_TECH_PENALTY = 0.6
REDDIT_DEV_PROMO_PENALTY = 0.5

REDDIT_DEV_LENGTH_BASE = 0.7
REDDIT_DEV_LENGTH_SCALE = 0.3
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

REDDIT_GAME_DEV_STORY_PATTERNS = [
    "how i made", "what i learned", "lessons learned", "behind the scenes",
    "making of", "our journey", "postmortem", "we decided to", "we built",
    "my first game", "from idea to", "what went wrong", "our experience",
    "indie dev story", "we learned", "mistakes", "success", "failure"
]

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
# --- Reddit Meme Ranker ---
REDDIT_MEME_RANKER_UPS_WEIGHT = 0.7              # вес апвоутов в общем скоре
REDDIT_MEME_RANKER_COMMENTS_WEIGHT = 0.3         # вес комментариев в общем скоре
REDDIT_MEME_RANKER_ENGAGEMENT_NORM = 10.0        # нормализация логарифмической вовлечённости
REDDIT_MEME_RANKER_HALFLIFE_DAYS = 30.0          # "период полураспада" свежести мема
REDDIT_MEME_RANKER_MIN_DECAY = 0.3               # минимальное значение коэффициента свежести
REDDIT_MEME_RANKER_MAX_UPS = 50000               # верхний предел апвоутов (для лог-нормализации)
REDDIT_MEME_RANKER_MAX_COMMENTS = 2000           # верхний предел комментариев (для лог-нормализации)
# ---------------------------------------------------------------------------------------------------------------------
# Reviews filter
REVIEWS_FILTER_GAME_RELEASE_DATE_DELTA_DAYS = 365
REVIEWS_FILTER_GAME_RATING_MIN = 0.3
# ---------------------------------------------------------------------------------------------------------------------
# Game leaderboards filter
GAME_LEADERBOARD_FILTER_RATING_MIN = 0.3
GAME_LEADERBOARD_FILTER_MAX_AGE_DAYS = 14

# ---------------------------------------------------------------------------------------------------------------------
# News filter
NEWS_FILTER_GAME_RELEASE_DATE_DELTA_DAYS = 180
NEWS_FILTER_DUPLICATION_CHECKING_MAX_AGE_DAYS = 30
NEWS_FILTER_GAME_RATING_MIN = 0.3
NEWS_FILTER_MIN_SCORE = 0.6
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

NEWS_FILTER_GPT_MODEL = 'gpt-4o-mini'
NEWS_FILTER_EMBEDDING_MODEL = 'text-embedding-3-small'

NEWS_FILTER_PROMPT_TEMPLATE = """
You are reviewing a Steam news post to decide if it would be interesting to indie gamers on Telegram.

Focus on:
- audience benefit: something they’d want to read or share;
- novelty, entertainment, or community importance;
- clarity and storytelling quality;
- skip overly technical or repetitive posts.

Return JSON only:
{{
  "suitable": true|false,
  "confidence": 0.0–1.0,
  "reason": "Short reason"
}}

Game: {game_name}
Title: {title}
Text: {text}
"""
# ---------------------------------------------------------------------------------------------------------------------
# GameFilter tuning
PRICE_CAP_RELAX_SCORE_DELTA = 0.15  # allow higher price if score exceeds threshold by this delta
PRICE_CAP_STRICT_FACTOR = 0.8       # strict cap factor when score is near threshold
IGDB_FLOOR_RELAX_DELTA = 0.2        # relax IGDB floors if score exceeds threshold by this delta
GAME_FILTER_RATING_MIN = 0.3
GAME_FILTER_RELEASE_DATE_DELTA_DAYS = 180


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
DISCOUNT_FILTER_GAME_RATING_MIN = 0.3
# ---------------------------------------------------------------------------------------------------------------------
# Reddit Post filter
REDDIT_FILTER_BAD_FLAIRS = [
    "question", "hiring", "looking for", "help", "feedback request",
    "tutorial", "showcase", "free", "promo", "giveaway"
]

REDDIT_FILTER_MIN_CONTENT_LENGTH = 80          # минимальная длина текста поста
REDDIT_FILTER_MIN_RANK_SCORE = 0.5             # минимальный рейтинг для публикации
REDDIT_FILTER_SIMILARITY_THRESHOLD = 0.65      # минимальная семантическая близость к игре
REDDIT_FILTER_TIME_WINDOW_HOURS = 168
REDDIT_FILTER_GAME_RELEASE_DATE_DELTA_DAYS = 180
REDDIT_FILTER_GAME_RATING_MIN = 0.3
REDDIT_FILTER_DUPLICATION_CHECKING_MAX_AGE_DAYS = 30

REDDIT_FILTER_GPT_MODEL = 'gpt-4o-mini'
REDDIT_FILTER_EMBEDDING_MODEL = 'text-embedding-3-small'

REDDIT_FILTER_PROMPT_TEMPLATE = """
You are a professional journalist and content curator specializing in indie video games. 
Analyze the Reddit post below and decide whether it is suitable for publication in a Telegram channel about PC indie games.

Input data:
Game title: {game_name}
Post title: {title}
Post text: {text}

Evaluate:
1. Is the post clearly related to the game?
2. Does it contain something interesting for gamers (opinions, humor, insights, news)?
3. Is it free from spam, ads, or toxicity?
4. Is it appropriate in tone and format for a Telegram audience?

Respond **only** in strict JSON format:
{{
  "suitable": true|false,
  "confidence": 0.0–1.0,
  "reason": "Short explanation"
}}
"""


# ---------------------------------------------------------------------------------------------------------------------
# Reddit meme filter
# constants.py
REDDIT_MEME_FILTER_MAX_AGE_DAYS = 90
REDDIT_MEME_FILTER_MIN_SCORE = 0.6

# ---------------------------------------------------------------------------------------------------------------------
# Reddit Dev Post Filter
REDDIT_DEV_FILTER_TIME_WINDOW_DAYS = 14
REDDIT_DEV_FILTER_MIN_RANK_SCORE = 0.5
REDDIT_DEV_FILTER_MIN_CONTENT_LENGTH = 400
REDDIT_DEV_FILTER_SIMILARITY_THRESHOLD = 0.75
REDDIT_DEV_FILTER_EMBEDDING_MODEL = "text-embedding-3-small"
REDDIT_DEV_FILTER_GPT_MODEL = "gpt-4o-mini"
REDDIT_DEV_FILTER_PROMPT_TEMPLATE = """
You are an assistant helping to select Reddit posts for an indie game discovery channel.

Your goal is to find posts that share interesting developer experiences, 
behind-the-scenes stories, lessons learned, or creative insights about game development.

Reject posts that are:
- Patch notes, release updates, or changelogs
- Hiring or collaboration requests
- Promotions, ads, or Kickstarter campaigns
- Posts focused on a specific product page or announcement

Analyze the following post and respond **only** in strict JSON format:
{{
  "suitable": true|false,
  "confidence": 0.0–1.0,
  "reason": "Short explanation"
}}

=== Post ===
Title: {title}

Text:
{text}
"""
REDDIT_DEV_FILTER_BAD_FLAIRS = ["update", "patch", "bugfix", "hiring", "release", "promo", "kickstarter"]
REDDIT_GAME_DEV_FILTER_RATING_MIN = 0.6
# ---------------------------------------------------------------------------------------------------------------------
# Publication
DEFAULT_DAILY_POSTS = 10
ALLOCATION_START_HOUR = 8
ALLOCATION_END_HOUR = 16
PUBLICATION_SCHEDULER_DELAY = SECONDS_IN_MINUTE * 5
TIME_WINDOWS = {
    "morning": (8, 12),  # 8:00 - 12:00
    "day": (12, 18),  # 12:00 - 18:00
    "evening": (18, 22),  # 18:00 - 22:00
}

# Базовые приоритеты по времени суток
TIME_PRIORITIES = {
    "morning": {
        "news": 0.1, "reddit_posts": 0.35, "games": 0.0, "discounts": 0.15, "reddit_memes": 0.4, "reviews": 0.0,
        "game_leaderboards": 0.0
    },
    "day": {
        "news": 0.2, "games": 0.1, "discounts": 0.1, "reddit_posts": 0.2, "reddit_memes": 0.2, "reviews": 0.1,
        "game_leaderboards": 0.2
    },
    "evening": {
        "news": 0.1, "games": 0.1, "discounts": 0.3, "reddit_posts": 0.3, "reddit_memes": 0.2, "reviews": 0.0,
        "game_leaderboards": 0.2
    },
}

EDITORIAL_REFINER_GAME_POST = """
You are a creative marketing writer for a Telegram gaming channel called Indie Game Radar.
Take the following raw description and turn it into a visually appealing Telegram post.
Make it lively, easy to read, and engaging, while keeping the original tone and key facts.
Add emojis that match the context (🎮, 🔥, 🧭, ⚙️, etc.), and split it into logical sections with clear headers.

The post should look like a formatted Telegram message — compact, readable, and with natural line breaks. Use only
Telegram allowed HTML tags. Text should be formatter **ONLY USING HTML TAGS APPROPRIATE FOR TELEGRAM POSTS**

Input:
Title: "{title}"
Content: "{content}"

Output:
Return your rewritten text **strictly in JSON** format like this:
{{
  "title": "Rewritten catchy title for Telegram post",
  "content": "Rewritten description written in natural human language using Telegram HTML format"
}}
Do not add any explanations, comments, or text outside this JSON.
"""

EDITORIAL_REFINER_STEAM_NEWS_PROMPT = """
You are a professional gaming journalist specializing in indie games. 
You write short, engaging posts for a Telegram channel that shares news about Steam releases and game updates.

Task:
Rewrite the following game news headline and content in your own words. 
Keep the meaning but make it more interesting and conversational, as if you’re telling your audience about this news personally.
Avoid sounding like marketing or PR — sound like a human journalist who actually plays games.

Tone:
Friendly, slightly emotional, confident, and natural for gamers.
Avoid hashtags, emojis, or explicit mentions of Steam.

Input:
Title: "{title}"
Content: "{content}"

Output:
Return your rewritten text **strictly in JSON** format like this:
{{
  "title": "Rewritten catchy title for Telegram post",
  "content": "Short engaging summary (3–5 sentences) written in natural human language."
}}
Do not add any explanations, comments, or text outside this JSON.
"""

EDITORIAL_REFINER_REDDIT_GAME_POST_PROMPT = """
You are an indie game journalist preparing a Telegram post based on a Reddit discussion about a specific game.

Task:
Retell the following Reddit post in your own words as if you are summarizing or reacting to it for your readers.
Keep it concise and engaging — highlight the main point or emotion of the original post.
If the post is personal or opinionated, preserve that tone but make it more readable and cohesive.
Avoid quoting directly or mentioning Reddit.

Tone:
Natural, curious, slightly informal — like a journalist who’s also part of the gaming community.

Input:
Title: "{title}"
Content: "{content}"

Output:
Return the rewritten version strictly in JSON format like this:
{{
  "title": "Improved, catchy title",
  "content": "Medium rewritten summary as if told by a journalist for Telegram readers."
}}
Do not include any explanations or text outside this JSON.
"""

EDITORIAL_REFINER_GAMEDEV_DISCUSSION_PROMPT = """
You are an experienced indie game journalist writing for a Telegram audience of game developers and enthusiasts.

Task:
Rewrite the following post about game development — it could be a personal experience, lesson, or insight.
Retell it in your own words, making it more structured, engaging, and relevant for readers.
Summarize key takeaways or ideas while keeping the human tone of the original.
Avoid technical overload — make it readable and relatable even for non-experts.

Tone:
Professional yet friendly. Sounds like an insightful mini-article or reflection written by a journalist familiar with game dev culture.

Input:
Title: "{title}"
Content: "{content}"

Output:
Return your rewritten result strictly in JSON format like this:
{{
  "title": "Refined, readable title",
  "content": "A summary conveying the essence of the post and key insights for Telegram readers."
}}
Do not add explanations, extra words, or anything outside the JSON.
"""

EDITORIAL_REFINER_REVIEW_PROMPT = """
You are an analyst who summarizes player sentiment from community reviews.
INPUT:
- Game title: "{game}"
- Selected reviews: {reviews} # array of objects [{{"author": "...", "text": "...", "language": "english", "votes_up": 41, "votes_funny": 0, "timestamp": 1762791739}}, ... ]

TASK:
Using only the provided selected reviews and metadata, produce a concise, honest, and balanced summary of player sentiment about the game. Output MUST be valid JSON **only** (no prose outside JSON). The JSON must follow this exact schema:

{{
  "title": "<short headline (max 60 chars)>",
  "summary": "<short paragraph 4-5 sentences - community consensus>",
  "sentiment_score": <float 0.0-1.0 indicating positivity (0 negative - 1 positive)>,
  "strengths": ["short bullet points (2-6) - what players praise"],
  "weaknesses": ["short bullet points (2-6) - what players complain about"],
  "common_requests": ["features or fixes players ask for (1-5)"],
  "notable_quotes": ["<short quote up to 200 chars>"],
  "surprises": ["unexpected observations from reviews (optional)"],
  "confidence": "<low|medium|high>  - how confident are you given #reviews>"
}}

RULES:
- Do not invent facts beyond the given reviews and metadata.
- Use reviews to justify strengths/weaknesses.
- sentiment_score should reflect overall tilt from reviews (approximate).
- 'title' should be catchy and suitable for a Telegram post heading.
- 'notable_quotes' should contain up to 3 short quotes (prefer higher votes_up).
- 'confidence' = "high" if total_reviews >= 200, "medium" if >= 30, else "low".
- Keep all text English.
- Output must be valid JSON with the fields above.

END.
"""
# ---------------------------------------------------------------------------------------------------------------------
# Editorial Refiner
EDITORIAL_REFINER_MODEL = "gpt-4o-mini"

# Embedding mixin settings
DEFAULT_EMBEDDING_MODEL = 'text-embedding-3-small'

TG_ALLOWED_TAGS = {
    "b", "i", "u", "s",
    "a", "code", "pre",
    "span", "tg-spoiler",
}

# Теги-синонимы, которые Telegram НЕ поддерживает напрямую,
# но они полностью эквивалентны разрешённым.
TG_TAG_MAPPING = {
    "strong": "b",
    "em": "i",
    "ins": "u",
    "strike": "s",
    "del": "s",
}

# Разрешённые атрибуты
TG_ALLOWED_ATTRS = {
    "a": {"href"},
    "span": {"class"},  # только class="tg-spoiler"
    "code": {"class"},  # class="language-xxx"
    "pre": {"language"},  # используется telegram
    "tg-spoiler": set(),
}
