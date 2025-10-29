import re
from datetime import datetime
from src.models import RankedGameModel
from src.models.game import SteamNewsItem
from src.utils.common import clamp, clean_html
from src.config import constants as C
# ---------------------------------------------------------------------------------------------------------------------


class NewsRanker:
    def __init__(self, game_rank_lookup=None):
        """
        :param game_rank_lookup: callable(game_id) -> last_score
        """
        self.game_rank_lookup = game_rank_lookup or (lambda gid: 0.0)

    def _length_penalty(self, text: str) -> float:
        """Штрафует короткие тексты"""
        min_len = C.MIN_NEWS_CONTENT_LENGTH
        if len(text) < min_len:
            return len(text) / min_len
        return 1.0

    # -------------------------------------------------------------------------
    # ---------------------  TECHNICAL UPDATE DETECTION  -----------------------
    # -------------------------------------------------------------------------

    def _is_technical_update(self, raw_html: str, cleaned_text: str) -> bool:
        """
        Heuristic: returns True if the news is primarily a technical changelog/hotfix list.
        Signals:
          - many list tokens ([list], [*], <li>, lines starting with '-', '*', '•')
          - short descriptive prose relative to list items
          - presence of typical low-value keywords like 'bugfix', 'hotfix', 'patch notes'
        """
        if not cleaned_text:
            return True

        lower_raw = (raw_html or "").lower()
        lower_text = cleaned_text.lower()

        # token counts
        list_token_count = 0
        list_token_count += lower_raw.count("[list]")
        list_token_count += lower_raw.count("[*]")
        list_token_count += lower_raw.count("<li>")
        # markdown-style bullets
        bullet_lines = re.findall(r"(?m)^[\s]*[-\*\u2022]\s+", raw_html)
        list_token_count += len(bullet_lines)

        # number of lines that look like list entries when cleaned
        lines = [ln.strip() for ln in cleaned_text.splitlines() if ln.strip()]
        list_like_lines = sum(1 for ln in lines if re.match(r"^(-|\*|•|\d+\.)\s+", ln) or len(ln.split()) < 10)

        # ratio checks
        total_words = len(cleaned_text.split())
        list_density = 0.0
        if total_words > 0:
            list_density = (list_token_count * 5 + list_like_lines) / (total_words / 10 + 1)  # heuristic scale

        # low-value keyword presence
        has_low_kw = any(kw in lower_text for kw in C.LOW_VALUE_KEYWORDS)

        # Decide: if many list tokens or list-like lines and also low-value keywords or short prose -> technical
        # thresholds are parameterized via constants if present

        fraction_list_lines = (list_like_lines / len(lines)) if lines else 0.0

        is_technical = (
            list_token_count >= C.TECH_LIST_TOKEN_THRESHOLD
            or fraction_list_lines >= C.TECH_LIST_LINE_RATIO
            or list_density >= C.TECH_LIST_DENSITY_THRESHOLD
        ) and has_low_kw

        return bool(is_technical)

    # -------------------------------------------------------------------------
    # -------------------------   SCORING LOGIC   ------------------------------
    # -------------------------------------------------------------------------

    def _info_value_score(self, text: str) -> float:
        """
        Оценивает информационную значимость текста.
        Новая версия: динамическое взвешивание по уровню важности ключевых слов.
        """
        if not text:
            return 0.0

        lower = text.lower()

        score = 0.5

        # Усиление по ключевым словам
        for kw in C.HIGH_VALUE_KEYWORDS:
            if kw in lower:
                score += 0.25
        for kw in C.MEDIUM_VALUE_KEYWORDS:
            if kw in lower:
                score += 0.05
        for kw in C.LOW_VALUE_KEYWORDS:
            if kw in lower:
                score -= 0.25

        # Дополнительное понижение если текст явно про фиксы и короткий
        if any(kw in lower for kw in C.LOW_VALUE_KEYWORDS) and len(text) < C.SHORT_TEXT_THRESHOLD:
            score -= 0.3

        # Понижение для слов вроде "dev log", "patch notes"
        if any(kw in lower for kw in C.DEVLOG_KEYWORDS):
            score -= 0.2

        return clamp(score, 0.0, 1.0)

    # -------------------------------------------------------------------------
    # -------------------------   MAIN METHOD   --------------------------------
    # -------------------------------------------------------------------------

    def evaluate(self, game: RankedGameModel, news: SteamNewsItem) -> float:
        now = datetime.now()

        # 1️⃣ Freshness
        age_days = (now - news.date).days if news.date else 9999
        freshness = clamp(1.0 - age_days / C.MAX_NEWS_AGE_DAYS, 0.0, 1.0)

        # 2️⃣ Source quality
        source_weight = {
            0: C.SOURCE_WEIGHT_EXTERNAL,
            1: C.SOURCE_WEIGHT_INTERNAL,
            2: C.SOURCE_WEIGHT_COMMUNITY,
        }.get(news.feed_type, 0.5)

        # 3️⃣ Content richness
        raw_html = news.contents or ""
        clean_text = clean_html(raw_html)
        content_len = len(clean_text)
        richness = clamp(content_len / C.MAX_CONTENT_LENGTH, 0.0, 1.0)

        # бонус за медиа (поиск raw_html для простоты)
        if "<img" in raw_html or "<video" in raw_html:
            richness = min(1.0, richness + C.MEDIA_BONUS)

        # Информационная ценность
        info_value = self._info_value_score(clean_text)
        length_factor = self._length_penalty(clean_text)
        content_score = richness * info_value * length_factor

        # 4️⃣ Detect technical / changelog posts and reduce their weight
        is_technical = self._is_technical_update(raw_html, clean_text)
        if is_technical:
            content_score *= C.TECHNICAL_POST_MULTIPLIER

        # 5️⃣ Game quality
        game_quality = clamp(game.last_score or self.game_rank_lookup(game.id), 0.0, 1.0)

        # Если новость малозначимая, влияние качества игры снижается
        if info_value < C.INFO_VALUE_GAME_QUALITY_THRESHOLD:
            game_quality *= C.GAME_QUALITY_REDUCTION_FACTOR

        # Also reduce game quality influence further if technical
        if is_technical:
            game_quality *= C.GAME_QUALITY_TECH_MULTIPLIER

        # 6️⃣ Recency boost
        recency_boost = 1.0
        if game.release_date:
            game_age_days = (now - game.release_date).days
            if game_age_days < C.RECENCY_BOOST_DECAY_DAYS:
                recency_boost = 1.0 + (C.RECENCY_BOOST_MAX - 1.0) * (
                        1 - game_age_days / C.RECENCY_BOOST_DECAY_DAYS
                )
                recency_boost = clamp(recency_boost, 1.0, C.RECENCY_BOOST_MAX)

        # 7️⃣ Итоговый скоринг
        raw_score = (
            C.WEIGHT_FRESHNESS * freshness
            + C.WEIGHT_SOURCE * source_weight
            + C.WEIGHT_CONTENT_RICHNESS * content_score
            + C.WEIGHT_GAME_QUALITY * game_quality
        )

        final_score = clamp(raw_score * recency_boost, 0.0, 1.0)
        return float(final_score)
