import logging
import time
import httpx
from src.config import constants as C
# ---------------------------------------------------------------------------------------------------------------------


class BaseAPIClient:
    """The BaseAPIManager class to be inherited by other API managers"""
    def __init__(self) -> None:
        """Initialization of the BaseAPIManager class
        """
        self._delay = 0
        self._last_increased_time = 0
        self._min_increase_diff_sec = C.BASE_CLIENT_MIN_INCREASE_DIFF_SEC

    def _increase_delay(self) -> None:
        """The method to increase the delay with checking the minimum increase difference and avoid too fast increase
        in the case if there were too many requests in a short period of time
        """
        if time.time() - self._last_increased_time > self._min_increase_diff_sec:
            self._delay += 0.1
            self._last_increased_time = time.time()

    async def _get_json_response(
        self, url: str, data: dict | None = None, method: str = "GET",
        query_params: dict | None = None, raise_on_status_code: dict[int, type[Exception]] | None = False,
        add_status_code: bool = False, headers: dict | None = None
    ) -> list | dict:
        """This method is used to get the response from the API
        :param url: a string representing the url of the resource
        :param headers: a dictionary representing the headers to be sent
        :param query_params: a dictionary representing the query parameters
        :param data: a dictionary representing the data to be sent
        :param method: a string representing the method to be used
        :param raise_on_status_code: a boolean representing whether to raise
        an exception if the status code is not in the range of
        [200, 201, 202, 204, 404]
        :param add_status_code: a boolean representing whether to add the status
        into the result dict
        :return: a list or a dict
        """
        raise_on_status_code = raise_on_status_code or {}

        async with (httpx.AsyncClient() as client):
            method_mapper = {
                "GET": client.get,
                "POST": client.post,
                "PUT": client.put,
                "DELETE": client.delete,
                "PATCH": client.patch
            }
            request_method = method_mapper.get(method)
            try:
                result = {}
                if method in ["POST", "PUT", "PATCH"]:
                    response = await request_method(
                        url=url, json=data, params=query_params,
                        headers=headers)
                else:
                    response = await request_method(
                        url=url, params=query_params, headers=headers)
                if add_status_code:
                    result['status_code'] = response.status_code

                if response.status_code in [200, 201, 202, 204]:
                    json_response = response.json()
                    if type(json_response) is list:
                        json_response = {'value': json_response}
                    result.update(json_response)

                elif response.status_code in raise_on_status_code:
                    exception_class = raise_on_status_code.get(response.status_code, ValueError)
                    raise exception_class(f'Status code is not OK: {response.text}')
                else:
                    logging.error(f'URL: {url}, Status code is not OK: {response.text}')

            except Exception as e:
                logging.error(f'URL: {url}, Error while making request: {e}')

        return result
