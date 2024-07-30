import logging
import pathlib
import typing
import csv
from datetime import datetime


def persist_open_positions(company_name, open_positions: typing.List[dict], override_last_res=False):
    if not open_positions:
        logging.info("[%s] empty list of open positions was provided", company_name)
        return
    logging.debug("[%s] persisting found jobs: %s", company_name, open_positions)
    
    fieldnames = ["title", "type", "location"]
    dest_file = pathlib.Path(".") / "run_outputs" / "1" / "positions" / f"{company_name}.csv"
    if dest_file.exists():
        if not override_last_res:
            logging.info("[%s] open positions were already extracted. exiting", company_name)
            return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_file_path = dest_file.with_name(f"{dest_file.stem}_{timestamp}{dest_file.suffix}")
        dest_file.rename(new_file_path)
        logging.debug("[%s] existing open positions csv from last run was renamed", company_name)

    with open(dest_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for raw_position_details in open_positions:
            if not raw_position_details.get("title"):
                logging.error("[%s] ignoring a position that is missing a title: %s",
                              company_name, raw_position_details)
                continue
            row = {
                "title": raw_position_details.get("title"),
                "type": raw_position_details.get("type", "N/A"),
                "location": raw_position_details.get("location", "N/A")
            }
            writer.writerow(row)


def read_csv_to_dict(path: pathlib.Path) -> list:
    result = []
    with open(path, 'r', newline='') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        for row in csv_reader:
            result.append(row)
    return result


