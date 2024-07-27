# fhir_ui.py
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
from typing import Dict

from lxml import etree as ET

import fhir_extractor
import fhir_file_operations
from fhir_dataclasses import DiagnosticReport


class FHIRExtractorApp:
    def __init__(self, tk_root: tk.Tk) -> None:
        self.table = None
        self.entry_condition = None
        self.tree = None
        self.entry_observation = None
        self.entry_bundle = None
        self.root: tk.Tk = tk_root
        self.bundle_dir: str = ""
        self.observation_dir: str = ""
        self.condition_dir: str = ""
        self.diagnostic_reports: Dict[str, DiagnosticReport] = {}

        # Initialize instance attributes
        self.entry_bundle: tk.Entry
        self.entry_observation: tk.Entry
        self.entry_condition: tk.Entry
        self.tree: ttk.Treeview
        self.table: ttk.Treeview

        self.create_widgets()

    @staticmethod
    def _dir_frame(parent: tk.Widget, label_text: str, browse_command) -> tk.Entry:
        main_frame: tk.Frame = tk.Frame(parent)
        main_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(main_frame, text=label_text).pack(side=tk.LEFT, padx=5)
        entry = tk.Entry(main_frame)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Button(main_frame, text="Browse...", command=browse_command).pack(side=tk.LEFT, padx=5)
        return entry

    def create_widgets(self) -> None:

        # Directory selection frames
        frame: tk.Widget = self.root  # noqa
        self.entry_bundle = self._dir_frame(frame, "Bundle Directory:", self.browse_bundle_dir)
        self.entry_observation = self._dir_frame(frame, "Observation Directory:", self.browse_observation_dir)
        self.entry_condition = self._dir_frame(frame, "Condition Directory:", self.browse_condition_dir)

        # Frame for Buttons
        frame_buttons = tk.Frame(self.root)
        frame_buttons.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(frame_buttons, text="Load Bundle Files", command=self.load_bundle_files).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_buttons, text="Extract to CSV", command=self.extract_to_csv).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_buttons, text="Quit", command=self.quit).pack(side=tk.LEFT, padx=5)

        # Treeview for displaying bundle files and observations
        self.tree = ttk.Treeview(self.root, columns='Observations', show='tree')
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Table for displaying results
        self.table = ttk.Treeview(self.root,
                                  columns=("Patient Name", "Patient ID", "Observation/Condition Name", "Date", "Value"),
                                  show="headings")
        self.table.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        for col in self.table["columns"]:
            self.table.heading(col, text=col)

    def browse_bundle_dir(self) -> None:
        self.bundle_dir = filedialog.askdirectory()
        self.entry_bundle.delete(0, tk.END)
        self.entry_bundle.insert(0, self.bundle_dir)
        print(f"Selected bundle directory: {self.bundle_dir}")

    def browse_observation_dir(self) -> None:
        self.observation_dir = filedialog.askdirectory()
        self.entry_observation.delete(0, tk.END)
        self.entry_observation.insert(0, self.observation_dir)
        print(f"Selected observation directory: {self.observation_dir}")

    def browse_condition_dir(self) -> None:
        self.condition_dir = filedialog.askdirectory()
        self.entry_condition.delete(0, tk.END)
        self.entry_condition.insert(0, self.condition_dir)
        print(f"Selected condition directory: {self.condition_dir}")

    def load_bundle_files(self) -> None:
        self.tree.delete(*self.tree.get_children())

        if not self.bundle_dir:
            messagebox.showwarning("Warning", "Please select the Bundle directory.")
            return

        self.diagnostic_reports = fhir_extractor.extract_diagnostic_reports(self.bundle_dir)

        for report_id, report_data in self.diagnostic_reports.items():
            patient_name = report_data.patient_name
            report_item = self.tree.insert("", "end", text=f"Patient: {patient_name}", values=(report_id,))
            for obs in report_data.observations:
                self.tree.insert(report_item, "end", text=f"Observation: {obs.name}", values=(obs.date, obs.value))

    def extract_to_csv(self) -> None:
        if not self.bundle_dir or not self.observation_dir or not self.condition_dir:
            messagebox.showwarning("Warning", "Please select all directories.")
            return

        diagnostic_reports = fhir_extractor.extract_diagnostic_reports(self.bundle_dir)
        observations = fhir_extractor.extract_resources(self.observation_dir, 'Observation')
        conditions = fhir_extractor.extract_resources(self.condition_dir, 'Condition')
        linked_reports = fhir_extractor.link_observations_to_reports(diagnostic_reports, observations)

        # Display the results in the table
        self.display_results(linked_reports, conditions)

        # Ask where to save the CSV file
        output_csv = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if output_csv:
            fhir_file_operations.write_to_csv(linked_reports, output_csv)
            messagebox.showinfo("Info", f"Data successfully extracted to {output_csv}")

    def display_results(self, linked_reports: Dict[str, DiagnosticReport], conditions: Dict[str, ET.Element]) -> None:
        # Clear previous results
        for item in self.table.get_children():
            self.table.delete(item)

        # Add new results
        for report_data in linked_reports.values():
            patient_name = report_data.patient_name
            patient_id = report_data.patient_id
            for obs in report_data.observations:
                self.table.insert("", "end", values=(patient_name, patient_id, obs.name, obs.date, obs.value))

        for condition in conditions.values():
            condition_name, condition_date, condition_value = fhir_extractor.extract_resource_details(condition,
                                                                                                      'Condition')
            self.table.insert("", "end", values=(condition_name, condition_date, condition_value))

    def quit(self) -> None:
        self.root.quit()


if __name__ == "__main__":
    root = tk.Tk()
    app = FHIRExtractorApp(root)
    root.mainloop()
