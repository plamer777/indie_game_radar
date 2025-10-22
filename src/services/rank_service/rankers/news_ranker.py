import html
import re
from datetime import datetime
from bs4 import BeautifulSoup
from src.models.game import GameModel, SteamNewsItem
from src.utils.common import clamp
from src.config import constants as C
# ---------------------------------------------------------------------------------------------------------------------

class NewsRanker:

    def __init__(self, game_rank_lookup=None):
        """
        :param game_rank_lookup: callable(game_id) -> last_score (если нужно подмешивать качество игры)
        """
        self.game_rank_lookup = game_rank_lookup or (lambda gid: 0.0)

    def _info_value_score(self, text: str) -> float:
        """Простая эвристика — оценивает информационную значимость текста."""
        if not text:
            return 0.0

        lower = text.lower()
        high_value_keywords = [
            "release", "launch", "announced", "expansion",
            "update 1.", "major patch", "roadmap", "partnership",
            "reveal", "coming soon", "out now",
            "trailer", "new gameplay", "feature",
            "partnership", "publisher", "collaboration", "major update", 'early access',
            "available now", 'out now', 'now available', 'release date', 'demo available', 'demo release'
        ]
        low_value_keywords = [
            "hotfix", "update", "patch", "version", "dev log", "stream", "podcast",
            "minor changes", "bugfix", "roadmap", "milestone", "announcement",
            "delay", "sale", "development", "improvements"
        ]

        score = 0.5
        for kw in high_value_keywords:
            if kw in lower:
                score += 0.15
        for kw in low_value_keywords:
            if kw in lower:
                score -= 0.15

        return clamp(score, 0.0, 1.0)

    def _length_penalty(self, text: str) -> float:
        """Штрафует за слишком короткие тексты."""
        min_len = getattr(C, "MIN_NEWS_CONTENT_LENGTH", 300)
        if len(text) < min_len:
            return len(text) / min_len
        return 1.0

    def _clean_html(self, html_text: str) -> str:
        """Удаляет HTML-теги, ссылки и мусор перед анализом."""
        if not html_text:
            return ""
        soup = BeautifulSoup(html_text, "html.parser")
        for tag in soup.find_all(["a", "script", "style"]):
            tag.decompose()
        text = soup.get_text(separator=" ")
        text = html.unescape(text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def evaluate(self, game: GameModel, news: SteamNewsItem) -> float:
        now = datetime.now()

        # ---- 1. Freshness ----
        age_days = (now - news.date).days if news.date else 9999
        freshness = clamp(1.0 - age_days / C.MAX_NEWS_AGE_DAYS, 0.0, 1.0)

        # ---- 2. Source quality ----
        # 0 = external, 1 = internal (Steam), 2 = community
        source_weight = {
            0: 1.0,   # внешние медиа: PCGamesN, GamingOnLinux и т.д.
            1: 0.7,   # официальные посты
            2: 0.8,   # коммьюнити / dev-блоги
        }.get(getattr(news, "feed_type", 0), 0.5)

        # ---- 3. Content richness + новая логика ----
        raw_html = news.contents or ""
        clean_text = self._clean_html(raw_html)
        content_len = len(clean_text)
        richness = clamp(content_len / C.MAX_CONTENT_LENGTH, 0.0, 1.0)

        if "<img" in raw_html or "<video" in raw_html:
            richness = min(1.0, richness + 0.1)

        # новая часть:
        info_value = self._info_value_score(clean_text)
        length_factor = self._length_penalty(clean_text)
        content_score = richness * info_value * length_factor

        # ---- 4. Game quality ----
        game_quality = clamp(game.last_score or self.game_rank_lookup(game.id), 0.0, 1.0)

        # ---- 5. Recency boost ----
        recency_boost = 1.0
        if game.release_date:
            age_days = (now - game.release_date).days
            if age_days < C.RECENCY_BOOST_DECAY_DAYS:
                recency_boost = 1.0 + (C.RECENCY_BOOST_MAX - 1.0) * (
                        1 - age_days / C.RECENCY_BOOST_DECAY_DAYS
                )
                recency_boost = clamp(recency_boost, 1.0, C.RECENCY_BOOST_MAX)

        # ---- 6. Aggregation ----
        raw_score = (
                C.WEIGHT_FRESHNESS * freshness
                + C.WEIGHT_SOURCE * source_weight
                + C.WEIGHT_CONTENT_RICHNESS * content_score
                + C.WEIGHT_GAME_QUALITY * game_quality
        )

        final_score = clamp(raw_score * recency_boost, 0.0, 1.0)
        return float(final_score)
