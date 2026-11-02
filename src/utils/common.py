import asyncio
import html
import json
import logging
import re
from functools import wraps
from typing import Callable, Optional
from uuid import uuid4
import markdown
from bs4 import BeautifulSoup
# ---------------------------------------------------------------------------------------------------------------------


def safe_div(a: float, b: float, default: float = 0.0) -> float:
    try:
        return a / b if b else default
    except Exception:
        return default


def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def is_markdown(text: str) -> bool:
    """
    Checks whether the given text contains Markdown formatting.
    """

    if not text or not isinstance(text, str):
        return False

    markdown_patterns = [
        r"\*\*[^*]+\*\*",        # bold: **text**
        r"__[^_]+__",            # bold: __text__
        r"\*[^*]+\*",            # italics: *text*
        r"_[^_]+_",              # italics: _text_
        r"`[^`]+`",              # inline code: `code`
        r"```[\s\S]+```",        # code block: ```...```
        r"\[[^\]]+\]\([^)]+\)",  # links: [text](url)
        r"^#{1,6}\s",            # headings: # Title
        r"!\[[^\]]*\]\([^)]+\)", # images: ![](url)
        r"^\s*[-*+]\s",          # unordered list: - item
        r"^\s*\d+\.\s",          # ordered list: 1. item
        r">\s",                  # blockquote: > text
    ]

    return any(re.search(pattern, text, flags=re.MULTILINE)
               for pattern in markdown_patterns)


def clean_text(raw_text: str, max_paragraphs: int = 1) -> str:
    """
    Universal cleanup of HTML/Markdown game descriptions for Telegram publishing.
    """
    if not raw_text:
        return ""

    text = raw_text.strip()

    # --- 1. Convert Markdown → HTML (if markdown markup is present)
    if any(sym in text for sym in ['**', '*', '_', '[', ']', '(', ')', '#', '`']):
        try:
            text = markdown.markdown(text)
        except Exception:
            pass

    # --- 2. Parse HTML and extract clean text with minimal structure
    soup = BeautifulSoup(text, "html.parser")

    # Preserve basic structure (headings, lists, paragraphs)
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for p in soup.find_all("p"):
        p.insert_before("\n\n")
    for li in soup.find_all("li"):
        li.insert_before("• ")
    for hr in soup.find_all("hr"):
        hr.replace_with("\n— — —\n")

    # --- 3. Remove everything extra (tags, scripts, etc.)
    cleaned = soup.get_text(separator=" ", strip=True)

    # --- 4. Format: remove extra spaces and repeated newlines
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)

    # --- 5. Support simple Markdown formatting for Telegram
    # (keep *, _, `, but drop stray ones)
    cleaned = re.sub(r'(?<!\S)\*(?!\S)', '', cleaned)  # lone * without a pair
    cleaned = re.sub(r'(?<!\S)_(?!\S)', '', cleaned)

    # --- 6. Trim to a reasonable number of paragraphs
    paragraphs = [p.strip() for p in cleaned.split("\n") if p.strip()]
    if len(paragraphs) > max_paragraphs:
        paragraphs = paragraphs[:max_paragraphs]
        paragraphs.append("…")

    final_text = "\n\n".join(paragraphs)

    # --- 7. Final cleanup and tidy presentation
    final_text = final_text.strip()
    final_text = re.sub(r'([^\n])\n([^\n])', r'\1\n\n\2', final_text)  # more breathing room
    return final_text


def execute_in_thread(coro: Callable) -> Callable:
    """The decorator serves to execute any task in separate thread to avoid blocking main program execution
    :param coro: a callable object returning Coroutine to wrap
    """
    @wraps(coro)
    async def wrapper(*args, **kwargs) -> dict[str, str]:
        """The async func is a wrapper to wrap provided coro and execute it in separate thread
        :params args: a positional arguments
        :param kwargs: a keyword arguments
        """
        task_id = str(uuid4())
        kwargs['task_id'] = task_id
        e = None
        for _ in range(3):
            try:
                loop = asyncio.get_running_loop()
                task = loop.create_task(coro(*args, **kwargs))
                task.add_done_callback(
                    lambda t: logging.error("Task failed", exc_info=t.exception()) if t.exception() else None
                )
                break
            except Exception as err:
                e = err
                kwargs.pop('task_id')
        else:
            if e:
                raise e
        return {'task_id': task_id}

    return wrapper


def repeat_execution_async(
    attempts: int = 3, ignore_errors: bool = True,
    log_results: bool = True, delay: int = 0,
    attempt_if_not_result: bool = False,
    excepts: tuple | None = None
) -> any:
    """This decorator is used try to use a few attempts to execute a wrapped
    function
    :param ignore_errors: a boolean representing whether to return the result as None if any error occurs during
    making request or raise an exception then all attempts are over if ignore_errors is False
    :param attempts: an integer representing the number of attempts to execute
    the wrapped function
    :param delay: an integer representing the delay in seconds between attempts
    to execute the wrapped function
    :param attempt_if_not_result: a boolean representing whether to execute
    the wrapped function one more time if the result is equal to bool(False)
    :param log_results: a boolean representing whether to log the results
    :param excepts: a tuple representing the exceptions to catch
    """
    excepts = excepts or (Exception,)
    def decorator(func):
        async def wrapper(*args, **kwargs):
            result = None
            e = None
            for _ in range(abs(attempts) or 1):
                try:
                    result = await func(*args, **kwargs)
                    if attempt_if_not_result and not result:
                        raise ValueError(
                            f'The function {func.__name__} returned no result')
                    if log_results:
                        logging.info(
                            f'Async function completed successfully:'
                            f' {func.__name__}')
                    return result

                except excepts as error:
                    e = error
                    await asyncio.sleep(abs(delay))
                    if log_results:
                        logging.error(
                            f'Async function: {func.__name__}, kwargs:'
                            f' {kwargs}, interrupted with error: {e}')

                except Exception:
                    return result

            if not ignore_errors and e:
                raise e

            return result

        return wrapper

    return decorator


def clean_html(html_text: Optional[str]) -> str:
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, "html.parser")
    for tag in soup.find_all(["a", "script", "style"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {}

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}