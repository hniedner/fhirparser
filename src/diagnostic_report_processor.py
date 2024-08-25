import csv
from typing import Any

from lxml import etree as ET

NS = {"fhir": "http://hl7.org/fhir"}


def parse_diagnostic_reports_from_bundle_file(file_path: str) -> list[dict[str, Any]]:
    """Parse the FHIR bundle from an XML file to extract diagnostic report details."""
    reports = []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        entries = root.findall("fhir:entry", NS)

        for entry in entries:
            diagnostic_report = entry.find("fhir:resource/fhir:DiagnosticReport", NS)
            if diagnostic_report is not None:
                report_details = extract_diagnostic_report_details(diagnostic_report)
                reports.append(report_details)

    except ET.XMLSyntaxError as e:
        print(f"Error parsing XML file {file_path}: {e}")

    return reports


def extract_diagnostic_report_details(report: ET.Element) -> dict[str, Any]:
    """Extract details from a DiagnosticReport resource element."""
    return {
        'report_id': get_attribute_value(report, "fhir:id", 'value'),
        'identifier': get_identifier(report),
        'status': get_attribute_value(report, "fhir:status", 'value'),
        'category': get_category_text(report),
        'code': get_code_text(report),
        'patient_name': get_attribute_value(report, "fhir:subject/fhir:display", 'value'),
        'patient_id': get_patient_id(report),
        'effective_date_time': get_attribute_value(report, "fhir:effectiveDateTime", 'value'),
        'issued': get_attribute_value(report, "fhir:issued", 'value'),
        'performer': get_attribute_value(report, "fhir:performer/fhir:display", 'value'),
        'results': get_results(report)
    }


def get_attribute_value(element: ET.Element, xpath: str, attribute: str) -> str:
    """Fetches the value of a specified attribute from an XML element located by XPath."""
    found = element.find(xpath, NS)
    return found.attrib.get(attribute, 'N/A') if found is not None else 'N/A'


def get_identifier(report: ET.Element) -> str:
    """Extract the identifier value from the DiagnosticReport."""
    identifier = get_attribute_value(report, "fhir:identifier/fhir:value", 'value')
    return identifier


def get_patient_id(report: ET.Element) -> str:
    """Extract the patient ID from the reference attribute."""
    reference = get_attribute_value(report, "fhir:subject/fhir:reference", 'value')
    return reference.split('/')[-1] if reference != 'N/A' else 'N/A'


def get_category_text(report: ET.Element) -> str:
    """Extract the category text of the DiagnosticReport."""
    category = get_attribute_value(report, "fhir:category/fhir:text", 'value')
    if category == 'N/A':
        category = get_attribute_value(report, "fhir:category/fhir:coding/fhir:display", 'value')
    return category


def get_code_text(report: ET.Element) -> str:
    """Extract the code text of the DiagnosticReport."""
    code = get_attribute_value(report, "fhir:code/fhir:text", 'value')
    return code


def get_results(report: ET.Element) -> list[dict[str, str]]:
    """Extract the results (observations) referenced in the DiagnosticReport."""
    results = []
    result_elements = report.findall("fhir:result", NS)
    for result in result_elements:
        observation_ref = get_attribute_value(result, "fhir:reference", 'value')
        observation_display = get_attribute_value(result, "fhir:display", 'value')
        results.append({
            'observation_ref': observation_ref.split('/')[-1],
            'observation_display': observation_display
        })
    return results


def export_diagnostic_reports_to_csv(reports: list[dict[str, Any]], output_file: str) -> None:
    """Export the diagnostic report details to a CSV file."""
    columns: list[str] = [
        'report_id', 'patient_name', 'patient_id', 'effective_date_time',
        'identifier', 'status', 'category', 'code',
        'issued', 'performer', 'results'
    ]
    with open(output_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for report in reports:
            # Flatten results for CSV export
            report_copy = report.copy()
            report_copy['results'] = '; '.join(
                [f"{r['observation_display']} (ID: {r['observation_ref']})" for r in report['results']])
            writer.writerow(report_copy)


if __name__ == "__main__":
    # Load the FHIR bundle from an XML file
    xml_file_path = "../resources/BundleDiagnosticReports/1111111DiagnosticReport.xml"
    diagnostic_reports = parse_diagnostic_reports_from_bundle_file(xml_file_path)

    # Export the parsed diagnostic reports to a CSV file
    output_csv = 'diagnostic_reports.csv'
    export_diagnostic_reports_to_csv(diagnostic_reports, output_csv)
    print(f"Results exported to {output_csv}")
