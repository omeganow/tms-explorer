from __future__ import annotations
from datetime import datetime

import hashlib
import xlsxwriter
import json
import os

from PyQt6 import QtCore, QtGui, QtWidgets

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QPushButton,
    QListWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QCheckBox,
    QLabel,
    QDoubleSpinBox,
    QTableWidget,
    QFileDialog,
)
from PyQt6 import uic
import qdarkstyle

import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("QtAgg")
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure

from tms_data import TmsPatient, TmsPlotObject, TmsMeasurement
from tms_regression import RegressionModels, RegressionMode, TmsLogger


class TmsUi(QtWidgets.QMainWindow):
    """Main UI Component for the main window for organizing all the UI-components"""

    app: QtWidgets.QApplication

    theme: qdarkstyle.Palette
    themeselector: QComboBox

    patient: TmsPatientExplorer
    inspector: TmsInspector
    overview: TmsOverview

    si1mv_plots: TmsSi1mvPlots
    recr_plots: TmsRecrPlots
    ici_plots: TmsIciPlots
    lici_plots: TmsLiciPlots

    tabViewer: QtWidgets.QTabWidget

    progress_bar: QtWidgets.QProgressBar
    progress_label: QLabel

    active_ui_components: list[TmsUiComponent] = []

    def __init__(self, app: QtWidgets.QApplication, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.app = app
        uic.loadUi("./src/tms_explorer.ui", self)
        self.setWindowTitle("TmsExplorer")

        pixmap = QtGui.QPixmap(100, 100)
        pixmap.fill((QtGui.QColor("white")))
        self.setWindowIcon(QtGui.QIcon(pixmap))

        # Basic Ui Features
        self.tabViewer = self.findChild(QtWidgets.QTabWidget, "dataExplorer")
        self.tabViewer.currentChanged.connect(self.tab_changed)
        self.progress_bar = self.findChild(QtWidgets.QProgressBar, "progressBar")
        self.progress_label = self.findChild(QLabel, "progressLabel")
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)

        # Theme Engine
        self.themeselector: QComboBox = self.findChild(
            QtWidgets.QComboBox, "mainThemeBox"
        )
        self.themeselector.addItems(["light", "dark"])
        self.themeselector.setCurrentIndex(0)
        self.themeselector.currentIndexChanged.connect(self.theme_change)
        self.theme_change()

        # Main UI Parts
        self.patient = TmsPatientExplorer(self)
        self.active_ui_components.append(self.patient)
        self.inspector = TmsInspector(self)
        self.active_ui_components.append(self.inspector)
        self.overview = TmsOverview(self)
        self.active_ui_components.append(self.overview)
        self.si1mv_plots = TmsSi1mvPlots(self)
        self.active_ui_components.append(self.si1mv_plots)
        self.recr_plots = TmsRecrPlots(self)
        self.active_ui_components.append(self.recr_plots)
        self.ici_plots = TmsIciPlots(self)
        self.active_ui_components.append(self.ici_plots)
        self.lici_plots = TmsLiciPlots(self)
        self.active_ui_components.append(self.lici_plots)
        TmsLogger().set_label(self)

        QtCore.QTimer.singleShot(500, self.update)

    def update(self):
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(len(self.active_ui_components))
        for progress, item in enumerate(self.active_ui_components):
            self.progress_label.setText(f"Updating: {item.__class__.__name__}")
            TmsLogger().log(self.progress_label.text())
            item.update()
            self.progress_bar.setValue(progress)
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        TmsLogger().log("Done...")

    def tab_changed(self):
        self.update()

    def theme_change(self):
        if self.themeselector.currentText() == "light":
            self.theme = qdarkstyle.LightPalette
            plt.style.use("default")

        elif self.themeselector.currentText() == "dark":
            self.theme = qdarkstyle.DarkPalette
            plt.style.use("dark_background")
            matplotlib.rcParams["axes.facecolor"] = "white"


class TmsUiComponent:
    ui: TmsUi

    def __init__(self, ui: TmsUi) -> None:
        self.ui = ui

    def update(self):
        """Needs to be implemented by each Child"""
        pass


class TmsPatientExplorer(TmsUiComponent):
    """Main UI Component to browse a folder with tmsData select patient and export
    the data as JSON or XLS"""

    ui: TmsUi

    data: TmsPatient = None

    selected_patient: str = ""
    path_to_folder: str = "./"

    # UI Components
    patient_list: QListWidget
    patient_reload_btn: QPushButton
    patient_label: QLabel
    patient_import_report: QtWidgets.QTextBrowser

    # Export
    path_show: QtWidgets.QLineEdit
    browse_btn: QPushButton
    export_all_xls_btn: QPushButton
    export_all_json_btn: QPushButton

    # Start End Time
    si1mv_start: QDoubleSpinBox
    si1mv_end: QDoubleSpinBox

    recr_start: QDoubleSpinBox
    recr_end: QDoubleSpinBox

    ici_start: QDoubleSpinBox
    ici_end: QDoubleSpinBox

    lici_start: QDoubleSpinBox
    lici_end: QDoubleSpinBox

    regression_model: QComboBox

    def __init__(self, ui: TmsUi) -> None:
        super().__init__(ui)

        self.patient_list = self.ui.findChild(QListWidget, "patientExplorer")
        self.patient_list.clicked.connect(self.get_selected_patient)

        self.patient_reload_btn = self.ui.findChild(QPushButton, "patientReload")
        self.patient_reload_btn.clicked.connect(self.update)

        self.patient_label = self.ui.findChild(QLabel, "patientLabelChanger")
        self.patient_import_report = self.ui.findChild(
            QtWidgets.QTextBrowser, "patientImportReport"
        )
        self.update()

        # Export
        self.export_all_xls_btn = self.ui.findChild(QPushButton, "patientExportAllXls")
        self.export_all_xls_btn.clicked.connect(self.export_all_xls)

        self.export_all_json_btn = self.ui.findChild(
            QPushButton, "patientExportAllJson"
        )
        self.export_all_json_btn.clicked.connect(self.export_all_json)

        self.browse_btn = self.ui.findChild(QPushButton, "patientBrowseButton")
        self.browse_btn.clicked.connect(self.browse_path)

        self.path_show = self.ui.findChild(QtWidgets.QLineEdit, "patientPathShow")
        self.path_show.setText(self.path_to_folder)
        self.path_show.textChanged.connect(self.manuel_path_change)

        # Regression Model
        self.regression_model = self.ui.findChild(QComboBox, "patientRegressionModel")
        for enum_choice in RegressionModels:
            self.regression_model.addItem(enum_choice.name)
        self.regression_model.setCurrentText(
            RegressionMode().selected_regression_model.name
        )
        self.regression_model.currentTextChanged.connect(self.regression_selection)

        # Double Spin Boxes
        self.si1mv_start = self.ui.findChild(QDoubleSpinBox, "patientSi1mvStart")
        self.si1mv_end = self.ui.findChild(QDoubleSpinBox, "patientSi1mvEnd")
        self.recr_start = self.ui.findChild(QDoubleSpinBox, "patientRecrStart")
        self.recr_end = self.ui.findChild(QDoubleSpinBox, "patientRecrEnd")
        self.ici_start = self.ui.findChild(QDoubleSpinBox, "patientIciStart")
        self.ici_end = self.ui.findChild(QDoubleSpinBox, "patientIciEnd")
        self.lici_start = self.ui.findChild(QDoubleSpinBox, "patientLiciStart")
        self.lici_end = self.ui.findChild(QDoubleSpinBox, "patientLiciEnd")
        self.connect_callbacks_sliders()
        self.load_config()

    def update(self):
        temp_patient_list = [
            self.patient_list.item(x).text() for x in range(self.patient_list.count())
        ]
        temp_selected_row = self.patient_list.currentRow()

        self.patient_list.clear()
        folder_list = []
        for folder in os.listdir(self.path_to_folder):
            if os.path.isdir(f"{self.path_to_folder}/{folder}"):
                if folder.startswith("F0"):
                    folder_list.append(folder)
        self.patient_list.addItems(folder_list)

        if temp_patient_list == [
            self.patient_list.item(x).text() for x in range(self.patient_list.count())
        ]:
            self.patient_list.setCurrentRow(temp_selected_row)
        else:
            self.patient_list.setCurrentRow(0)
            self.get_selected_patient()

    def connect_callbacks_sliders(self):
        self.si1mv_start.valueChanged.connect(self.update_config)
        self.si1mv_end.valueChanged.connect(self.update_config)
        self.recr_start.valueChanged.connect(self.update_config)
        self.recr_end.valueChanged.connect(self.update_config)
        self.ici_start.valueChanged.connect(self.update_config)
        self.ici_end.valueChanged.connect(self.update_config)
        self.lici_start.valueChanged.connect(self.update_config)
        self.lici_end.valueChanged.connect(self.update_config)

    def disconnect_callbacks_sliders(self):
        self.si1mv_start.valueChanged.disconnect(self.update_config)
        self.si1mv_end.valueChanged.disconnect(self.update_config)
        self.recr_start.valueChanged.disconnect(self.update_config)
        self.recr_end.valueChanged.disconnect(self.update_config)
        self.ici_start.valueChanged.disconnect(self.update_config)
        self.ici_end.valueChanged.disconnect(self.update_config)
        self.lici_start.valueChanged.disconnect(self.update_config)
        self.lici_end.valueChanged.disconnect(self.update_config)

    def default_config(self):
        default = {
            "s1mv_start": 0.10,
            "s1mv_stop": 0.13,
            "recr_start": 0.1,
            "recr_stop": 0.13,
            "ici_start": 0.1,
            "ici_stop": 0.13,
            "lici_start": 0.26,
            "lici_stop": 0.3,
            "regression": "Cubic",
        }
        file = open("./config.cf", "w")
        json.dump(default, file)
        file.close()

    def load_config(self):
        self.disconnect_callbacks_sliders()
        self.regression_model.currentTextChanged.disconnect(self.regression_selection)
        if not os.path.isfile("./config.cf"):
            self.default_config()

        try:
            file = open("./config.cf")
            config_file = json.load(file)
            file.close()
        except:
            self.default_config()
            file = open("./config.cf")
            config_file = json.load(file)
            file.close()

        self.si1mv_start.setValue(config_file["s1mv_start"])
        self.si1mv_end.setValue(config_file["s1mv_stop"])
        self.recr_start.setValue(config_file["recr_start"])
        self.recr_end.setValue(config_file["recr_stop"])
        self.ici_start.setValue(config_file["ici_start"])
        self.ici_end.setValue(config_file["ici_stop"])
        self.lici_start.setValue(config_file["lici_start"])
        self.lici_end.setValue(config_file["lici_stop"])
        self.regression_model.setCurrentText(config_file["regression"])
        self.regression_selection(False)

        self.connect_callbacks_sliders()
        self.regression_model.currentTextChanged.connect(self.regression_selection)

    def update_config(self):
        config_file = {}
        config_file["s1mv_start"] = self.si1mv_start.value()
        config_file["s1mv_stop"] = self.si1mv_end.value()
        config_file["recr_start"] = self.recr_start.value()
        config_file["recr_stop"] = self.recr_end.value()
        config_file["ici_start"] = self.ici_start.value()
        config_file["ici_stop"] = self.ici_end.value()
        config_file["lici_start"] = self.lici_start.value()
        config_file["lici_stop"] = self.lici_end.value()
        config_file["regression"] = self.regression_model.currentText()

        file = open("./config.cf", "w")
        json.dump(config_file, file)
        file.close()
        self.load_config()

    def regression_selection(self, trigger_update=True):
        current_text = self.regression_model.currentText()
        if current_text == "Cubic":
            RegressionMode().selected_regression_model = RegressionModels.Cubic
        elif current_text == "Logistic":
            RegressionMode().selected_regression_model = RegressionModels.Logistic
        elif current_text == "Gombertz":
            RegressionMode().selected_regression_model = RegressionModels.Gombertz
        elif current_text == "Reverse Gombertz":
            RegressionMode().selected_regression_model = (
                RegressionModels.ReverseGombertz
            )
        elif current_text == "Boltzmann":
            RegressionMode().selected_regression_model = RegressionModels.Boltzmann
        if trigger_update:
            self.update_config()
            self.ui.update()

    def browse_path(self):
        dirname = ""
        dirname = QFileDialog.getExistingDirectory(
            self.ui, "Select Folder with TmsPatien Data", self.path_to_folder
        )
        if dirname != "":
            self.path_to_folder = dirname
            self.path_show.setText(self.path_to_folder)
            self.update()

    def manuel_path_change(self):
        if os.path.isdir(self.path_show.text()):
            self.path_to_folder = self.path_show.text()

    def export_all_xls(self):
        if not self.ui.patient.data:
            return

        filename = ""
        filename = QFileDialog.getSaveFileName(
            self.ui,
            "Select where to export Data",
            "export_all_patients.xlsx",
            "*.xlsx",
        )

        self.ui.progress_bar.setVisible(True)
        self.ui.progress_label.setVisible(True)
        self.ui.progress_bar.setMinimum(0)
        self.ui.progress_bar.setMaximum(self.patient_list.count())

        if filename[0] != "":
            path_to_write = filename[0]
            if ".xls" not in path_to_write:
                path_to_write = path_to_write + ".xlsx"

            xlxfile = xlsxwriter.Workbook(path_to_write)
            si1mv_table = xlxfile.add_worksheet("SI1mv")
            si1mv_table.set_column(0, 0, 20)
            si1mv_table.write(1, 0, "Patient_No")
            si1mv_table.write(1, 1, "BA (MEP)")
            si1mv_table.write(1, 2, "PM (MEP)")
            si1mv_table.write(1, 3, "AC (MEP)")
            si1mv_table.write(1, 4, "LT (MEP)")

            recr_table = xlxfile.add_worksheet("RECR")
            recr_table.set_column(0, 0, 20)
            recr_table.write(1, 0, "Patient_No")
            for count, session in enumerate(["BA", "PM", "AC", "LT"]):
                offset = count * 9
                recr_table.write(0, 1 + offset, session)
                recr_table.write(1, 1 + offset, "90% RMT")
                recr_table.write(1, 2 + offset, "100% RMT")
                recr_table.write(1, 3 + offset, "110% RMT")
                recr_table.write(1, 4 + offset, "120% RMT")
                recr_table.write(1, 5 + offset, "130% RMT")
                recr_table.write(1, 6 + offset, "140% RMT")
                recr_table.write(1, 7 + offset, "S50")
                recr_table.write(1, 8 + offset, "Slope ( S50 )")
                recr_table.write(1, 9 + offset, "%RMT ( S50 )")

            ici_table = xlxfile.add_worksheet("ICI")
            ici_table.set_column(0, 0, 20)
            ici_table.set_column("B:M", 12)
            ici_table.write(1, 0, "Patient_No")
            for count, session in enumerate(["BA", "PM", "AC", "LT"]):
                offset = count * 3
                ici_table.write(0, 1 + offset, session)
                ici_table.write(1, 1 + offset, "State 1 (MEP)")
                ici_table.write(1, 2 + offset, "State 2 (MEP)")
                ici_table.write(1, 3 + offset, "State 3 (MEP)")

            lici_table = xlxfile.add_worksheet("LICI")
            lici_table.set_column(0, 0, 20)
            lici_table.set_column("B:Q", 12)
            lici_table.write(1, 0, "Patient_No")
            for count, session in enumerate(["BA", "PM", "AC", "LT"]):
                offset = count * 4
                lici_table.write(0, 1 + offset, session)
                lici_table.write(1, 1 + offset, "State 1 (MEP)")
                lici_table.write(1, 2 + offset, "State 2 (MEP)")
                lici_table.write(1, 3 + offset, "State 3 (MEP)")
                lici_table.write(1, 4 + offset, "State 2_3 (MEP)")

            row = 2
            for progress in range(0, self.patient_list.count()):
                patient_name = self.patient_list.item(progress).text()

                self.ui.progress_label.setText(f"Exporting: Patient {patient_name} ")
                self.ui.progress_bar.setValue(progress)

                patient = TmsPatient(patient_name, self.path_to_folder)
                data = patient.export_data()[patient_name]

                si1mv_table.write(row, 0, patient_name)
                recr_table.write(row, 0, patient_name)
                ici_table.write(row, 0, patient_name)
                lici_table.write(row, 0, patient_name)

                column_offsets = {"ba": 0, "pm": 1, "ac": 2, "lt": 3}
                for session in data:
                    column = column_offsets[session] + 1

                    if data[session].get("si1mv"):
                        si1mv_table.write(row, column, data[session]["si1mv"]["mep"])

                    if data[session].get("recr"):
                        for idx, item in enumerate(data[session]["recr"]):
                            recr_column = ((column - 1) * 9) + 1
                            if item != -99999:
                                recr_table.write(row, recr_column + idx, item)

                    if data[session].get("ici"):
                        for idx, item in enumerate(data[session]["ici"]):
                            ici_column = ((column - 1) * 3) + 1
                            ici_table.write(row, ici_column + idx, item)

                    if data[session].get("lici"):
                        for idx, item in enumerate(data[session]["lici"]):
                            lici_column = ((column - 1) * 4) + 1
                            lici_table.write(row, lici_column + idx, item)
                row += 1
            xlxfile.close()

        self.ui.progress_bar.setVisible(False)
        self.ui.progress_label.setVisible(False)
        TmsLogger().log("Done...")

    def export_all_json(self):
        if not self.ui.patient.data:
            return

        filename = ""
        filename = QFileDialog.getSaveFileName(
            self.ui,
            "Select where to export Data",
            "export_all_patients.json",
            "*.json",
        )

        self.ui.progress_bar.setVisible(True)
        self.ui.progress_label.setVisible(True)
        self.ui.progress_bar.setMinimum(0)
        self.ui.progress_bar.setMaximum(self.patient_list.count())

        if filename[0] != "":
            path_to_write = filename[0]
            if ".json" not in path_to_write:
                path_to_write = path_to_write + ".json"

            export = {}
            for progress in range(0, self.patient_list.count()):
                patient_name = self.patient_list.item(progress).text()

                self.ui.progress_label.setText(f"Exporting: Patient {patient_name} ")
                self.ui.progress_bar.setValue(progress)

                patient = TmsPatient(patient_name, self.path_to_folder)
                export[patient_name] = patient.export_data()[patient_name]

            with open(path_to_write, "w") as file:
                json.dump(export, file, indent=5)

        self.ui.progress_bar.setVisible(False)
        self.ui.progress_label.setVisible(False)
        TmsLogger().log("Done...")

    def load_tms_patient(self):
        start = datetime.now()
        self.data = TmsPatient(self.selected_patient, self.path_to_folder)
        print(f"Patient {self.data.subject_name} loaded")
        self.patient_label.setText(self.data.subject_name)
        import_report_text = ""
        for line in self.data.import_report:
            import_report_text += line + "\n"
        self.patient_import_report.setText(import_report_text)
        print(datetime.now() - start)

    def get_selected_patient(self):
        temp_patient = self.selected_patient
        for item in self.patient_list.selectedItems():
            self.selected_patient = item.text()

        if temp_patient != self.selected_patient:
            self.load_tms_patient()
            self.ui.update()


class TmsInspector(TmsUiComponent):
    """Tabview for the Frameinspector functionality here frames can be previewed
    and can be rejected from here"""

    sessions: QListWidget
    types: QListWidget
    frames: QListWidget

    session_filter: str
    type_filter: str
    selected_frame: int = 0

    next_frame_btn: QPushButton
    previous_frame_btn: QPushButton
    plot_view: QVBoxLayout

    reject_check_box: QCheckBox
    show_rejected_box: QCheckBox
    show_rejected: bool = True
    only_inspection_needed_box: QCheckBox
    only_inspection_needed: bool = False

    canvas: MplCanvas
    canvas_toolbar: NavigationToolbar

    def __init__(self, ui: TmsUi) -> None:
        super().__init__(ui)

        ### Plot Area
        self.canvas = MplCanvas(self)
        self.canvas_toolbar = NavigationToolbar(self.canvas, self.ui, coordinates=False)

        self.plot_view = self.ui.findChild(QVBoxLayout, "inspPlotTarget")
        self.plot_view.addWidget(self.canvas)

        self.plot_navigation = self.ui.findChild(QHBoxLayout, "inspPlotNavigation")
        self.plot_navigation.addWidget(self.canvas_toolbar)

        ### Buttons
        self.next_frame_btn = self.ui.findChild(QtWidgets.QPushButton, "inspNextFrame")
        self.next_frame_btn.clicked.connect(self.next_frame)

        self.previous_frame_btn = self.ui.findChild(QPushButton, "inspPrevFrame")
        self.previous_frame_btn.clicked.connect(self.prev_frame)

        ### Lists
        self.sessions = self.ui.findChild(QListWidget, "inspSessionList")
        self.sessions.clicked.connect(self.session_changed)
        self.initiate_sessions()

        self.types = self.ui.findChild(QListWidget, "inspMeasurementTypeList")
        self.types.clicked.connect(self.type_changed)
        self.initiate_types()

        self.frames = self.ui.findChild(QListWidget, "inspFrameSelectList")
        self.frames.clicked.connect(self.frameselection_changed)

        ### Check Boxes
        self.reject_check_box = self.ui.findChild(QCheckBox, "inspRejectCheck")
        self.reject_check_box.stateChanged.connect(self.reject_frame)
        self.show_rejected_box = self.ui.findChild(QCheckBox, "inspShowRejected")
        self.show_rejected_box.stateChanged.connect(self.show_rejected_changed)
        self.show_rejected_box.setCheckState(Qt.CheckState.Checked)
        self.only_inspection_needed_box = self.ui.findChild(
            QCheckBox, "inspOnlyInspectionNeeded"
        )
        self.only_inspection_needed_box.stateChanged.connect(
            self.show_inspection_only_changed
        )

    def update(self):
        if not self.ui.patient.data:
            return

        self.initiate_sessions()
        self.initiate_types()

        theme_change_update = False
        if self.canvas.theme != self.ui.themeselector.currentText():
            self.plot_view.removeWidget(self.canvas)
            self.plot_navigation.removeWidget(self.canvas_toolbar)

            self.canvas = MplCanvas(self)
            self.canvas_toolbar = NavigationToolbar(
                self.canvas, self.ui, coordinates=False
            )

            if self.canvas.theme == "dark":
                self.canvas_toolbar.setStyleSheet("color:white;")

            self.plot_view.addWidget(self.canvas)
            self.plot_navigation.addWidget(self.canvas_toolbar)
            theme_change_update = True

        temp_frames_list = [
            self.frames.item(x).text() for x in range(self.frames.count())
        ]
        temp_selected_row = self.frames.currentRow()

        self.frames.clear()
        for frame in self.ui.patient.data.measurement_data[self.session_filter][
            self.type_filter
        ].frames:
            frameItem = QtWidgets.QListWidgetItem(str(frame.number))
            if frame.rejected and self.show_rejected:
                frameItem.setBackground(QtGui.QColor.fromRgb(245, 66, 66))
                self.frames.addItem(frameItem)
            elif frame.inspection_needed and not frame.rejected:
                frameItem.setBackground(QtGui.QColor.fromRgb(245, 203, 66))
                self.frames.addItem(frameItem)
            else:
                if not self.only_inspection_needed:
                    if not frame.rejected:
                        self.frames.addItem(frameItem)

        if temp_frames_list == [
            self.frames.item(x).text() for x in range(self.frames.count())
        ]:
            self.frames.setCurrentRow(temp_selected_row)
            if theme_change_update:
                self.update_plot()
        else:
            self.frames.setCurrentRow(0)
            self.frameselection_changed()

    def update_plot(self):
        if self.canvas.fig.get_axes():
            self.canvas.fig.delaxes(self.canvas.axes)

        tms: TmsMeasurement = self.ui.patient.data.measurement_data[
            self.session_filter
        ][self.type_filter]

        if self.frames.count() == 0:
            self.canvas.fig.suptitle(f"Currently No Data to Display", fontsize=16)
        else:
            # Set Checkbox to rejected State
            if tms.frames[self.selected_frame].rejected:
                self.reject_check_box.setCheckState(Qt.CheckState.Checked)
            else:
                self.reject_check_box.setCheckState(Qt.CheckState.Unchecked)

            # Plotting
            self.canvas.axes = self.canvas.fig.add_subplot()
            self.canvas.fig.suptitle("")

            plot_inspector = TmsPlotObject(
                self.canvas.fig, self.canvas.axes, color="k", linewidth=1.0
            )
            plot_inspector.axis.set_title(
                f"{self.ui.patient.data.subject_name} Inspector: {tms.measurement_type.name} - {self.type_filter.upper()} Frame No:{self.selected_frame +1} State: {tms.frames[self.selected_frame].state}"
            )
            max_val, min_val = tms.get_max_min_bound()
            plot_inspector.axis.set_ylim(min_val, max_val)

            tms.plot_frames(
                start_index_window=0,
                end_index_window=tms.points,
                pl=plot_inspector,
                start_frame_sel=self.selected_frame,
                end_frame_sel=self.selected_frame,
                show_rejected=True,
            )
        self.canvas.draw()

    def initiate_sessions(self):
        if not self.ui.patient.data:
            return

        current_row = self.sessions.currentRow()
        self.sessions.clear()

        tms: TmsPatient = self.ui.patient.data
        for session in ["BA", "PM", "AC", "LT"]:
            if (
                tms.measurement_data.get(session.lower()) is not None
                and len(tms.measurement_data.get(session.lower())) != 0
            ):
                inspneeded = tms.get_count_inspection_needed(session.lower())
                rejected = tms.get_count_rejected(session.lower())
                self.sessions.addItem(f"{session} \tI({inspneeded}) R({rejected})")

        if current_row == -1 or current_row > self.sessions.count() - 1:
            self.sessions.setCurrentRow(0)
        else:
            self.sessions.setCurrentRow(current_row)

        for item in self.sessions.selectedItems():
            print(item.text())
            self.session_filter = item.text().split(" ")[0].lower()

    def initiate_types(self):
        if not self.ui.patient.data:
            return

        current_row = self.types.currentRow()
        self.types.clear()

        tms: TmsPatient = self.ui.patient.data.measurement_data[self.session_filter]
        for type in ["SI1mV", "RECR", "ICI", "LICI"]:
            if tms.get(type.lower()) is not None:
                inspneeded = tms[type.lower()].get_count_inspection_needed()
                rejected = tms[type.lower()].get_count_rejected()
                self.types.addItem(f"{type} \tI({inspneeded}) R({rejected})")

        if current_row == -1 or current_row > self.types.count() - 1:
            self.types.setCurrentRow(0)
        else:
            self.types.setCurrentRow(current_row)

        for item in self.types.selectedItems():
            print(item.text())
            self.type_filter = item.text().split(" ")[0].lower()

    def next_frame(self):
        if not self.ui.patient.data:
            return

        self.frames.setCurrentRow(self.frames.currentRow() + 1)
        if self.frames.currentRow() == -1:
            self.frames.setCurrentRow(0)
        self.frameselection_changed()

    def prev_frame(self):
        if not self.ui.patient.data:
            return

        self.frames.setCurrentRow(self.frames.currentRow() - 1)
        if self.frames.currentRow() == -1:
            self.frames.setCurrentRow(self.frames.count() - 1)
        self.frameselection_changed()

    def session_changed(self):
        for item in self.sessions.selectedItems():
            self.session_filter = item.text().split(" ")[0].lower()
        self.update()

    def type_changed(self):
        for item in self.types.selectedItems():
            self.type_filter = item.text().lower()
        self.update()

    def frameselection_changed(self):
        for item in self.frames.selectedItems():
            self.selected_frame = int(item.text()) - 1
        self.update_plot()

    def reject_frame(self):
        if not self.ui.patient.data:
            return

        tms: TmsMeasurement = self.ui.patient.data.measurement_data[
            self.session_filter
        ][self.type_filter]

        if self.reject_check_box.checkState() == Qt.CheckState.Checked:
            tms.frames[self.selected_frame].rejected = True
        else:
            tms.frames[self.selected_frame].rejected = False

        self.ui.patient.data.save_preferences()
        self.update()

    def show_rejected_changed(self):
        self.show_rejected = (
            self.show_rejected_box.checkState() == Qt.CheckState.Checked
        )
        self.update()

    def show_inspection_only_changed(self):
        self.only_inspection_needed = (
            self.only_inspection_needed_box.checkState() == Qt.CheckState.Checked
        )
        self.update()


class TmsOverview(TmsUiComponent):
    """Tabview for the main overview of all the data in a tableview"""

    si1mv_table: QTableWidget
    recr_table: QTableWidget
    ici_table: QTableWidget
    lici_table: QTableWidget

    si1mv_value: QLabel
    export_xls: QPushButton

    def __init__(self, ui: TmsUi) -> None:
        super().__init__(ui)

        self.si1mv_table = self.ui.findChild(QTableWidget, "overviewSi1mvTable")
        self.recr_table = self.ui.findChild(QTableWidget, "overviewRecrTable")
        self.ici_table = self.ui.findChild(QTableWidget, "overviewIciTable")
        self.lici_table = self.ui.findChild(QTableWidget, "overviewLiciTable")

        self.si1mv_value = self.ui.findChild(QLabel, "overviewSi1mvValue")
        self.export_xls = self.ui.findChild(QPushButton, "overviewExport")
        self.export_xls.clicked.connect(self.export)

    def update(self):
        if not self.ui.patient.data:
            return

        table_data = self.ui.patient.data.export_data()[
            self.ui.patient.data.subject_name
        ]

        row = 0
        for session in ["ba", "pm", "ac", "lt"]:
            no_data_item = QtWidgets.QTableWidgetItem("No Data")
            no_data_item.setBackground(QtGui.QColor.fromRgb(90, 90, 90))
            no_data_item.setForeground(QtGui.QColor.fromRgb(255, 255, 255))

            # SI1mV
            if (
                table_data.get(session) is not None
                and table_data[session].get("si1mv") is not None
            ):
                self.si1mv_table.setItem(
                    row,
                    0,
                    QtWidgets.QTableWidgetItem(
                        str(table_data[session]["si1mv"]["mep"])
                    ),
                )
                self.si1mv_value.setText(f"{table_data[session]['si1mv']['value']} mV")
            else:
                self.si1mv_table.setItem(
                    row, 0, QtWidgets.QTableWidgetItem(no_data_item)
                )

            # RECR
            if (
                table_data.get(session) is not None
                and table_data[session].get("recr") is not None
            ):
                for idx, item in enumerate(table_data[session]["recr"]):
                    self.display_data(self.recr_table, item, row, idx)

            else:
                for idx in range(0, 9):
                    self.recr_table.setItem(
                        row, idx, QtWidgets.QTableWidgetItem(no_data_item)
                    )

            # ICI
            if (
                table_data.get(session) is not None
                and table_data[session].get("ici") is not None
            ):
                for idx, item in enumerate(table_data[session]["ici"]):
                    self.display_data(self.ici_table, item, row, idx)
            else:
                for idx in range(0, 3):
                    self.ici_table.setItem(
                        row, idx, QtWidgets.QTableWidgetItem(no_data_item)
                    )

            # LICI
            if (
                table_data.get(session) is not None
                and table_data[session].get("lici") is not None
            ):
                for idx, item in enumerate(table_data[session]["lici"]):
                    self.display_data(self.lici_table, item, row, idx)
            else:
                for idx in range(0, 4):
                    self.lici_table.setItem(
                        row, idx, QtWidgets.QTableWidgetItem(no_data_item)
                    )
            row += 1

    def export(self):
        if not self.ui.patient.data:
            return

        filename = ""
        filename = QFileDialog.getSaveFileName(
            self.ui,
            "Select where to export Data",
            f"{self.ui.patient.data.subject_name}.xlsx",
            "*.xlsx",
        )

        if filename[0] != "":
            path_to_write = filename[0]
            if ".xls" not in path_to_write:
                path_to_write = path_to_write + ".xlsx"

            xlxfile = xlsxwriter.Workbook(path_to_write)
            si1mv_table = xlxfile.add_worksheet("SI1mv")
            si1mv_table.set_column(0, 0, 20)
            si1mv_table.write(1, 0, "Patient_No")
            si1mv_table.write(1, 1, "BA (MEP)")
            si1mv_table.write(1, 2, "PM (MEP)")
            si1mv_table.write(1, 3, "AC (MEP)")
            si1mv_table.write(1, 4, "LT (MEP)")

            recr_table = xlxfile.add_worksheet("RECR")
            recr_table.set_column(0, 0, 20)
            recr_table.write(1, 0, "Patient_No")
            for count, session in enumerate(["BA", "PM", "AC", "LT"]):
                offset = count * 9
                recr_table.write(0, 1 + offset, session)
                recr_table.write(1, 1 + offset, "90% RMT")
                recr_table.write(1, 2 + offset, "100% RMT")
                recr_table.write(1, 3 + offset, "110% RMT")
                recr_table.write(1, 4 + offset, "120% RMT")
                recr_table.write(1, 5 + offset, "130% RMT")
                recr_table.write(1, 6 + offset, "140% RMT")
                recr_table.write(1, 7 + offset, "S50")
                recr_table.write(1, 8 + offset, "Slope ( S50 )")
                recr_table.write(1, 9 + offset, "%RMT ( S50 )")

            ici_table = xlxfile.add_worksheet("ICI")
            ici_table.set_column(0, 0, 20)
            ici_table.set_column("B:M", 12)
            ici_table.write(1, 0, "Patient_No")
            for count, session in enumerate(["BA", "PM", "AC", "LT"]):
                offset = count * 3
                ici_table.write(0, 1 + offset, session)
                ici_table.write(1, 1 + offset, "State 1 (MEP)")
                ici_table.write(1, 2 + offset, "State 2 (MEP)")
                ici_table.write(1, 3 + offset, "State 3 (MEP)")

            lici_table = xlxfile.add_worksheet("LICI")
            lici_table.set_column(0, 0, 20)
            lici_table.set_column("B:Q", 12)
            lici_table.write(1, 0, "Patient_No")
            for count, session in enumerate(["BA", "PM", "AC", "LT"]):
                offset = count * 4
                lici_table.write(0, 1 + offset, session)
                lici_table.write(1, 1 + offset, "State 1 (MEP)")
                lici_table.write(1, 2 + offset, "State 2 (MEP)")
                lici_table.write(1, 3 + offset, "State 3 (MEP)")
                lici_table.write(1, 4 + offset, "State 2_3 (MEP)")

            row = 2
            data = self.ui.patient.data.export_data()[self.ui.patient.data.subject_name]

            si1mv_table.write(row, 0, self.ui.patient.data.subject_name)
            recr_table.write(row, 0, self.ui.patient.data.subject_name)
            ici_table.write(row, 0, self.ui.patient.data.subject_name)
            lici_table.write(row, 0, self.ui.patient.data.subject_name)

            column_offsets = {"ba": 0, "pm": 1, "ac": 2, "lt": 3}
            for session in data:
                column = column_offsets[session] + 1

                if data[session].get("si1mv"):
                    si1mv_table.write(row, column, data[session]["si1mv"]["mep"])

                if data[session].get("recr"):
                    for idx, item in enumerate(data[session]["recr"]):
                        recr_column = ((column - 1) * 9) + 1
                        if item != -99999:
                            recr_table.write(row, recr_column + idx, item)

                if data[session].get("ici"):
                    for idx, item in enumerate(data[session]["ici"]):
                        ici_column = ((column - 1) * 3) + 1
                        ici_table.write(row, ici_column + idx, item)

                if data[session].get("lici"):
                    for idx, item in enumerate(data[session]["lici"]):
                        lici_column = ((column - 1) * 4) + 1
                        lici_table.write(row, lici_column + idx, item)
            xlxfile.close()

        self.ui.progress_bar.setVisible(False)
        self.ui.progress_label.setVisible(False)
        TmsLogger().log("Done...")

    def display_data(self, table, item, row, idx):
        if item == -1:
            data_item = QtWidgets.QTableWidgetItem(str(item))
            data_item.setBackground(QtGui.QColor.fromRgb(245, 66, 66))
            table.setItem(row, idx, data_item)
        elif item == -99999:
            data_item = QtWidgets.QTableWidgetItem("No Data")
            data_item.setBackground(QtGui.QColor.fromRgb(230, 174, 23))
            table.setItem(row, idx, data_item)
        else:
            table.setItem(row, idx, QtWidgets.QTableWidgetItem(str(item)))


class TmsSi1mvPlots(TmsUiComponent):
    """Tabview for the SI1MV Plots"""

    si1mv_plot_targets: dict[str, QVBoxLayout] = {}

    change_indicator: str = ""

    def __init__(self, ui: TmsUi) -> None:
        super().__init__(ui)

        self.si1mv_plot_targets["ba"] = self.ui.findChild(QVBoxLayout, "si1mvBaPlot")
        self.si1mv_plot_targets["pm"] = self.ui.findChild(QVBoxLayout, "si1mvPmPlot")
        self.si1mv_plot_targets["ac"] = self.ui.findChild(QVBoxLayout, "si1mvAcPlot")
        self.si1mv_plot_targets["lt"] = self.ui.findChild(QVBoxLayout, "si1mvLtPlot")

    def clear_plot_target(self, plot_target):
        for i in reversed(range(plot_target.count())):
            widgetToRemove = plot_target.itemAt(i).widget()
            # remove it from the layout list
            plot_target.removeWidget(widgetToRemove)
            # remove it from the gui
            widgetToRemove.setParent(None)

    def update(self):
        if not self.ui.patient.data:
            return

        if self.ui.tabViewer.currentWidget().objectName() == "si1mvTab":
            new_hash = hashlib.sha256(
                str(self.ui.patient.data.export_data()).encode()
            ).hexdigest()
            if self.change_indicator != new_hash:
                for session in ["ba", "pm", "ac", "lt"]:
                    self.clear_plot_target(self.si1mv_plot_targets[session])
                for session in self.si1mv_plot_targets.keys():
                    if self.ui.patient.data.measurement_data[session].get("si1mv"):
                        self.clear_plot_target(self.si1mv_plot_targets[session])
                        canvas = MplCanvas(self, subplot=False)
                        self.si1mv_plot_targets[session].addWidget(canvas)

                        canvas.fig.suptitle(f"{session.upper()} : SI1mV")
                        self.ui.patient.data.measurement_data[session][
                            "si1mv"
                        ].plot_external(
                            canvas.fig,
                            self.ui.patient.si1mv_start.value(),
                            self.ui.patient.si1mv_end.value(),
                        )
                        canvas.draw()
                self.change_indicator = new_hash


class TmsRecrPlots(TmsUiComponent):
    """Tabview for the RECR Plots"""

    plot_targets: dict[str, QVBoxLayout] = {}

    ba_overwrite: QComboBox
    pm_overwrite: QComboBox
    ac_overwrite: QComboBox
    lt_overwrite: QComboBox

    ba_overwrite_label: QLabel
    pm_overwrite_label: QLabel
    ac_overwrite_label: QLabel
    lt_overwrite_label: QLabel

    change_indicator: str = ""

    def __init__(self, ui: TmsUi) -> None:
        super().__init__(ui)

        self.plot_targets["ba"] = self.ui.findChild(QVBoxLayout, "baRecrPlot")
        self.plot_targets["pm"] = self.ui.findChild(QVBoxLayout, "pmRecrPlot")
        self.plot_targets["ac"] = self.ui.findChild(QVBoxLayout, "acRecrPlot")
        self.plot_targets["lt"] = self.ui.findChild(QVBoxLayout, "ltRecrPlot")

        self.ba_overwrite_label = self.ui.findChild(
            QLabel, "labelRegressionOverwriteBa"
        )
        self.pm_overwrite_label = self.ui.findChild(
            QLabel, "labelRegressionOverwritePm"
        )
        self.ac_overwrite_label = self.ui.findChild(
            QLabel, "labelRegressionOverwriteAc"
        )
        self.lt_overwrite_label = self.ui.findChild(
            QLabel, "labelRegressionOverwriteLt"
        )

        self.ba_overwrite = self.ui.findChild(QComboBox, "patientRegressionModelBa")
        self.ba_overwrite.addItem("Default")
        for enum_choice in RegressionModels:
            self.ba_overwrite.addItem(enum_choice.name)
        self.ba_overwrite.currentTextChanged.connect(self.ba_overwrite_changed)

        self.pm_overwrite = self.ui.findChild(QComboBox, "patientRegressionModelPm")
        self.pm_overwrite.addItem("Default")
        for enum_choice in RegressionModels:
            self.pm_overwrite.addItem(enum_choice.name)
        self.pm_overwrite.currentTextChanged.connect(self.pm_overwrite_changed)

        self.ac_overwrite = self.ui.findChild(QComboBox, "patientRegressionModelAc")
        self.ac_overwrite.addItem("Default")
        for enum_choice in RegressionModels:
            self.ac_overwrite.addItem(enum_choice.name)
        self.ac_overwrite.currentTextChanged.connect(self.ac_overwrite_changed)

        self.lt_overwrite = self.ui.findChild(QComboBox, "patientRegressionModelLt")
        self.lt_overwrite.addItem("Default")
        for enum_choice in RegressionModels:
            self.lt_overwrite.addItem(enum_choice.name)
        self.lt_overwrite.currentTextChanged.connect(self.lt_overwrite_changed)

        self.update_overwrite_selection()

    def update_overwrite_selection(self):
        if not self.ui.patient.data:
            return
        # Disconnect Current Callbacks
        self.ba_overwrite.currentTextChanged.disconnect(self.ba_overwrite_changed)
        self.pm_overwrite.currentTextChanged.disconnect(self.pm_overwrite_changed)
        self.ac_overwrite.currentTextChanged.disconnect(self.ac_overwrite_changed)
        self.lt_overwrite.currentTextChanged.disconnect(self.lt_overwrite_changed)

        # Reset combobox values and visibility
        if self.ui.patient.data.measurement_data["ba"].get("recr"):
            self.ba_overwrite.setVisible(True)
            self.ba_overwrite_label.setVisible(True)

            overwrite = self.ui.patient.data.measurement_data["ba"][
                "recr"
            ].regression_overwrite
            if overwrite is not None:
                self.ba_overwrite.setCurrentText(overwrite.name)
            else:
                self.ba_overwrite.setCurrentText("Default")
        else:
            self.ba_overwrite_label.setVisible(False)
            self.ba_overwrite.setVisible(False)

        if self.ui.patient.data.measurement_data["pm"].get("recr"):
            self.pm_overwrite.setVisible(True)
            self.pm_overwrite_label.setVisible(True)

            overwrite = self.ui.patient.data.measurement_data["pm"][
                "recr"
            ].regression_overwrite
            if overwrite is not None:
                self.pm_overwrite.setCurrentText(overwrite.name)
            else:
                self.pm_overwrite.setCurrentText("Default")
        else:
            self.pm_overwrite_label.setVisible(False)
            self.pm_overwrite.setVisible(False)

        if self.ui.patient.data.measurement_data["ac"].get("recr"):
            self.ac_overwrite.setVisible(True)
            self.ac_overwrite_label.setVisible(True)

            overwrite = self.ui.patient.data.measurement_data["ac"][
                "recr"
            ].regression_overwrite
            if overwrite is not None:
                self.ac_overwrite.setCurrentText(overwrite.name)
            else:
                self.ac_overwrite.setCurrentText("Default")
        else:
            self.ac_overwrite_label.setVisible(False)
            self.ac_overwrite.setVisible(False)

        if self.ui.patient.data.measurement_data["lt"].get("recr"):
            self.lt_overwrite.setVisible(True)
            self.lt_overwrite_label.setVisible(True)

            overwrite = self.ui.patient.data.measurement_data["lt"][
                "recr"
            ].regression_overwrite
            if overwrite is not None:
                self.lt_overwrite.setCurrentText(overwrite.name)
            else:
                self.lt_overwrite.setCurrentText("Default")
        else:
            self.lt_overwrite_label.setVisible(False)
            self.lt_overwrite.setVisible(False)

        # Reconnect Callbacks
        self.ba_overwrite.currentTextChanged.connect(self.ba_overwrite_changed)
        self.pm_overwrite.currentTextChanged.connect(self.pm_overwrite_changed)
        self.ac_overwrite.currentTextChanged.connect(self.ac_overwrite_changed)
        self.lt_overwrite.currentTextChanged.connect(self.lt_overwrite_changed)

    def overwrite_match(self, text) -> RegressionModels:
        if text == "Cubic":
            return RegressionModels.Cubic
        elif text == "Logistic":
            return RegressionModels.Logistic
        elif text == "Gombertz":
            return RegressionModels.Gombertz
        elif text == "ReverseGombertz":
            return RegressionModels.ReverseGombertz
        elif text == "Boltzmann":
            return RegressionModels.Boltzmann

    def ba_overwrite_changed(self):
        if not self.ui.patient.data:
            return

        if self.ba_overwrite.currentText() == "Default":
            overwrite = None
        else:
            overwrite = self.overwrite_match(self.ba_overwrite.currentText())

        print("#" * 20)
        print(overwrite)
        print(self.ba_overwrite.currentText())

        self.ui.patient.data.measurement_data["ba"][
            "recr"
        ].regression_overwrite = overwrite
        self.ui.patient.data.save_overwrites()
        self.ui.update()

    def pm_overwrite_changed(self):
        if not self.ui.patient.data:
            return

        if self.pm_overwrite.currentText() == "Default":
            overwrite = None
        else:
            overwrite = self.overwrite_match(self.pm_overwrite.currentText())

        self.ui.patient.data.measurement_data["pm"][
            "recr"
        ].regression_overwrite = overwrite
        self.ui.patient.data.save_overwrites()
        self.ui.update()

    def ac_overwrite_changed(self):
        if not self.ui.patient.data:
            return

        if self.ac_overwrite.currentText() == "Default":
            overwrite = None
        else:
            overwrite = self.overwrite_match(self.ac_overwrite.currentText())

        self.ui.patient.data.measurement_data["ac"][
            "recr"
        ].regression_overwrite = overwrite
        self.ui.patient.data.save_overwrites()
        self.ui.update()

    def lt_overwrite_changed(self):
        if not self.ui.patient.data:
            return

        if self.lt_overwrite.currentText() == "Default":
            overwrite = None
        else:
            overwrite = self.overwrite_match(self.lt_overwrite.currentText())

        self.ui.patient.data.measurement_data["lt"][
            "recr"
        ].regression_overwrite = overwrite
        self.ui.patient.data.save_overwrites()
        self.ui.update()

    def clear_plot_target(self, plot_target):
        for i in reversed(range(plot_target.count())):
            widgetToRemove = plot_target.itemAt(i).widget()
            # remove it from the layout list
            plot_target.removeWidget(widgetToRemove)
            # remove it from the gui
            widgetToRemove.setParent(None)

    def update(self, force_redraw=False):
        if not self.ui.patient.data:
            return

        if self.ui.tabViewer.currentWidget().objectName() == "recrTab":
            new_hash = hashlib.sha256(
                str(self.ui.patient.data.export_data()).encode()
            ).hexdigest()
            if self.change_indicator != new_hash or force_redraw:
                self.update_overwrite_selection()

                for session in ["ba", "pm", "ac", "lt"]:
                    self.clear_plot_target(self.plot_targets[session])
                for session in self.plot_targets.keys():
                    if self.ui.patient.data.measurement_data[session].get("recr"):
                        canvas = MplCanvas(self, subplot=False)
                        self.plot_targets[session].addWidget(canvas)

                        canvas.fig.suptitle(f"{session.upper()} : Recruitment Curve")
                        self.ui.patient.data.measurement_data[session][
                            "recr"
                        ].plot_external(
                            canvas.fig,
                            self.ui.patient.recr_start.value(),
                            self.ui.patient.recr_end.value(),
                        )
                        canvas.draw()
                self.change_indicator = new_hash


class TmsIciPlots(TmsUiComponent):
    """Tabview for ICI Plots"""

    plot_targets: dict[str, QVBoxLayout] = {}

    change_indicator: str = ""

    def __init__(self, ui: TmsUi) -> None:
        super().__init__(ui)

        self.plot_targets["ba"] = self.ui.findChild(QVBoxLayout, "baIciPlot")
        self.plot_targets["pm"] = self.ui.findChild(QVBoxLayout, "pmIciPlot")
        self.plot_targets["ac"] = self.ui.findChild(QVBoxLayout, "acIciPlot")
        self.plot_targets["lt"] = self.ui.findChild(QVBoxLayout, "ltIciPlot")

    def clear_plot_target(self, plot_target):
        for i in reversed(range(plot_target.count())):
            widgetToRemove = plot_target.itemAt(i).widget()
            # remove it from the layout list
            plot_target.removeWidget(widgetToRemove)
            # remove it from the gui
            widgetToRemove.setParent(None)

    def update(self):
        if not self.ui.patient.data:
            return

        if self.ui.tabViewer.currentWidget().objectName() == "iciTab":
            new_hash = hashlib.sha256(
                str(self.ui.patient.data.export_data()).encode()
            ).hexdigest()
            if self.change_indicator != new_hash:
                for session in ["ba", "pm", "ac", "lt"]:
                    self.clear_plot_target(self.plot_targets[session])
                for session in self.plot_targets.keys():
                    if self.ui.patient.data.measurement_data[session].get("ici"):
                        canvas = MplCanvas(self, subplot=False)
                        self.plot_targets[session].addWidget(canvas)

                        canvas.fig.suptitle(f"{session.upper()} : ICI")
                        self.ui.patient.data.measurement_data[session][
                            "ici"
                        ].plot_external(
                            canvas.fig,
                            self.ui.patient.ici_start.value(),
                            self.ui.patient.ici_end.value(),
                        )
                        canvas.draw()
                self.change_indicator = new_hash


class TmsLiciPlots(TmsUiComponent):
    """Tabview of LICI Plots"""

    plot_targets: dict[str, QVBoxLayout] = {}

    change_indicator: str = ""

    def __init__(self, ui: TmsUi) -> None:
        super().__init__(ui)

        self.plot_targets["ba"] = self.ui.findChild(QVBoxLayout, "baLiciPlot")
        self.plot_targets["pm"] = self.ui.findChild(QVBoxLayout, "pmLiciPlot")
        self.plot_targets["ac"] = self.ui.findChild(QVBoxLayout, "acLiciPlot")
        self.plot_targets["lt"] = self.ui.findChild(QVBoxLayout, "ltLiciPlot")

    def clear_plot_target(self, plot_target):
        for i in reversed(range(plot_target.count())):
            widgetToRemove = plot_target.itemAt(i).widget()
            # remove it from the layout list
            plot_target.removeWidget(widgetToRemove)
            # remove it from the gui
            widgetToRemove.setParent(None)

    def update(self):
        if not self.ui.patient.data:
            return

        if self.ui.tabViewer.currentWidget().objectName() == "liciTab":
            new_hash = hashlib.sha256(
                str(self.ui.patient.data.export_data()).encode()
            ).hexdigest()
            if self.change_indicator != new_hash:
                for session in ["ba", "pm", "ac", "lt"]:
                    self.clear_plot_target(self.plot_targets[session])
                for session in self.plot_targets.keys():
                    if self.ui.patient.data.measurement_data[session].get("lici"):
                        self.clear_plot_target(self.plot_targets[session])
                        canvas = MplCanvas(self, subplot=False)
                        self.plot_targets[session].addWidget(canvas)

                        canvas.fig.suptitle(f"{session.upper()} : LICI")
                        self.ui.patient.data.measurement_data[session][
                            "lici"
                        ].plot_external(
                            canvas.fig,
                            self.ui.patient.lici_start.value(),
                            self.ui.patient.lici_end.value(),
                        )
                        canvas.draw()
                self.change_indicator = new_hash


class MplCanvas(FigureCanvas):
    """Class that defines an interactive Plotarea"""

    ui_component: TmsUiComponent
    theme: str

    def __init__(self, ui_component: TmsUiComponent, dpi=100, subplot: bool = True):
        self.ui_component = ui_component
        self.theme = self.ui_component.ui.themeselector.currentText()

        self.fig = Figure(dpi=dpi)
        self.fig.set_facecolor(self.ui_component.ui.theme.COLOR_BACKGROUND_1)

        if subplot:
            self.axes = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)
