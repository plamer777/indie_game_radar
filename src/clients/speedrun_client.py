import httpx
from typing import Optional, List, Dict, Any, Literal
from src.config import constants as C
from src.utils.logging import get_logger
# ---------------------------------------------------------------------------------------------------------------------


class SpeedrunClient:
    """Async client for interacting with the Speedrun.com API using httpx."""

    def __init__(self, base_url: str = C.BASE_SPEEDRUN_URL) -> None:
        """The constructor method for SpeedrunClient class.
        :param base_url: a string representing the base url of the speedrun.com api
        """
        self._log = get_logger().bind(client="speedrun")
        self.client = httpx.AsyncClient(base_url=base_url, timeout=C.SPEEDRUN_CLIENT_TIMEOUT)

    async def __aenter__(self):
        """Async context manager support (async with)."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close the HTTP client when exiting the context."""
        await self.client.aclose()

    async def _fetch(self, endpoint: str, params: dict | None = None) -> Optional[Dict[str, Any]]:
        """Internal method for making requests and handling errors."""
        try:
            # Async GET request
            response = await self.client.get(endpoint, params=params or None)
            response.raise_for_status()  # Raises an exception for 4xx/5xx HTTP errors

            # Speedrun.com API always returns JSON
            return response.json()

        except httpx.HTTPStatusError as e:
            # Handle API-specific errors (e.g. not found - 404)
            self._log.error(f"❌ Ошибка HTTP при запросе к {endpoint}: {e}")

        except httpx.RequestError as e:
            # Handle network or timeout errors
            self._log.error(f"❌ Ошибка соединения при запросе к {endpoint}: {e}")

        except Exception as e:
            self._log.error(f'Error while making request: {e}')

        return None

    async def search_game_id(self, name: str) -> Optional[str]:
        """Find a game ID by its name."""
        # Search endpoint: /games?name={name}
        try:
            data = await self._fetch(f"games?name={name}")

            if data and data['data']:
                # Return the ID of the first matched game
                return data['data'][0]['id']
        except Exception as e:
            self._log.error(f'Error while fetching game id: {e}')

        return None

    async def get_player_info(self, player_id: str) -> Optional[Dict[str, Any]]:
        """The method serves to retrieve a player info by provided id
        :param player_id: a string representing the id of player
        """
        data = await self._fetch(f"users/{player_id}")
        return data.get('data', []) if data else data

    async def get_game_info(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Get basic game data (names, year, developer)."""
        # Endpoint: /games/{id}
        data = await self._fetch(f"games/{game_id}")
        return data.get('data', {}) if data else data

    async def get_category(self, category_id: str) -> Optional[Dict[str, Any]]:
        """The method serves to retrieve a single category by provided id"""
        data = await self._fetch(f"categories/{category_id}")
        if data:
            return data.get('data', {})
        return None

    async def get_world_records(
        self, game_id: str, top: int = 5, scope: Literal['full-game', 'level', 'all'] = 'all',
        miscellaneous: bool = True, skip_empty: bool = True
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get world records for a game (top 5 categories by default).

        Note: the API returns records for all categories.
        The 'top' parameter in the speedrun.com API limits the number of ranks per category,
        not the number of categories themselves, but we keep it simple here.
        """
        # Endpoint: /games/{id}/records
        # The 'miscellaneous=yes' parameter fetches all categories
        endpoint = f"games/{game_id}/records"
        params = {'top': top, 'scope': scope, 'miscellaneous': miscellaneous, 'skip-empty': skip_empty}
        data = await self._fetch(endpoint, params=params)

        result = data.get('data', []) or []

        return result[:top]
