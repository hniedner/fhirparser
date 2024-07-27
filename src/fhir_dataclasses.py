# fhir_dataclasses.py
from dataclasses import dataclass
from typing import List

from lxml import etree as ET


@dataclass
class FHIRData:
    id: str
    name: str
    date: str
    value: str
    resource: ET.Element


@dataclass
class Observation:
    id: str
    name: str
    date: str
    value: str
    resource: ET.Element


@dataclass
class Condition:
    id: str
    name: str
    date: str
    value: str
    resource: ET.Element


@dataclass
class DiagnosticReport:
    id: str
    patient_id: str
    patient_name: str
    report: ET.Element
    observations: List[Observation]
