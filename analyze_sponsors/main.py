import asyncio
import csv
import logging
import pathlib

import careers_page
import logs

OUTPUTS_DIR = pathlib.Path(".") / "run_outputs"
EMPLOYERS_CSV = pathlib.Path(".") / "data" / "approved_employers.csv"
LOGS_PATH = OUTPUTS_DIR / "logs"


def read_csv_to_dict(path: pathlib.Path) -> list:
    result = []
    with open(path, 'r', newline='') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        for row in csv_reader:
            result.append(row)
    return result


async def process_company(name: str):
    logs.trace_id_var.set(name)
    logging.info("[%s] processing company %s", logs.trace_id_var.get(), name)
    website_url = await careers_page.find_website(name)


async def main():
    logs.setup_logging(LOGS_PATH, logging.DEBUG)
    raw_employers = read_csv_to_dict(EMPLOYERS_CSV)
    # TODO - apply for all companies
    raw_employers = raw_employers[:45]
    company_names = [entry["Organisation Name"] for entry in raw_employers]
    _ = await asyncio.gather(*(process_company(company_name) for company_name in company_names), return_exceptions=True)
    logs.flush_logger()


if __name__ == '__main__':
    asyncio.run(main())

