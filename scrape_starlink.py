import csv
import glob
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

from bs4 import BeautifulSoup


MONTHS = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
}


def load_document(path):
    with open(path, "r", encoding="utf-8") as file:
        return BeautifulSoup(file.read(), "html.parser")


def find_cycle_month(document):
    heading = document.select_one('h6[class*="1bcwr2w"]')
    if heading is None:
        return datetime.now().month

    label = heading.get_text(strip=True)
    return MONTHS.get(label, datetime.now().month)


def find_cycle_year(paragraphs):
    current_year = datetime.now().year
    pattern = re.compile(r"\d{1,2}/\d{1,2}/(\d{4})")

    for paragraph in paragraphs:
        text = paragraph.get_text(" ", strip=True)
        match = pattern.search(text)
        if match:
            return int(match.group(1))

    return current_year


def extract_total_gb(paragraphs):
    default_total = 459.0

    for index in range(len(paragraphs)):
        text = paragraphs[index].get_text(" ", strip=True)
        if "Total Data Usage" not in text:
            continue

        try:
            next_text = paragraphs[index + 1].get_text(" ", strip=True)
            next_text = next_text.replace("GB", "").strip()
            return float(next_text)
        except Exception:
            return default_total

    return default_total


def get_bar_values(document):
    bars = document.find_all("rect", class_="MuiBarElement-series-y_0")
    values = []

    for bar in bars:
        try:
            values.append(float(bar.get("height", 0)))
        except (TypeError, ValueError):
            values.append(0.0)

    return values


def convert_bars_to_rows(start_date, heights, total_gb):
    total_height = sum(heights)
    if total_height == 0:
        return None

    scale = total_gb / total_height
    output_rows = []

    for offset, height in enumerate(heights):
        day = start_date + timedelta(days=offset)
        output_rows.append(
            {
                "Date": day.strftime("%m/%d/%Y"),
                "GB": round(height * scale, 2),
            }
        )

    return output_rows


def process_html(path):
    document = load_document(path)
    paragraphs = document.find_all("p")

    total_gb = extract_total_gb(paragraphs)
    heights = get_bar_values(document)

    if not heights or sum(heights) == 0:
        return None, None

    month_num = find_cycle_month(document)
    year_num = find_cycle_year(paragraphs)

    start_date = datetime(year_num, month_num, 17)
    print(f"   -> Anchoring cycle start to: {start_date.strftime('%B %d, %Y')}")

    rows = convert_bars_to_rows(start_date, heights, total_gb)
    return total_gb, rows


def pick_files(file_list):
    print("Found files:")
    for idx, file_path in enumerate(file_list, start=1):
        print(f"  [{idx}] {os.path.basename(file_path)}")
    print("  [0] Process Everything")

    choice = input("\nSelect a option to scrape: ").strip()

    if choice == "0":
        return file_list

    try:
        chosen_index = int(choice) - 1
        return [file_list[chosen_index]]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return []


def save_csv(destination, usage_map, total_consumption):
    ordered_dates = sorted(
        usage_map.keys(),
        key=lambda item: datetime.strptime(item, "%m/%d/%Y")
    )

    with open(destination, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Data Usage (GB)"])

        for date_text in ordered_dates:
            writer.writerow([date_text, round(usage_map[date_text], 2)])

        writer.writerow([])
        writer.writerow(["Total Usage", round(total_consumption, 2)])


def auto_scrape_starlink():
    base_dir = Path(__file__).resolve().parent
    html_files = glob.glob(str(base_dir / "*.html"))

    if not html_files:
        print(f"Error: No .html files found in {base_dir}")
        return

    selected_files = pick_files(html_files)
    if not selected_files:
        return

    merged_usage = defaultdict(float)
    combined_total = 0.0

    for html_file in selected_files:
        print(f"\nProcessing: {os.path.basename(html_file)}")
        total_gb, rows = process_html(html_file)

        if not rows:
            print("   -> Error: Could not extract data from file.")
            continue

        combined_total += total_gb

        for row in rows:
            merged_usage[row["Date"]] += row["GB"]

    if not merged_usage:
        print("\nNo rows generated to export.")
        return

    output_file = base_dir / "data_usage.csv"

    try:
        save_csv(output_file, merged_usage, combined_total)
        print("\nSuccess! Exported to 'data_usage.csv'.")
        print(f"Total Combined Usage: {round(combined_total, 2)} GB")
    except PermissionError:
        print("\nError: Could not save 'data_usage.csv'. Please close the file if it is open in Excel.")


if __name__ == "__main__":
    auto_scrape_starlink()