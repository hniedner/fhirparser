# fhir_file_operations.py
import csv
from typing import List, Any


def write_to_csv(columns: List[str], rows: List[List[Any]], output_csv: str) -> None:
    """Write data to a CSV file."""
    with open(output_csv, mode='w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(columns)
        csv_writer.writerows(rows)

