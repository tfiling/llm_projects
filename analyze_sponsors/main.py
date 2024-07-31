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
temp_blacklist = [
    "10BE5 LTD.",
    "29FORWARD Ltd",
    "Adam Ellis Ltd",
    "Adludio Limited",
    "Admaxim Limited",
    "ADSWIZZ LIMITED",
    "Advancy Limited",
    "Advantage Solicitors Ltd T/A Advantage Solicitors",
    "Aeguana Ltd",
]


def _is_already_processed(company_name: str):
    expected_csv_file = CURRENT_RUN_DIR / "positions" / f"{company_name}.csv"
    return expected_csv_file.exists()


async def process_company(name: str):
    error = None
    try:
        logs.trace_id_var.set(name)
        if name in temp_blacklist:
            logging.info("[%s] skipping black listed company", logs.trace_id_var.get())
            return name, None
        if _is_already_processed(name):
            logging.info("[%s] already processed", logs.trace_id_var.get())
            return name, None
        logging.info("[%s] processing company", logs.trace_id_var.get())
        website_url = await careers_page.find_website(name)
        positions = await open_positions.analyze(website_url)
        csv_utils.persist_open_positions(name, positions)
    except Exception as e:
        error = e
    return name, error


async def process_batch(raw_employers):
    company_names = {entry["Organisation Name"] for entry in raw_employers}
    res = await asyncio.gather(*(process_company(company_name) for company_name in company_names),
                               return_exceptions=True)
    for company_name, err in res:
        if err:
            logging.error("[%s] analysis failed with error: %s", company_name, err)


async def main():
    logs.setup_logging(LOGS_PATH, logging.DEBUG)
    raw_employers = csv_utils.read_csv_to_dict(EMPLOYERS_CSV)
    # TODO - apply for all companies
    batch_size = 10
    batches = [raw_employers[i:i + batch_size] for i in range(0, len(raw_employers), batch_size)]
    # batches = batches[:1000]
    for b in batches:
        await process_batch(b)
    logs.flush_logger()


if __name__ == '__main__':
    asyncio.run(main())
