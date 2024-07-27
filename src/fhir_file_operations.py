# fhir_file_operations.py
import csv
from typing import Dict

from fhir_dataclasses import DiagnosticReport


def write_to_csv(
        diagnostic_reports: Dict[str, DiagnosticReport],
        output_csv: str
) -> None:
    """Write extracted data to a CSV file."""
    with open(output_csv, mode='w', newline='') as csvfile:
        csv_writer: csv.writer = csv.writer(csvfile)
        csv_writer.writerow(['Patient Name', 'Patient ID', 'Observation/Condition Name', 'Date', 'Value'])

        for report_data in diagnostic_reports.values():
            patient_name = report_data.patient_name
            patient_id = report_data.patient_id
            for obs in report_data.observations:
                csv_writer.writerow([patient_name, patient_id, obs.name, obs.date, obs.value])
