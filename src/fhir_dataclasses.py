# fhir_dataclasses.py
from dataclasses import asdict
from dataclasses import dataclass

@dataclass
class Base:
    id: str

    def dict(self):
        return {k: str(v) for k, v in asdict(self).items()}


@dataclass
class Patient(Base):
    name: str

@dataclass
class DiagnosticReport(Base):
    date: str
    category: str
    code: str
    performer: str
    patient: Patient
    results: list[str]


@dataclass
class Observation(Base):
    name: str
    date: str
    value: str


@dataclass
class Condition(Base):
    id: str
    name: str
    date: str
    value: str
