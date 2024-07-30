import asyncio
import difflib
import logging
import pathlib
import typing
import re
from urllib import parse

from diskcache import Cache
import oxylabs

import logs

cache = Cache(str(pathlib.Path(".") / "run_outputs" / "1" / "search_cache"))


async def find_website(name: str) -> str:
    website_search_methods = [
        concrete_google_search
    ]
    for method in website_search_methods:
        website_url = await method(name)
        if website_url:
            return website_url
    logging.warning("[%s] could not find website for company", logs.trace_id_var.get())
    raise RuntimeError(f"could not find website for company {name}")


async def concrete_google_search(name: str) -> typing.Optional[str]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, sync_concrete_google_search, name)
    # return sync_concrete_google_search(name)


def sync_concrete_google_search(name: str) -> typing.Optional[str]:
    # Might be applied in a separate context due since it's not async
    logs.trace_id_var.set(name)
    website_url = _query_for_website(name)
    if not website_url:
        logging.warning("[%s] No google search results", logs.trace_id_var.get())
        raise RuntimeError("No google search results")
    try:
        logging.debug("[%s] found careers page %s", logs.trace_id_var.get(), website_url)
        similarity = _domain_company_similarity(website_url, name)
        if similarity < 0.6:
            logging.info("[%s] website %s is not similar enough to company name(%.2f%% similar)",
                         logs.trace_id_var.get(), website_url, similarity)
            return None
    except Exception as e:
        logging.error("[%s] could not calculate website similarity to company name: %s",
                      logs.trace_id_var.get(), e)
        return None
    logging.info("[%s] found careers page(%.2f%% similar): %s", logs.trace_id_var.get(), similarity, website_url)
    return website_url


@cache.memoize()
def _query_for_website(name: str) -> typing.Optional[str]:
    logging.debug("[%s] cache miss for google search", logs.trace_id_var.get())
    # sleep_time = random.uniform(5, 10)
    # sleep_time = 0.2
    # logging.debug("[%s] sleeping %.2f%% seconds", logs.trace_id_var.get(), sleep_time)
    # time.sleep(sleep_time)
    try:
        client = oxylabs.RealtimeClient("tfiling_AkUi1", "MxQSK8bQyjyM6h_")
        response = client.serp.google.scrape_search(f"{name} official website careers", limit=1,
                                                    geo_location="United Kingdom", parse=True)
        if not response:
            raise RuntimeError("internal scraper failure")
        logging.debug("[%s] search results: %s", logs.trace_id_var.get(), response.results)
        return _extract_first_result(response)
    except Exception as e:
        logging.warning("[%s] failed searching careers page: %s", name, e)
        raise e


def _extract_first_result(response) -> typing.Optional[str]:
    if len(response.results) == 0:
        logging.debug("[%s] empty search results", logs.trace_id_var.get())
        return None
    result = response.results[0]
    logging.debug("[%s] processing result %s", logs.trace_id_var.get(), result.content)
    if ("results" not in result.content or
            "organic" not in result.content["results"]):
        logging.error("[%s] invalid response schema", logs.trace_id_var.get())
        return None
    if len(result.content["results"]["organic"]) == 0:
        logging.warning("[%s] no search results", logs.trace_id_var.get())
        return None
    if "url" not in result.content["results"]["organic"][0]:
        logging.error("[%s] missing url from result: %s", logs.trace_id_var.get(), result.content["results"]["organic"][0])
        return None
    return result.content["results"]["organic"][0]["url"]


def _domain_company_similarity(url: str, company_name: str):
    parsed_url = parse.urlparse(url)
    domain = parsed_url.netloc if parsed_url.netloc else parsed_url.path
    domain_parts = domain.split('.')
    if len(domain_parts) > 2:
        second_level_domain = domain_parts[-2]
    else:
        second_level_domain = domain_parts[0]
    second_level_domain = _clean_string(second_level_domain)
    company_name = _clean_string(company_name)
    logging.debug("[%s] extracted second level domain %s from %s",
                  logs.trace_id_var.get(), second_level_domain, url)
    similarity = _get_similarity_ratio(second_level_domain, company_name)

    return similarity


def _get_similarity_ratio(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()


def _clean_string(s: str):
    """Remove non-alphanumeric characters and convert to lowercase"""
    return re.sub(r'[^a-zA-Z0-9]', '', s).lower()
