import json
import logging
import pathlib
import re

import aiohttp
import bs4
from diskcache import Cache
import anthropic

from analyze_sponsors import logs
from analyze_sponsors import prompts

cache = Cache(str(pathlib.Path(".") / "run_outputs" / "1"))


async def analyze(careers_page_url: str):
    logging.debug("[%s] analyzing open positions", logs.trace_id_var.get())
    page_contents = await _get_stripped_page_content(careers_page_url)
    return _extract_open_positions(page_contents)


def _extract_open_positions(page_contents: str) -> list:
    message = _send_api_request(page_contents)
    if message.stop_reason != "end_turn":
        logging.warning("[%s] unexpected stop reason: %s", logs.trace_id_var.get(), message.stop_reason)
    if not message.content:
        logging.error("[%s] open positions extraction prompt resulted an empty reply", logs.trace_id_var.get())
        return []
    if len(message.content) > 1:
        logging.warning("[%s] received more than one content block", logs.trace_id_var.get())
        print(str(message.content))
    open_positions_dict = _extract_json_from_text_block(message.content[0].text)
    return open_positions_dict.get("positions", [])


@cache.memoize()
def _send_api_request(page_contents: str) -> anthropic.types.Message:
    client = anthropic.Anthropic(
        api_key="",
    )
    message = client.messages.create(
        max_tokens=1024,
        system=prompts.ANALYZE_OPEN_POSITIONS_PAGE,
        messages=[
            {
                "role": "user",
                "content": page_contents,
            }
        ],
        model="claude-3-5-sonnet-20240620",
        temperature=0
    )
    logging.debug("[%s] position extraction prompt was sent. usage: %s", logs.trace_id_var.get(), message.usage)
    return message


async def _get_stripped_page_content(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, allow_redirects=False) as resp:
            html_content = await resp.text()
    soup = bs4.BeautifulSoup(html_content, 'html.parser')
    tags_to_remove = [
        "script", "style", "meta", "link", "header", "footer", "nav",
        "aside", "noscript", "iframe", "svg", "form", "input", "button"
    ]
    for tag in tags_to_remove:
        for element in soup.find_all(tag):
            element.decompose()
    for comment in soup.find_all(text=lambda text: isinstance(text, bs4.Comment)):
        comment.extract()
    text = soup.get_text()
    text = re.sub(r'\n\s*\n', '\n', text)
    return text


def _extract_json_from_text_block(text_block: str) -> dict:
    res = {}
    if "```json" in text_block:
        start = text_block.index("```json")
        end = text_block.rindex("```")
        if end <= start:
            print("[%s] detected an invalid json annotation in text block")
            return {}
        text_block = text_block[start + len("```json"):end]
    try:
        res = json.loads(text_block)
    except json.JSONDecodeError as e:
        print(str(e))
    return res
