import csv
import pathlib


def read_csv_to_dict(path: pathlib.Path) -> list:
    result = []
    with open(path, 'r', newline='') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        for row in csv_reader:
            result.append(row)
    return result


if __name__ == '__main__':
    file_path = pathlib.Path(".") / "data" / "approved_employers.csv"
    data = read_csv_to_dict(file_path)
    print(data)
