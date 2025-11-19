import httpx
from typing import Optional, List, Dict, Any, Literal

# Базовый URL для API Speedrun.com
BASE_URL = "https://www.speedrun.com/api/v1"


class SpeedrunClient:
    """Асинхронный клиент для взаимодействия с Speedrun.com API с использованием httpx."""

    def __init__(self):
        # httpx.AsyncClient позволяет переиспользовать соединение для всех запросов
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=10.0)

    async def __aenter__(self):
        """Поддержка асинхронного контекстного менеджера (async with)."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие HTTP-клиента при выходе из контекста."""
        await self.client.aclose()

    async def _fetch(self, endpoint: str, params: dict | None = None) -> Optional[Dict[str, Any]]:
        """Внутренний метод для выполнения запросов и обработки ошибок."""
        try:
            # Асинхронный GET-запрос
            response = await self.client.get(endpoint, params=params or None)
            response.raise_for_status()  # Вызывает исключение для HTTP-ошибок 4xx/5xx

            # API Speedrun.com всегда возвращает JSON
            return response.json()

        except httpx.HTTPStatusError as e:
            # Обработка ошибок, специфичных для API (например, не найдено - 404)
            print(f"❌ Ошибка HTTP при запросе к {endpoint}: {e}")

        except httpx.RequestError as e:
            # Обработка ошибок сети или таймаута
            print(f"❌ Ошибка соединения при запросе к {endpoint}: {e}")

        except Exception as e:
            print(f'Error while making request: {e}')

        return None

    async def search_game_id(self, name: str) -> Optional[str]:
        """Найти ID игры по ее названию."""
        # Эндпоинт для поиска: /games?name={name}
        data = await self._fetch(f"games?name={name}")

        if data and data['data']:
            # Возвращаем ID первой найденной игры
            return data['data'][0]['id']
        return None

    async def get_player_info(self, player_id: str) -> Optional[Dict[str, Any]]:
        """The method serves to retrieve a player info by provided id
        :param player_id: a string representing the id of player
        """
        data = await self._fetch(f"users/{player_id}")
        return data.get('data')

    async def get_game_info(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Получить основные данные об игре (названия, год, разработчик)."""
        # Эндпоинт: /games/{id}
        data = await self._fetch(f"games/{game_id}")
        return data.get('data')

    async def get_categories(self, game_id: str) -> Optional[List[Dict[str, Any]]]:
        """Получить список категорий и подкатегорий (Any%, 100%, Glitchless и т.д.)."""
        # Эндпоинт: /games/{id}/categories
        data = await self._fetch(f"games/{game_id}/categories")
        if data:
            return data['data']
        return None

    async def get_category(self, category_id: str) -> Optional[Dict[str, Any]]:
        """The method serves to retrieve a single category by provided id"""
        data = await self._fetch(f"categories/{category_id}")
        if data:
            return data['data']
        return None

    async def get_world_records(
        self, game_id: str, top: int = 5, scope: Literal['full-game', 'level', 'all'] = 'all',
        miscellaneous: bool = True, skip_empty: bool = True
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Получить мировые рекорды для игры (по умолчанию - top 5 категорий).

        Обратите внимание: API возвращает рекорды для всех категорий.
        Параметр 'top' в API speedrun.com используется для ограничения количества рангов в каждой категории,
        а не числа самих категорий, но в данном примере мы упростим.
        """
        # Эндпоинт: /games/{id}/records
        # Параметр 'miscellaneous=yes' позволяет получить все категории
        endpoint = f"games/{game_id}/records"
        params = {'top': top, 'scope': scope, 'miscellaneous': miscellaneous, 'skip-empty': skip_empty}
        data = await self._fetch(endpoint, params=params)

        result = data.get('data', []) or []

        return result[:top]
