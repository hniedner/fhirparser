# fhir_ui.py
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
from typing import Any
from typing import Dict
from typing import List

import fhir_bundle_processor
from src import observation_processor


class FHIRExtractorApp:
    def __init__(self, tk_root: tk.Tk) -> None:
        self.label_patient_name = None
        self.label_patient_id = None
        self.text_observations = None
        self.parse_button = None
        self.entry_observation_files = None
        self.observation_files = None
        self.quit = None
        self.tree = None
        self.entry_file = None
        self.root: tk.Tk = tk_root
        self.root.title("FHIR Resource Extractor")

        self.file_path: str = ""
        self.patient_info: Dict[str, str] = {}
        self.diagnostic_reports: List[Dict[str, Any]] = []
        self.sort_column = None
        self.sort_order = {}
        self.create_widgets()

    # def create_widgets(self) -> None:
    #     self.create_file_selection_frame()
    #     self.create_patient_info_frame()
    #     self.create_buttons_frame()
    #     self.create_treeview()
    #     self.create_text_widget()
    #     self.create_parse_button()

    # Update to create_widgets method
    def create_widgets(self) -> None:
        self.create_file_selection_frame()
        self.create_patient_info_frame()
        self.create_observation_file_selection_frame()
        self.create_treeview()
        self.create_text_widget()

    def create_file_selection_frame(self) -> None:
        frame_file = tk.Frame(self.root)
        frame_file.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(frame_file, text="Select Diagnostic Report Bundle XML File:").pack(side=tk.LEFT, padx=5)
        self.entry_file = tk.Entry(frame_file)
        self.entry_file.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Button(frame_file, text="Browse...", command=self.browse_file).pack(side=tk.LEFT, padx=5)

    def create_patient_info_frame(self) -> None:
        frame_patient = tk.Frame(self.root)
        frame_patient.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(frame_patient, text="Patient Name:").pack(side=tk.LEFT, padx=5)
        self.label_patient_name = tk.Label(frame_patient, text="")
        self.label_patient_name.pack(side=tk.LEFT, padx=5)

        tk.Label(frame_patient, text="Patient ID:").pack(side=tk.LEFT, padx=5)
        self.label_patient_id = tk.Label(frame_patient, text="")
        self.label_patient_id.pack(side=tk.LEFT, padx=5)

    def create_buttons_frame(self) -> None:
        frame_buttons = tk.Frame(self.root)
        frame_buttons.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(frame_buttons, text="Quit", command=self.quit).pack(side=tk.LEFT, padx=5)

    def create_treeview(self) -> None:
        columns = ("ID", "Category", "Type", "Date", "Observations Count")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", selectmode="browse")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        for col in columns:
            self.tree.heading(col, text=col, command=lambda _col=col: self.sort_by_column(_col, False))
            self.tree.column(col, width=100)

        self.tree.bind("<Double-1>", self.on_tree_select)

    def create_text_widget(self) -> None:
        self.text_observations = tk.Text(self.root, height=10)
        self.text_observations.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def create_parse_button(self) -> None:
        self.parse_button = tk.Button(self.root, text="Parse Selected Row", command=self.parse_selected_row)
        self.parse_button.pack(padx=10, pady=5)

    def browse_file(self) -> None:
        self.file_path = filedialog.askopenfilename(filetypes=[("XML files", "*.xml")])
        self.entry_file.delete(0, tk.END)
        self.entry_file.insert(0, self.file_path)
        self.extract_reports()

    def extract_reports(self) -> None:
        if not self.file_path:
            messagebox.showwarning("Warning", "Please select a file.")
            return

        try:
            result = fhir_bundle_processor.extract_diagnostic_report_details(self.file_path)
            self.patient_info = result['patient_info']
            self.diagnostic_reports = result['diagnostic_reports']
            self.display_patient_info()
            self.display_reports()
        except ValueError as e:
            self.text_observations.insert(tk.END, f"Failed to extract diagnostic reports: {e}\n")
        except Exception as e:
            self.text_observations.insert(tk.END, f"An unexpected error occurred: {e}\n")

    def display_patient_info(self) -> None:
        self.label_patient_name.config(text=self.patient_info.get('name', 'N/A'))
        self.label_patient_id.config(text=self.patient_info.get('id', 'N/A'))

    def display_reports(self) -> None:
        # Clear previous results
        for item in self.tree.get_children():
            self.tree.delete(item)

        for report in self.diagnostic_reports:
            self.tree.insert("", "end", values=(
                report['id'],
                report['category'],
                report['code'],
                report['date'],
                len(report['results'])
            ))

    def on_tree_select(self, event) -> None:
        print(event)
        selected_item = self.tree.selection()[0]
        report_id = self.tree.item(selected_item, "values")[0]
        report = next(r for r in self.diagnostic_reports if r['report_id'] == report_id)
        self.display_observations(report)

    def display_observations(self, report: Dict[str, Any]) -> None:
        self.text_observations.delete(1.0, tk.END)
        observations = report['results']

        for obs in observations:
            self.text_observations.insert(tk.END, f"Observation ID: {obs['id']}\n")
            self.text_observations.insert(tk.END, "\n")

    # def parse_selected_row(self) -> None:
    #     selected_item = self.tree.selection()
    #     if not selected_item:
    #         messagebox.showwarning("Warning", "Please select a row to parse.")
    #         return

    def parse_selected_row(self) -> None:
        selected_item = self.tree.selection()
        if not selected_item:
            self.text_observations.delete(1.0, tk.END)
            return

        report_id = self.tree.item(selected_item, "values")[0]
        report = next(r for r in self.diagnostic_reports if r['id'] == report_id)
        self.display_observations(report)

    def sort_by_column(self, col: str, descending: bool) -> None:
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children("")]
        data.sort(reverse=descending)

        for index, (val, item) in enumerate(data):
            self.tree.move(item, "", index)

        self.tree.heading(col, command=lambda: self.sort_by_column(col, not descending))

        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)

        sort_indicator = "▼" if descending else "▲"
        self.tree.heading(col, text=f"{col} {sort_indicator}")

    # New method to create the observation file selection frame
    def create_observation_file_selection_frame(self) -> None:
        frame_observation = tk.Frame(self.root)
        frame_observation.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(frame_observation, text="Select Observation Files:").pack(side=tk.LEFT, padx=5)
        self.entry_observation_files = tk.Entry(frame_observation)
        self.entry_observation_files.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Button(frame_observation, text="Browse...", command=self.browse_observation_files).pack(side=tk.LEFT, padx=5)

    # New method to handle observation file browsing
    def browse_observation_files(self) -> None:
        files = filedialog.askopenfilenames(filetypes=[("XML files", "*.xml")])
        self.entry_observation_files.delete(0, tk.END)
        self.entry_observation_files.insert(0, ';'.join(files))
        self.observation_files = files

    # Update on_tree_click method to call parse_observation_files
    def on_tree_click(self, event) -> None:
        item = self.tree.identify('item', event.x, event.y)
        if item:
            if item in self.tree.selection():
                self.tree.selection_remove(item)
                self.text_observations.delete(1.0, tk.END)
            else:
                self.tree.selection_set(item)
                self.parse_selected_row()

        selected_item = self.tree.selection()
        report_id = self.tree.item(selected_item, "values")[0]
        observations = fhir_bundle_processor.get_observations(report_id, self.diagnostic_reports)
        self.text_observations.delete(1.0, tk.END)
        for obs in observations:
            observation_details = observation_processor.parse_observation_files(obs, self.observation_files)
            self.display_observation_details(observation_details)

    # New method to display observation details
    def display_observation_details(self, details: List[Dict[str, str]]) -> None:
        for detail in details:
            self.text_observations.insert(tk.END, f"ID: {detail['id']}\n")
            self.text_observations.insert(tk.END, f"Date: {detail['date']}\n")
            self.text_observations.insert(tk.END, f"Label: {detail['label']}\n")
            self.text_observations.insert(tk.END, f"Value: {detail['value']}\n")
            self.text_observations.insert(tk.END, f"Unit: {detail['unit']}\n")
            self.text_observations.insert(tk.END, "\n")


if __name__ == "__main__":
    root = tk.Tk()
    app = FHIRExtractorApp(root)
    root.mainloop()
