# fhir_bundle_processor.py
from plistlib import InvalidFileException
from typing import Any

from lxml import etree as ET

from src.fhir_constants import NS
from src.fhir_dataclasses import DiagnosticReport
from src.fhir_dataclasses import Patient
from src.utils import get_attribute_value
from src.utils import parse_resource_id
from src.utils import parse_xml_file


def parse_patient(resource: ET.Element) -> Patient:
    full_id_ref = get_attribute_value(resource, "fhir:subject/fhir:reference", 'value')
    patient_name = get_attribute_value(resource, "fhir:subject/fhir:display", 'value')
    patient: Patient = Patient(
        id=parse_resource_id(full_id_ref),
        name=patient_name
    )
    return patient


def parse_results(resource: ET.Element) -> list[str]:
    results: list[str] = []
    for reference in resource.findall("fhir:result/fhir:reference", NS):
        obs_ref: str = reference.attrib.get('value')
        if obs_ref:
            obs_id = obs_ref.split('/')[-1]
            results.append(obs_id)
    return results


def parse_diagnostic_report(resource: ET.Element) -> DiagnosticReport:
    report_id = get_attribute_value(resource, "fhir:id", 'value')
    report_date = get_attribute_value(resource, "fhir:effectiveDateTime", 'value')
    category = get_attribute_value(resource, "fhir:category/fhir:text", 'value')
    if category == 'N/A':
        category = get_attribute_value(resource, "fhir:category/fhir:coding/fhir:display", 'value')
    code = get_attribute_value(resource, "fhir:code/fhir:text", 'value')
    performer = get_attribute_value(resource, "fhir:performer/fhir:display", 'value')

    report: DiagnosticReport = DiagnosticReport(
        id=report_id,
        date=report_date,
        category=category,
        code=code,
        performer=performer,
        patient=parse_patient(resource),
        results=parse_results(resource)
    )
    return report


def extract_diagnostic_reports(file_path: str) -> list[DiagnosticReport]:
    """Extract patient information and details from DiagnosticReport entries in a Bundle resource XML file."""
    diagnostic_reports: list[DiagnosticReport] = []
    root: ET.Element = parse_xml_file(file_path)
    patient: Patient = parse_patient(root.find("fhir:resource/fhir:DiagnosticReport", NS))
    for entry in root.findall("fhir:entry", NS):
        resource = entry.find("fhir:resource/fhir:DiagnosticReport", NS)
        if resource is None:
            raise InvalidFileException(
                message='This resource does not contain Diagnostic Reports!'
            )
        diagnostic_reports.append(parse_diagnostic_report(resource=resource))
    return diagnostic_reports


def extract_diagnostic_report_details(file_path: str) -> dict[str, Any]:
    reports: list[DiagnosticReport]
    reports = extract_diagnostic_reports(file_path)
    patient: Patient = reports[0].patient
    return {
        'patient_info': patient.dict(),
        'diagnostic_reports': [report.dict() for report in reports]
    }


def get_observations(report_id, diagnostic_reports):
    return None


if __name__ == '__main__':
    xml_file: str = '../resources/BundleDiagnosticReports/1111111DiagnosticReport.xml'
    details: dict[str:Any] = extract_diagnostic_report_details(xml_file)
    print(details)
