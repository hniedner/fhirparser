import os
import csv
from plistlib import InvalidFileException
from typing import List, Dict, Any
from lxml import etree as ET
from src.fhir_constants import NS
from src.utils import get_attribute_value


def parse_observation_files(file_path: str) -> List[Dict[str, Any]]:
    result_array = []
    for file in os.listdir(file_path):
        full_path = os.path.join(file_path, file)
        if os.path.isdir(full_path) or not file.endswith('.xml'):
            continue  # Skip directories and non-XML files

        try:
            tree = ET.parse(full_path)
            root: ET.Element = tree.getroot()
            observations: List[ET.Element] = root.xpath(f"//fhir:Observation", namespaces=NS)
            if not observations:
                raise InvalidFileException(
                    message='This resource does not contain Observations!'
                )
            for observation in observations:
                obs_details = extract_observation_details(observation)
                result_array.append(obs_details)

        except ET.XMLSyntaxError as e:
            print(f"Error parsing XML file {full_path}: {e}")

    return result_array


def extract_observation_details(observation: ET.Element) -> Dict[str, Any]:
    """Extract details from an Observation element."""
    return {
        'id': get_attribute_value(observation, "fhir:id", 'value'),
        'category': get_category_text(observation),
        'code': get_code_text(observation),
        'date': get_attribute_value(observation, "fhir:effectiveDateTime", 'value'),
        'value': get_value(observation),
        'unit': get_unit(observation),
        'interpretation': get_attribute_value(observation, "fhir:interpretation/fhir:text", 'value'),
        'value_string': get_attribute_value(observation, "fhir:valueString", 'value'),
        'reference_range': get_reference_range(observation),
        'subject': get_subject_details(observation)
    }


def get_category_text(observation: ET.Element) -> str:
    """Extract the category text from an Observation."""
    category = get_attribute_value(observation, "fhir:category/fhir:text", 'value')
    if category == 'N/A':
        category = get_attribute_value(observation, "fhir:category/fhir:coding/fhir:display", 'value')
    return category


def get_code_text(observation: ET.Element) -> str:
    """Extract the code text from an Observation."""
    code = get_attribute_value(observation, "fhir:code/fhir:text", 'value')
    if code == 'N/A':
        code = get_attribute_value(observation, "fhir:code/fhir:coding/fhir:display", 'value')
    return code


def get_value(observation: ET.Element) -> str:
    """Extract the value from the Observation."""
    value = get_attribute_value(observation, "fhir:valueQuantity/fhir:value", 'value')
    if value == 'N/A':
        value = get_attribute_value(observation, "fhir:valueString", 'value')
    return value


def get_unit(observation: ET.Element) -> str:
    """Extract the unit from the Observation."""
    return get_attribute_value(observation, "fhir:valueQuantity/fhir:unit", 'value')


def get_reference_range(observation: ET.Element) -> Dict[str, Any]:
    """Extract the reference range from the Observation."""
    low_value = get_attribute_value(observation, "fhir:referenceRange/fhir:low/fhir:value", 'value')
    low_unit = get_attribute_value(observation, "fhir:referenceRange/fhir:low/fhir:unit", 'value')
    high_value = get_attribute_value(observation, "fhir:referenceRange/fhir:high/fhir:value", 'value')
    high_unit = get_attribute_value(observation, "fhir:referenceRange/fhir:high/fhir:unit", 'value')

    return {
        'low': {'value': low_value, 'unit': low_unit},
        'high': {'value': high_value, 'unit': high_unit}
    }


def get_subject_details(observation: ET.Element) -> Dict[str, str]:
    """Extract the subject's name and ID from the Observation."""
    subject_name = get_attribute_value(observation, "fhir:subject/fhir:display", 'value')
    subject_id = get_attribute_value(observation, "fhir:subject/fhir:reference", 'value').split('/')[-1]
    return {'name': subject_name, 'id': subject_id}


def export_to_csv(data: List[Dict[str, Any]], output_file: str) -> None:
    """Export the observation details to a CSV file."""
    columns: list[str] =[
        'report_id', 'subject_name', 'subject_id', 'date',
        'category', 'code','value', 'unit',
        'interpretation', 'value_string',
        'reference_range_low_value', 'reference_range_low_unit',
        'reference_range_high_value', 'reference_range_high_unit'
    ]
    with open(output_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for row in data:
            writer.writerow({
                'subject_name': row['subject'].get('name', 'N/A'),
                'subject_id': row['subject'].get('id', 'N/A'),
                'report_id': row.get('id', 'N/A'),
                'category': row.get('category', 'N/A'),
                'code': row.get('code', 'N/A'),
                'date': row.get('date', 'N/A'),
                'value': row.get('value', 'N/A'),
                'unit': row.get('unit', 'N/A'),
                'interpretation': row.get('interpretation', 'N/A'),
                'value_string': row.get('value_string', 'N/A'),
                'reference_range_low_value': row['reference_range']['low'].get('value', 'N/A'),
                'reference_range_low_unit': row['reference_range']['low'].get('unit', 'N/A'),
                'reference_range_high_value': row['reference_range']['high'].get('value', 'N/A'),
                'reference_range_high_unit': row['reference_range']['high'].get('unit', 'N/A')
            })


if __name__ == '__main__':
    xml_obs_filepath: str = '../resources/Observations'
    results = parse_observation_files(file_path=xml_obs_filepath)
    # print(results)

    export_to_csv(results, output_file='observations.csv')