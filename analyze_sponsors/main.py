import asyncio
import logging
import pathlib

import careers_page
import logs
import csv_utils
from analyze_sponsors import open_positions

OUTPUTS_DIR = pathlib.Path(".") / "run_outputs"
EMPLOYERS_CSV = pathlib.Path(".") / "data" / "approved_employers.csv"
LOGS_PATH = OUTPUTS_DIR / "logs"
CURRENT_RUN_DIR = OUTPUTS_DIR / "1"


async def process_company(name: str):
    error = None
    try:
        logs.trace_id_var.set(name)
        logging.info("[%s] processing company %s", logs.trace_id_var.get(), name)
        website_url = await careers_page.find_website(name)
        positions = await open_positions.analyze(website_url)
        csv_utils.persist_open_positions(name, positions)
    except Exception as e:
        error = e
    return name, error


async def main():
    logs.setup_logging(LOGS_PATH, logging.DEBUG)
    raw_employers = csv_utils.read_csv_to_dict(EMPLOYERS_CSV)
    # TODO - apply for all companies
    raw_employers = raw_employers[:50]
    # raw_employers = [raw_employers[40]]
    company_names = [entry["Organisation Name"] for entry in raw_employers]
    res = await asyncio.gather(*(process_company(company_name) for company_name in company_names), return_exceptions=True)
    for company_name, err in res:
        if err:
            logging.error("[%s] analysis failed with error: %s", company_name, err)
    logs.flush_logger()


if __name__ == '__main__':
    asyncio.run(main())

