from lxml import etree as ET

from src.fhir_constants import NS


def parse_xml_file(file_path: str) -> ET.Element:
    """Parse an XML file and return the root element."""
    try:
        tree: ET.ElementTree = ET.parse(file_path)
        return tree.getroot()
    except ET.XMLSyntaxError as e:
        raise ValueError(f"Error parsing XML file: {e}")


def get_attribute_value(element: ET.Element, xpath: str, attribute: str) -> str:
    """Get the attribute value of an XML element if it exists."""
    if element is not None:
        found = element.find(xpath, NS)
        if found is not None and attribute in found.attrib:
            return found.attrib[attribute]
    return 'N/A'


def parse_resource_id(full_id_ref: str) -> str:
    return full_id_ref.split('/')[-1]
