from openai import AsyncOpenAI
from src.config import constants as C
from src.utils.common import parse_json
# ---------------------------------------------------------------------------------------------------------------------


class EditorialRefiner:
    """
    Uses GPT to rewrite and polish post text in a professional journalistic style
    suitable for the Indie Game Radar Telegram channel.
    """

    def __init__(self, open_ai_client: AsyncOpenAI, model: str = C.EDITORIAL_REFINER_MODEL):
        self._client = open_ai_client
        self._model = model
        self._prompt_mapper = {
            "news": C.EDITORIAL_REFINER_STEAM_NEWS_PROMPT,
            "reddit_posts_game_related": C.EDITORIAL_REFINER_REDDIT_GAME_POST_PROMPT,
            "reddit_posts_game_dev_story": C.EDITORIAL_REFINER_GAMEDEV_DISCUSSION_PROMPT,
        }

    async def refine(self, title: str, text: str, post_type: str) -> dict:
        """
        Returns rewritten {'title': str, 'body': str}
        """

        prompt = self._build_prompt(title, text, post_type)
        for _ in range(3):
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": "You are a professional game journalist specializing in indie games."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8
            )

            content = response.choices[0].message.content.strip()
            parsed = parse_json(content)
            if parsed:
                return parsed

        return {'title': title, 'content': text}

    def _build_prompt(self, title: str, text: str, post_type: str) -> str:
        prompt_template = self._prompt_mapper.get(post_type)
        if not prompt_template:
            raise ValueError(f"Unknown post type: {post_type}")

        return prompt_template.format(title=title, content=text)
