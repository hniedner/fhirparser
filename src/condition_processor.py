import csv
from typing import Any
from lxml import etree as ET

NS = {"fhir": "http://hl7.org/fhir"}


def parse_conditions_from_bundle_file(file_path: str) -> list[dict[str, Any]]:
    """Parse the FHIR bundle from an XML file to extract condition details."""
    conditions = []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        entries = root.findall("fhir:entry", NS)

        for entry in entries:
            condition = entry.find("fhir:resource/fhir:Condition", NS)
            if condition is not None:
                condition_details = extract_condition_details(condition)
                conditions.append(condition_details)

    except ET.XMLSyntaxError as e:
        print(f"Error parsing XML file {file_path}: {e}")

    return conditions


def extract_condition_details(condition: ET.Element) -> dict[str, Any]:
    """Extract details from a Condition resource element."""
    return {
        'id': get_attribute_value(condition, "fhir:id", 'value'),
        'patient_name': get_attribute_value(condition, "fhir:patient/fhir:display", 'value'),
        'patient_id': get_patient_id(condition),
        'asserter_name': get_attribute_value(condition, "fhir:asserter/fhir:display", 'value'),
        'asserter_id': get_asserrer_id(condition),
        'date_recorded': get_attribute_value(condition, "fhir:dateRecorded", 'value'),
        'condition_text': get_condition_text(condition),
        'condition_code': get_condition_code(condition),
        'category': get_category_text(condition),
        'clinical_status': get_attribute_value(condition, "fhir:clinicalStatus", 'value'),
        'verification_status': get_attribute_value(condition, "fhir:verificationStatus", 'value'),
        'onset_date_time': get_attribute_value(condition, "fhir:onsetDateTime", 'value')
    }


def get_attribute_value(element: ET.Element, xpath: str, attribute: str) -> str:
    """Fetches the value of a specified attribute from an XML element located by XPath."""
    found = element.find(xpath, NS)
    return found.attrib.get(attribute, 'N/A') if found is not None else 'N/A'


def get_patient_id(condition: ET.Element) -> str:
    """Extract the patient ID from the reference attribute."""
    reference = get_attribute_value(condition, "fhir:patient/fhir:reference", 'value')
    return reference.split('/')[-1] if reference != 'N/A' else 'N/A'


def get_asserrer_id(condition: ET.Element) -> str:
    """Extract the asserter ID from the reference attribute."""
    reference = get_attribute_value(condition, "fhir:asserter/fhir:reference", 'value')
    return reference.split('/')[-1] if reference != 'N/A' else 'N/A'


def get_condition_text(condition: ET.Element) -> str:
    """Extract the text description of the condition."""
    text = get_attribute_value(condition, "fhir:code/fhir:text", 'value')
    if text == 'N/A':
        text = get_attribute_value(condition, "fhir:code/fhir:coding/fhir:display", 'value')
    return text


def get_condition_code(condition: ET.Element) -> str:
    """Extract the condition code."""
    code = get_attribute_value(condition, "fhir:code/fhir:coding/fhir:code", 'value')
    return code


def get_category_text(condition: ET.Element) -> str:
    """Extract the category text of the condition."""
    category = get_attribute_value(condition, "fhir:category/fhir:text", 'value')
    if category == 'N/A':
        category = get_attribute_value(condition, "fhir:category/fhir:coding/fhir:display", 'value')
    return category


def export_conditions_to_csv(conditions: list[dict[str, Any]], output_file: str) -> None:
    """Export the condition details to a CSV file."""
    with open(output_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=[
            'id', 'patient_name', 'patient_id', 'asserter_name', 'asserter_id',
            'date_recorded', 'condition_text', 'condition_code', 'category',
            'clinical_status', 'verification_status', 'onset_date_time'
        ])
        writer.writeheader()
        for condition in conditions:
            writer.writerow(condition)


if __name__ == "__main__":
    # Load the FHIR bundle from an XML file
    xml_file_path = "../resources/Conditions/1111111_Conditions_Diagnosis.xml"
    results = parse_conditions_from_bundle_file(xml_file_path)

    # Export the parsed conditions to a CSV file
    output_csv = 'conditions.csv'
    export_conditions_to_csv(results, output_csv)
    print(f"Results exported to {output_csv}")