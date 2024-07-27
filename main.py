import csv
import os
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union

from lxml import etree as ET

# Define namespaces
FHIR_NS = 'http://hl7.org/fhir'
NS = {'fhir': FHIR_NS}


class FHIRExtractorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("FHIR Resource Extractor")

        self.bundle_dir: str = ""
        self.observation_dir: str = ""

        self.diagnostic_reports: Dict[str, Dict[str, Union[str, List[ET.Element]]]] = {}

        self.create_widgets()

    def create_widgets(self) -> None:
        # Frame for Bundle directory selection
        frame_bundle = tk.Frame(self.root)
        frame_bundle.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(frame_bundle, text="Bundle Directory:").pack(side=tk.LEFT, padx=5)
        self.entry_bundle = tk.Entry(frame_bundle)
        self.entry_bundle.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Button(frame_bundle, text="Browse...", command=self.browse_bundle_dir).pack(side=tk.LEFT, padx=5)

        # Frame for Observation directory selection
        frame_observation = tk.Frame(self.root)
        frame_observation.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(frame_observation, text="Observation Directory:").pack(side=tk.LEFT, padx=5)
        self.entry_observation = tk.Entry(frame_observation)
        self.entry_observation.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Button(frame_observation, text="Browse...", command=self.browse_observation_dir).pack(side=tk.LEFT, padx=5)

        # Frame for Buttons
        frame_buttons = tk.Frame(self.root)
        frame_buttons.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(frame_buttons, text="Load Bundle Files", command=self.load_bundle_files).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_buttons, text="Extract to CSV", command=self.extract_to_csv).pack(side=tk.LEFT, padx=5)

        # Treeview for displaying bundle files and observations
        self.tree = ttk.Treeview(self.root, columns=("Observations"), show='tree')
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Table for displaying results
        self.table = ttk.Treeview(self.root, columns=(
            "Patient Name", "Patient ID", "Observation Name", "Date of Observation", "Value"), show="headings")
        self.table.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        for col in self.table["columns"]:
            self.table.heading(col, text=col)

    def browse_bundle_dir(self) -> None:
        self.bundle_dir = filedialog.askdirectory()
        self.entry_bundle.delete(0, tk.END)
        self.entry_bundle.insert(0, self.bundle_dir)

    def browse_observation_dir(self) -> None:
        self.observation_dir = filedialog.askdirectory()
        self.entry_observation.delete(0, tk.END)
        self.entry_observation.insert(0, self.observation_dir)

    def load_bundle_files(self) -> None:
        self.tree.delete(*self.tree.get_children())

        if not self.bundle_dir:
            messagebox.showwarning("Warning", "Please select the Bundle directory.")
            return

        self.diagnostic_reports = extract_diagnostic_reports(self.bundle_dir)

        for report_id, report_data in self.diagnostic_reports.items():
            patient_name = report_data['patient_name']
            report_item = self.tree.insert("", "end", text=f"Patient: {patient_name}", values=(report_id,))
            for obs in report_data['observations']:
                obs_name, obs_date, obs_value = extract_observation_details(obs)
                self.tree.insert(report_item, "end", text=f"Observation: {obs_name}", values=(obs_date, obs_value))

    def extract_to_csv(self) -> None:
        if not self.bundle_dir or not self.observation_dir:
            messagebox.showwarning("Warning", "Please select both directories.")
            return

        diagnostic_reports = extract_diagnostic_reports(self.bundle_dir)
        observations = extract_observations(self.observation_dir)
        linked_reports = link_observations_to_reports(diagnostic_reports, observations)

        # Display the results in the table
        self.display_results(linked_reports)

        # Ask where to save the CSV file
        output_csv = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if output_csv:
            write_to_csv(linked_reports, output_csv)
            messagebox.showinfo("Info", f"Data successfully extracted to {output_csv}")

    def display_results(self, linked_reports: Dict[str, Dict[str, Union[str, List[ET.Element]]]]) -> None:
        # Clear previous results
        for item in self.table.get_children():
            self.table.delete(item)

        # Add new results
        for report_id, report_data in linked_reports.items():
            patient_name = report_data['patient_name']  # type: ignore
            patient_id = report_data['patient_id']  # type: ignore
            for obs in report_data['observations']:  # type: ignore
                obs_name, obs_date, obs_value = extract_observation_details(obs)
                self.table.insert("", "end", values=(patient_name, patient_id, obs_name, obs_date, obs_value))


def parse_xml_file(file_path: str) -> ET.Element:
    """Parse an XML file and return the root element."""
    tree: ET.ElementTree = ET.parse(file_path)
    return tree.getroot()


def extract_diagnostic_reports(bundle_dir: str) -> Dict[str, Dict[str, Union[str, List[ET.Element]]]]:
    """Extract DiagnosticReport resources from Bundle files."""
    diagnostic_reports: Dict[str, Dict[str, Union[str, List[ET.Element]]]] = {}

    for filename in os.listdir(bundle_dir):
        if filename.endswith('.xml'):
            file_path: str = os.path.join(bundle_dir, filename)
            root: ET.Element = parse_xml_file(file_path)

            for entry in root.findall('.//fhir:entry', NS):
                resource: ET.Element = entry.find('.//fhir:DiagnosticReport', NS)
                if resource is not None:
                    report_id: str = resource.find('.//fhir:id', NS).attrib['value']
                    patient_id: str = resource.find('.//fhir:subject/fhir:reference', NS).attrib['value']
                    patient_name: str = resource.find('.//fhir:subject/fhir:display', NS).text
                    diagnostic_reports[report_id] = {
                        'patient_id': patient_id,
                        'patient_name': patient_name,
                        'report': resource,
                        'observations': []
                    }

    return diagnostic_reports


def extract_observations(observation_dir: str) -> Dict[str, ET.Element]:
    """Extract Observation resources from individual XML files."""
    observations: Dict[str, ET.Element] = {}

    for filename in os.listdir(observation_dir):
        if filename.endswith('.xml'):
            file_path: str = os.path.join(observation_dir, filename)
            root: ET.Element = parse_xml_file(file_path)
            resource: ET.Element = root.find('.//fhir:Observation', NS)
            if resource is not None:
                observation_id: str = resource.find('.//fhir:id', NS).attrib['value']
                observations[observation_id] = resource

    return observations


def link_observations_to_reports(
        diagnostic_reports: Dict[str, Dict[str, Union[str, List[ET.Element]]]],
        observations: Dict[str, ET.Element]
) -> Dict[str, Dict[str, Union[str, List[ET.Element]]]]:
    """Link Observation resources to DiagnosticReport resources."""
    for report_id, report_data in diagnostic_reports.items():
        report: ET.Element = report_data['report']  # type: ignore
        for reference in report.findall('.//fhir:result', NS):
            obs_ref: str = reference.attrib['value']
            obs_id: str = obs_ref.split('/')[-1]
            if obs_id in observations:
                diagnostic_reports[report_id]['observations'].append(observations[obs_id])  # type: ignore

    return diagnostic_reports


def extract_observation_details(observation: ET.Element) -> Tuple[str, str, str]:
    """Extract details from an Observation resource."""
    obs_name: str = observation.find('.//fhir:code/fhir:text', NS).text
    obs_date: str = observation.find('.//fhir:effectiveDateTime', NS).text
    obs_value: str = observation.find('.//fhir:valueQuantity/fhir:value', NS).attrib['value']

    return obs_name, obs_date, obs_value


def write_to_csv(
        diagnostic_reports: Dict[str, Dict[str, Union[str, List[ET.Element]]]],
        output_csv: str
) -> None:
    """Write extracted data to a CSV file."""
    with open(output_csv, mode='w', newline='') as csvfile:
        csv_writer: csv.writer = csv.writer(csvfile)
        csv_writer.writerow(['Patient Name', 'Patient ID', 'Observation Name', 'Date of Observation', 'Value'])

        for report_id, report_data in diagnostic_reports.items():
            patient_name: str = report_data['patient_name']  # type: ignore
            patient_id: str = report_data['patient_id']  # type: ignore
            for obs in report_data['observations']:  # type: ignore
                obs_name, obs_date, obs_value = extract_observation_details(obs)
                csv_writer.writerow([patient_name, patient_id, obs_name, obs_date, obs_value])


if __name__ == "__main__":
    print("Starting application...")
    root = tk.Tk()
    app = FHIRExtractorApp(root)
    root.mainloop()
    print("Application ended.")
