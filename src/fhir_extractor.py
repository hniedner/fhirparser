# fhir_extractor.py
import os
from typing import Dict

from lxml import etree as ET

from fhir_constants import FHIR_CLINICAL_STATUS
from fhir_constants import FHIR_CODE_TEXT
from fhir_constants import FHIR_EFFECTIVE_DATETIME
from fhir_constants import FHIR_ID
from fhir_constants import FHIR_RECORDED_DATE
from fhir_constants import FHIR_RESULT
from fhir_constants import FHIR_SUBJECT_DISPLAY
from fhir_constants import FHIR_SUBJECT_REFERENCE
from fhir_constants import FHIR_VALUE_QUANTITY
from fhir_constants import NS
from fhir_dataclasses import DiagnosticReport
from fhir_dataclasses import Observation


def parse_xml_file(file_path: str) -> ET.Element:
    """Parse an XML file and return the root element."""
    tree: ET.ElementTree = ET.parse(file_path)
    return tree.getroot()


def extract_resources(directory: str, resource_type: str) -> Dict[str, ET.Element]:
    """Extract specified resources from XML files in a directory."""
    resources: Dict[str, ET.Element] = {}

    for filename in os.listdir(directory):
        if filename.endswith('.xml'):
            file_path: str = os.path.join(directory, filename)
            root: ET.Element = parse_xml_file(file_path)
            resource: ET.Element = root.find(f'.//fhir:{resource_type}', NS)
            if resource is not None:
                resource_id: str = resource.find(FHIR_ID, NS).attrib['value']
                resources[resource_id] = resource

    return resources


def extract_diagnostic_reports(bundle_dir: str) -> Dict[str, DiagnosticReport]:
    """Extract DiagnosticReport resources from Bundle files."""
    diagnostic_reports: Dict[str, DiagnosticReport] = {}

    for filename in os.listdir(bundle_dir):
        if filename.endswith('.xml'):
            file_path: str = os.path.join(bundle_dir, filename)
            root: ET.Element = parse_xml_file(file_path)

            for entry in root.findall('.//fhir:entry', NS):
                resource: ET.Element = entry.find('.//fhir:DiagnosticReport', NS)
                if resource is not None:
                    report_id: str = resource.find(FHIR_ID, NS).attrib['value']
                    patient_id: str = resource.find(FHIR_SUBJECT_REFERENCE, NS).attrib['value']
                    patient_name: str = resource.find(FHIR_SUBJECT_DISPLAY, NS).text
                    diagnostic_reports[report_id] = DiagnosticReport(
                        id=report_id,
                        patient_id=patient_id,
                        patient_name=patient_name,
                        report=resource,
                        observations=[]
                    )

    return diagnostic_reports


def link_observations_to_reports(
        diagnostic_reports: Dict[str, DiagnosticReport],
        observations: Dict[str, ET.Element]
) -> Dict[str, DiagnosticReport]:
    """Link Observation resources to DiagnosticReport resources."""
    for report_data in diagnostic_reports.values():
        report: ET.Element = report_data.report
        for reference in report.findall(FHIR_RESULT, NS):
            obs_ref: str = reference.attrib['value']
            obs_id: str = obs_ref.split('/')[-1]
            if obs_id in observations:
                obs_element: ET.Element = observations[obs_id]
                obs_name, obs_date, obs_value = extract_resource_details(obs_element, 'Observation')
                observation = Observation(
                    id=obs_id,
                    name=obs_name,
                    date=obs_date,
                    value=obs_value,
                    resource=obs_element
                )
                report_data.observations.append(observation)

    return diagnostic_reports


def extract_resource_details(resource: ET.Element, resource_type: str) -> tuple[str, str, str]:
    """Extract details from a specified resource."""
    if resource_type == 'Observation':
        name: str = resource.find(FHIR_CODE_TEXT, NS).text
        date: str = resource.find(FHIR_EFFECTIVE_DATETIME, NS).text
        value: str = resource.find(FHIR_VALUE_QUANTITY, NS).attrib['value']
    elif resource_type == 'Condition':
        name: str = resource.find(FHIR_CODE_TEXT, NS).text
        date: str = resource.find(FHIR_RECORDED_DATE, NS).text
        value: str = resource.find(FHIR_CLINICAL_STATUS, NS).text
    else:
        raise ValueError(f"Unsupported resource type: {resource_type}")

    return name, date, value
