import asyncio
import difflib
import logging
import pathlib
import typing
import re
from urllib import parse
import threading

import bs4
import requests
from diskcache import Cache
import oxylabs

from analyze_sponsors.logs import logs
from analyze_sponsors import keywords

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
    raise AssertionError(f"could not find website for company {name}")


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
        if similarity > 0.6:
            logging.info("[%s] found careers page(%.2f%% similar): %s", logs.trace_id_var.get(),
                         similarity, website_url)
            return website_url
        contains_keywords = False
        try:
            matched_words = run_with_timeout(_find_relevant_keywords, args=(website_url,), timeout_seconds=5)
            logging.debug("[%s] careers page contents matched %d keywords: %s",
                          logs.trace_id_var.get(), len(matched_words), matched_words)
            contains_keywords = len(matched_words) > 0
        except TimeoutError:
            logging.info("[%s] could not fetch website in under 5 secs", logs.trace_id_var.get())
        if contains_keywords:
            logging.info("[%s] found careers page %s based on relevant keywords",
                         logs.trace_id_var.get(), website_url)
            return website_url
    except Exception as e:
        logging.error("[%s] could not calculate website similarity to company name: %s",
                      logs.trace_id_var.get(), e)
        raise e
    logging.info("[%s] website %s is not similar enough to company name",
                 logs.trace_id_var.get(), website_url)
    return None


@cache.memoize()
def _query_for_website(name: str) -> typing.Optional[str]:
    logging.debug("[%s] cache miss for google search", logs.trace_id_var.get())
    try:
        client = oxylabs.RealtimeClient("tfiling_AkUi1", "MxQSK8bQyjyM6h_")
        response = client.serp.google.scrape_search(f"{name} official website careers", limit=1,
                                                    geo_location="United Kingdom", parse=True)
        if not response:
            raise RuntimeError("internal scraper failure")
        logging.debug("[%s] search results: %s", logs.trace_id_var.get(), response.results)
        return _extract_first_result(response)
    except Exception as e:
        logging.warning("[%s] failed searching careers page: %s", logs.trace_id_var.get(), e)
        raise e


def _find_relevant_keywords(website_url) -> list:
    resp = requests.get(website_url)
    resp.raise_for_status()
    html_content = resp.text.lower()
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
    contents = re.sub(r'\n\s*\n', '\n', text)
    matched_words = [word for word in keywords.RELEVANT_POSITIONS_KEYWORDS if word in contents]
    logging.debug("[%s] careers page contents matched %d keywords: %s",
                  logs.trace_id_var.get(), len(matched_words), matched_words)
    return matched_words


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
        logging.error("[%s] missing url from result: %s", logs.trace_id_var.get(),
                      result.content["results"]["organic"][0])
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
    try:
        similarity = run_with_timeout(_get_similarity_ratio, args=(second_level_domain, company_name), timeout_seconds=5)
    except TimeoutError:
        logging.info("[%s] could not calculate in under 5 secs similarity to %s",
                     logs.trace_id_var.get(), url)
        return 0
    return similarity


def _get_similarity_ratio(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()


def _clean_string(s: str):
    """Remove non-alphanumeric characters and convert to lowercase"""
    return re.sub(r'[^a-zA-Z0-9]', '', s).lower()


def run_with_timeout(func, args=(), kwargs={}, timeout_seconds=5):
    result = [None]
    exception = [None]

    def worker():
        try:
            result[0] = func(*args, **kwargs)
        except Exception as e:
            exception[0] = e

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join(timeout_seconds)

    if thread.is_alive():
        raise TimeoutError(f"Function execution timed out after {timeout_seconds} seconds")

    if exception[0]:
        raise exception[0]

    return result[0]
