from typing import Literal
import markdown
from openai import AsyncOpenAI
from src.config import constants as C
from src.utils.common import parse_json, is_markdown
from src.utils.logging import get_logger
# ---------------------------------------------------------------------------------------------------------------------


class EditorialRefiner:
    """
    Uses GPT to rewrite and polish post text in a professional journalistic style
    suitable for the Indie Game Radar Telegram channel.
    """

    def __init__(self, open_ai_client: AsyncOpenAI, model: str = C.EDITORIAL_REFINER_MODEL) -> None:
        """
        The constructor for the EditorialRefiner class.
        :param open_ai_client: The OpenAI client to use for the API calls
        :param model: The model to use for the API calls
        """
        self._client = open_ai_client
        self._model = model
        self._prompt_mapper = {
            "news": C.EDITORIAL_REFINER_STEAM_NEWS_PROMPT,
            "reddit_posts_game_related": C.EDITORIAL_REFINER_REDDIT_GAME_POST_PROMPT,
            "reddit_posts_game_dev_story": C.EDITORIAL_REFINER_GAMEDEV_DISCUSSION_PROMPT,
            "games": C.EDITORIAL_REFINER_GAME_POST,
            "reviews": C.EDITORIAL_REFINER_REVIEW_PROMPT,
        }
        self._log = get_logger().bind(service="EditorialRefiner")

    async def refine(
        self,
        post_type: Literal["news", "reddit_posts_game_related", "reddit_posts_game_dev_story", "games", "reviews"],
        **kwargs
    ) -> dict:
        """
        The method uses GPT to rewrite and polish post text in a professional journalistic style
        suitable for the Telegram channel.
        :param kwargs: The parameters for the prompt template
        :param post_type: The type of the post
        Returns rewritten {'title': str, 'body': str}
        """
        prompt = self._build_prompt(kwargs, post_type)
        if not prompt:
            return dict(kwargs)

        for _ in range(3):
            try:
                response = await self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a professional game journalist specializing in indie games."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.8
                )

                content = response.choices[0].message.content.strip()


                parsed = parse_json(content)
                if parsed:
                    description = parsed.get('content')
                    if is_markdown(description):
                        parsed['content'] = markdown.markdown(description)
                    return parsed

            except Exception as e:
                self._log.error("refine_failed", error=str(e))

        return dict(kwargs)

    def _build_prompt(self, params: dict, post_type: str) -> str | None:
        """The method builds the prompt template for the given post type
        :param params: The parameters for the prompt template
        :param post_type: The type of the post
        :return: The prompt template for the given post type
        """
        prompt_template = self._prompt_mapper.get(post_type)
        if not prompt_template:
            return None

        return prompt_template.format(**params)
