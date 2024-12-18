import json
import pathlib
import subprocess
import typing
from urllib import parse

json_path = pathlib.Path("/home/galt/code/llm_projects/analyze_sponsors/log_analysis/categorize_by_name_results.json")
probability_json_path = pathlib.Path("/home/galt/code/llm_projects/analyze_sponsors/run_outputs/1/hiring_probability/hiring_probability.json")
class_path = pathlib.Path("/home/galt/code/llm_projects/analyze_sponsors/log_analysis/manual_class.json")
class_back_path = pathlib.Path("/home/galt/code/llm_projects/analyze_sponsors/log_analysis/manual_class_back.json")

classifications_menu = {
    1: "relevant, interesting and hiring",
    2: "relevant and hiring",
    3: "interesting not hiring",
    4: "relevant not hiring",
    5: "irrelevant",
}


def open_chrome_search(term: str):
    term = parse.quote(term)
    command = ['google-chrome', f'https://www.google.com/search?q={term}']

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            print("Chrome launched successfully.")
        else:
            print(f"Error launching Chrome. Return code: {process.returncode}")
            if stderr:
                print(f"Error message: {stderr.decode('utf-8')}")

    except FileNotFoundError:
        print("Error: 'google-chrome' command not found. Make sure Chrome is installed and in your PATH.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def print_menu(company_name: str):
    print(f"{company_name}:")
    for key, val in classifications_menu.items():
        print(f"{key}) {val}")


def persist_classification(choice: int, name: str):
    if choice not in list(classifications_menu):
        raise RuntimeError("invalid choice")
    classifications = {}
    if class_path.exists():
        with open(class_path, "r") as f:
            classifications = json.load(f)
        class_path.rename(class_back_path)
    curr = classifications.get(classifications_menu[choice], [])
    curr.append(name)
    classifications[classifications_menu[choice]] = curr
    with open(class_path, "w") as f:
        json.dump(classifications, f)
    print(f"successfully persisted {name}: {choice}")


def load_persisted_classifications() -> typing.Set[str]:
    res = set()
    if not class_path.exists():
        return res
    with open(class_path) as f:
        d = json.load(f)
    for companies in d.values():
        res = res | set(companies)
    return res


def catalog_by_company_category():
    with open(json_path) as f:
        companies = json.load(f)
    already_classified = load_persisted_classifications()
    for obj in companies:
        for name, category in obj.items():
            if name in already_classified:
                continue
            if category != "Technology & Software":
                continue
            open_chrome_search(f"{name} careers")
            print_menu(name)
            choice = input("select:")
            choice = int(choice.strip())
            persist_classification(choice, name)


def catalog_by_company_probability(max=100, min=100):
    with open(probability_json_path) as f:
        companies = json.load(f)
    already_classified = load_persisted_classifications()
    for obj in companies:
        for name, probability in obj.items():
            if name in already_classified:
                continue
            if int(probability) > max or int(probability) < min:
                continue
            open_chrome_search(f"{name}")
            print_menu(name)
            choice = input("select:")
            choice = int(choice.strip())
            persist_classification(choice, name)


if __name__ == '__main__':
    catalog_by_company_category()
