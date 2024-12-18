import asyncio
import datetime
import json
import logging
import pathlib
import re
import typing

import anthropic
from diskcache import Cache

from analyze_sponsors.logs import logs
from analyze_sponsors.prompts import hiring_developers_probability
from analyze_sponsors.utils import json_utils

OUTPUTS_DIR = pathlib.Path(".") / "run_outputs"
CATEGORIES_JSON = pathlib.Path(".") / "log_analysis" / "categorize_by_name_results.json"
CURRENT_RUN_DIR = OUTPUTS_DIR / "1"
DEDUCTION_RES_PATH = CURRENT_RUN_DIR / "hiring_probability" / "hiring_probability.json"
LOGS_PATH = OUTPUTS_DIR / "logs"

FORBIDDEN_RESP_LOG_PATTERN = re.compile(r"^.+careers_page.py:57 \| \[(.+)].+403 Client Error.+url: (.+)$")

cache = Cache(str(pathlib.Path(".") / "run_outputs" / "1" / "claude_cache"))


def _persist_batch(deductions: typing.List[dict]):
    if not DEDUCTION_RES_PATH.exists():
        logging.info(f"{DEDUCTION_RES_PATH.name} does not exist")
        accumulated_deductions = []
    else:
        current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        backup_target = DEDUCTION_RES_PATH.parent / f"{DEDUCTION_RES_PATH.name}_back_{current_time}"
        DEDUCTION_RES_PATH.rename(backup_target)
        with open(backup_target) as f:
            accumulated_deductions = json.load(f)
        if not _is_valid_deductions_list(accumulated_deductions):
            raise RuntimeError("unexpected invalid schema of precious deductions in categorize_by_name_results.json")
    accumulated_deductions.extend(deductions)
    with open(DEDUCTION_RES_PATH, "w") as f:
        json.dump(accumulated_deductions, f)


async def _deduct_hiring_probability(company_list_prompt: str):
    message = await _send_prompt(company_list_prompt)
    if not message.content:
        logging.error("deduction of companies hiring probability prompt resulted in an empty reply")
        return []
    if len(message.content) > 1:
        logging.warning("received more than one content block")
        print(str(message.content))
    return json_utils.extract_json_from_prompt_text_block(message.content[0].text)


def _is_valid_deductions_list(res):
    return all((len(d) == 1 for d in res))


async def _process_batch(prompts_batch: typing.List[str]) -> typing.List[dict]:
    gathered_res = []
    results = await asyncio.gather(
        *(_deduct_hiring_probability(company_list_prompt) for company_list_prompt in prompts_batch),
        return_exceptions=True)
    for res in results:
        if isinstance(res, Exception):
            logging.error("deduction failed with exception: %s", res)
            continue
        if not _is_valid_deductions_list(res):
            logging.error("invalid json parsed from claude response")
            print(res)
            continue
        logging.info("completed batch of %d companies", len(res))
        gathered_res.extend(res)
    return gathered_res


async def _deduct_companies_categories(company_list_prompt: str) -> typing.List[dict]:
    message = await _send_prompt(company_list_prompt)
    if not message.content:
        logging.error("deduction of company category by name prompt resulted in an empty reply")
        return []
    if len(message.content) > 1:
        logging.warning("received more than one content block")
        print(str(message.content))
    claude_response = message.content[0].text
    if message.stop_reason == "max_tokens":
        logging.info("fixing partial json response due to max token stop reason")
        claude_response = json_utils.amend_partial_json_resp(claude_response)
    return json_utils.extract_json_from_prompt_text_block(claude_response)


async def _send_prompt(company_list_prompt: str) -> anthropic.types.Message:
    compacted_list = re.sub("\n", ";", company_list_prompt)
    key = f"hiring_developers_probability;{compacted_list}"
    cached_resp = cache.get(key)
    if cached_resp:
        return cached_resp
    client = anthropic.AsyncClient(
        api_key="",
        max_retries=5,
    )
    message = await client.messages.create(
        max_tokens=4096,
        system=hiring_developers_probability.PROMPT,
        messages=[
            {
                "role": "user",
                "content": company_list_prompt,
            }
        ],
        model="claude-3-5-sonnet-20240620",
        temperature=0
    )
    logging.debug("deduction of company domain by name prompt was sent. usage: %s", message.usage)
    if message.stop_reason == "max_tokens":
        raise RuntimeError("prompt stopped with max tokens reason")
    cache.set(key, message)
    return message


def _read_companies():
    with open(CATEGORIES_JSON) as f:
        raw_json = json.load(f)
    companies = []
    for raw_obj in raw_json:
        if len(raw_obj) != 1:
            raise RuntimeError(f"invalid json obj: {raw_obj}")
        name, category = next(iter(raw_obj.items()))
        companies.append(f"{name}({category})")
    return companies


def _split_to_batches(companies: typing.List[str], companies_per_prompt=100, batch_size=5):
    prompts = []
    for i in range(0, len(companies), companies_per_prompt):
        prompts.append("\n".join(companies[i:i + companies_per_prompt]))
    return [prompts[i:i + batch_size] for i in range(0, len(prompts), batch_size)]


async def main():
    companies = _read_companies()
    batches = _split_to_batches(companies)
    for batch in batches:
        deductions = await _process_batch(batch)
        _persist_batch(deductions)



if __name__ == '__main__':
    logs.setup_logging(LOGS_PATH, logging.DEBUG, "hiring_probability_")
    asyncio.run(main())
