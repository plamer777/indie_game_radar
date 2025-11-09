import re
from typing import Literal
from openai import AsyncOpenAI
from src.db.repositories import CheckedEntityRepository
from src.models import RankedGameModel, CheckedEntity
from src.schemas import CheckedEntitySchema
from src.utils.common import parse_json
# ---------------------------------------------------------------------------------------------------------------------


class BaseFilter:
    def __init__(
        self, open_ai_client: AsyncOpenAI | None = None, gpt_model: str | None = None,
        checked_entity_repo: CheckedEntityRepository | None = None
    ):
        self._open_ai_client = open_ai_client
        self._gpt_model = gpt_model
        self._checked_entity_repo = checked_entity_repo

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
        price = game.price.final if game.price else 0

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
            parsed = parse_json(raw)
            if parsed:
                return parsed

        return {"suitable": False, "confidence": 0.0, "reason": "No JSON found"}


    async def _get_checked(
        self, entity_id: str | int, entity_type: Literal['news', 'game', 'reddit']
    ) -> CheckedEntity | None:
        """The method returns the result of the filter for the entity if it was checked before

        Args:
            entity_id: The ID of the entity
            entity_type: The type of the entity

        Returns:
            CheckedEntity | None: The result of the filter for the entity if it was checked before
        """
        checked = await self._checked_entity_repo.get_one({'entity_id': entity_id, 'type': entity_type})
        return checked

    async def _add_to_checked(
        self, entity_id: str | int, entity_type: Literal['news', 'game', 'reddit'], result: dict
    ) -> None:
        """The method adds the result of the filter for the entity to the checked entities repository
        Args:
            entity_id: The ID of the entity
            entity_type: The type of the entity
            result: The result of the filter for the entity
        """
        await self._checked_entity_repo.add_new(
            CheckedEntitySchema(entity_id=entity_id, type=entity_type, **result).model_dump()
        )
