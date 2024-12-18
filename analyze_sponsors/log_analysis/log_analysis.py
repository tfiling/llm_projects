import asyncio
import datetime
import json
import logging
import pathlib
import re
import typing

import anthropic

from analyze_sponsors.logs import logs
from analyze_sponsors.prompts import categorize_by_company_name
from analyze_sponsors.utils import json_utils
from analyze_sponsors.utils import csv_utils

SCRAPER_LOGS_PATH = pathlib.Path(".") / "run_outputs" / "logs"
OUT_CSVS_DIR = pathlib.Path(".") / "run_outputs" / "1" / "positions"
EMPLOYERS_CSV = pathlib.Path(".") / "data" / "approved_employers.csv"
LOGS_DIR = pathlib.Path(".") / "log_analysis" / "logs"
FAILED_COMPANIES_FILE = pathlib.Path(".") / "log_analysis" / "categorize_by_name.txt"
CATEGORIZED_COMPANIES_FILE = pathlib.Path(".") / "log_analysis" / "categorize_by_name_results.json"

FORBIDDEN_RESP_LOG_PATTERN = re.compile(r"^.+careers_page.py:57 \| \[(.+)].+403 Client Error.+url: (.+)$")


def extract_from_logs_companies_with_no_keyword_matches() -> set:
    if not SCRAPER_LOGS_PATH.exists():
        raise RuntimeError(f"logs path does not exist {str(SCRAPER_LOGS_PATH)}")
    company_names = set()
    for log_file in SCRAPER_LOGS_PATH.iterdir():
        with open(log_file, "r") as f:
            for log_line in f:
                if "careers page contents matched 0 keywords" in log_line:
                    company_name = _extract_company_name_from_log(log_line)
                    company_names.add(company_name)
    return company_names


async def categorize_companies_that_failed():
    # company_names = (_extract_from_logs_companies_that_failed() |
    #                  _read_failed_companies_file() |
    #                  _list_companies_without_extracted_positions())
    # logging.debug("detected %d companies", len(company_names))
    company_names = _list_all_companies()
    logging.debug("listing all %d companies", len(company_names))
    categorized_companies = _read_cached_deducted_categories()
    logging.debug("%d companies already categorized", len(company_names))
    company_names = list(company_names - categorized_companies)
    logging.debug("%d companies left to be categorized", len(company_names))
    names_per_prompt = 100
    prompts = []
    for i in range(0, len(company_names), names_per_prompt):
        prompts.append("\n".join(company_names[i:i + names_per_prompt]))

    batch_size = 5
    batches = [prompts[i:i + batch_size] for i in range(0, len(prompts), batch_size)]
    for batch in batches:
        deductions = await _process_failed_companies_batch(batch)
        _persist_batch(deductions)


def extract_details_from_forbidden_resp_log(line: str):
    match = FORBIDDEN_RESP_LOG_PATTERN.match(line)
    if not match:
        raise RuntimeError("not a forbidden resp log")
    if len(match.groups()) != 2:
        raise RuntimeError("pattern could not extract forbidden resp name and url")
    return match.groups()[0], match.groups()[1]


def is_forbidden_response_log(line: str):
    return "could not calculate website similarity to company name: 403 Client Error: Forbidden for url:" in line


def _persist_batch(deductions: typing.List[dict]):
    if not CATEGORIZED_COMPANIES_FILE.exists():
        logging.info("categorize_by_name_results.json does not exist")
        accumulated_deductions = []
    else:
        current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        backup_target = CATEGORIZED_COMPANIES_FILE.parent / f"{CATEGORIZED_COMPANIES_FILE.name}_back_{current_time}"
        CATEGORIZED_COMPANIES_FILE.rename(backup_target)
        with open(backup_target) as f:
            accumulated_deductions = json.load(f)
        if not _is_valid_deductions_list(accumulated_deductions):
            raise RuntimeError("unexpected invalid schema of precious deductions in categorize_by_name_results.json")
    accumulated_deductions.extend(deductions)
    with open(CATEGORIZED_COMPANIES_FILE, "w") as f:
        json.dump(accumulated_deductions, f)


async def _process_failed_companies_batch(prompts_batch: typing.List[str]) -> typing.List[dict]:
    gathered_res = []
    results = await asyncio.gather(
        *(_deduct_companies_categories(company_list_prompt) for company_list_prompt in prompts_batch),
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
    client = anthropic.AsyncClient(
        api_key="",
        max_retries=5,
    )
    message = await client.messages.create(
        max_tokens=4096,
        system=categorize_by_company_name.PROMPT,
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
    return message


def _extract_from_logs_companies_that_failed() -> set:
    if not SCRAPER_LOGS_PATH.exists():
        raise RuntimeError(f"logs path does not exist {str(SCRAPER_LOGS_PATH)}")
    company_names = set()
    for log_file in SCRAPER_LOGS_PATH.iterdir():
        with open(log_file, "r") as f:
            for log_line in f:
                if "analysis failed with error" in log_line:
                    company_name = _extract_company_name_from_log(log_line)
                    company_names.add(company_name)
    return company_names


def _read_failed_companies_file() -> set:
    if not FAILED_COMPANIES_FILE.exists():
        logging.info("categorize_by_name.txt does not exist")
    with open(FAILED_COMPANIES_FILE) as f:
        return {line.strip() for line in f}


def _list_companies_without_extracted_positions() -> set:
    if not OUT_CSVS_DIR.exists():
        raise RuntimeError(f"output csvs dir does not exist {str(OUT_CSVS_DIR)}")
    company_names = set()
    for csv_file in OUT_CSVS_DIR.iterdir():
        positions = csv_utils.read_csv_to_dict(csv_file)
        if len(positions) == 0 or all(p["title"] == "N/A" for p in positions):
            name = csv_utils.get_company_name_from_csv_file_name(csv_file.name)
            logging.debug("extracted company name %s from %s", name, csv_file.name)
            company_names.add(name)
    return company_names


def _list_all_companies() -> set:
    return {entry["Organisation Name"] for entry in csv_utils.read_csv_to_dict(EMPLOYERS_CSV)}


def _read_cached_deducted_categories():
    if not CATEGORIZED_COMPANIES_FILE.exists():
        logging.info("categorize_by_name_results.json does not exist")
    with open(CATEGORIZED_COMPANIES_FILE) as f:
        detected_categories = json.load(f)
    return {list(category_detection)[0] for category_detection in detected_categories}


def _extract_company_name_from_log(log_line: str):
    start = log_line.index("[") + 1
    end = log_line.index("]")
    return log_line[start:end]


def _is_valid_deductions_list(deductions) -> bool:
    return isinstance(deductions, list) and all((isinstance(d, dict) for d in deductions))


if __name__ == '__main__':
    logs.setup_logging(LOGS_DIR, logging.DEBUG)
    asyncio.run(categorize_companies_that_failed())
