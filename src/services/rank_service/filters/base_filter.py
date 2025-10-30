import json
import re
from openai import OpenAI
from src.models import RankedGameModel
# ---------------------------------------------------------------------------------------------------------------------


class BaseFilter:
    def __init__(self, open_ai_client: OpenAI | None = None, gpt_model: str | None = None):
        self._open_ai_client = open_ai_client
        self._gpt_model = gpt_model

    BIG_PUBLISHERS = {
        "ubisoft", "ea", "electronic arts", "activision", "square enix",
        "capcom", "bandai namco", "bethesda", "sony", "microsoft", "sega",
        "2k", "take-two", "nintendo", "devolver digital", "tinybuild"
    }

    def _is_indie_game(self, game: RankedGameModel) -> bool:
        name = game.name.lower()
        description = game.detailed_description.lower()
        tags = " ".join(game.tags or []).lower()
        genres = [g.lower() for g in game.genres or []]
        developers = [developer.lower() for developer in game.developers or []]
        publishers = [publisher.lower() for publisher in game.publishers or []]
        price = game.price or 0

        # 1. Прямое указание жанра
        if "indie" in genres or "indie" in tags or "indie" in description:
            indie_score = 2
        else:
            indie_score = 0

        # 2. Независимая студия
        if (
            developers == publishers or not publishers or
                all(publisher not in self.BIG_PUBLISHERS for publisher in publishers)
        ):
            indie_score += 1

        # 3. Не часть франшизы
        if not re.search(r"\b(remaster|ii|iii|iv|collection|deluxe|edition)\b", name):
            indie_score += 1

        # 4. Масштаб
        if price <= 25:
            indie_score += 1

        # 5. Визуальные признаки (по тегам)
        if any(keyword in tags for keyword in ("pixel", "lowpoly", "hand-drawn", "retro")):
            indie_score += 1

        # Итог: >=3 из 5 признаков — вероятная инди-игра
        return indie_score >= 3

    async def _filter_by_content(self, filter_prompt: str) -> dict:
        if not self._open_ai_client or not self._gpt_model:
            raise ValueError("OpenAI client and GPT model must be provided")

        for _ in range(3):
            response = await self._open_ai_client.chat.completions.create(
                model=self._gpt_model,
                messages=[{"role": "user", "content": filter_prompt}],
                temperature=0.2,
                max_tokens=200,
            )

            raw = response.choices[0].message.content.strip()
            # Извлекаем JSON даже если модель добавила текст вокруг
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if not match:
                continue

            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return {"suitable": False, "confidence": 0.0, "reason": "Invalid JSON"}

        return {"suitable": False, "confidence": 0.0, "reason": "No JSON found"}
