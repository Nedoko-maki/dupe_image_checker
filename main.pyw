import multiprocessing as mp
import sys
import traceback
import dupe_image_lib as dil
from pathlib import Path

from PyQt5.QtWidgets import (QComboBox, QPushButton, QApplication, QGridLayout, QWidget, QDesktopWidget, QMainWindow,
                             QLineEdit, QTextEdit, QLabel, QProgressBar, QTextBrowser, QGroupBox, QCheckBox)
from PyQt5.QtGui import QIntValidator
from PyQt5.QtCore import QThread, QObject, pyqtSignal


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.layout = QGridLayout()
        self.window = QWidget()
        self.text_log_widget = QGroupBox()
        self.text_log = QTextBrowser(self.text_log_widget)

        self.widgets = {"combobox_sel_folder": QComboBox(), "combobox_cpu_cores": QComboBox(),
                        "button_confirm": QPushButton("Confirm"),
                        "progress_bar": QProgressBar(),
                        "checkbox_remove_json": QCheckBox("Remove previous json?"),
                        "checkbox_perfect_dupe": QCheckBox("Check for perfect dupes?"),
                        "textbox_grid_density": QLineEdit(), "textbox_cutoff": QLineEdit(),
                        "textbox_strfex": QLineEdit(),
                        "text_combobox_cc": QLabel("Max CPU cores to be allowed?"),
                        "text_grid_density": QLabel("Grid Density (Default 10, max 20)"),
                        "text_cutoff": QLabel("Cutoff (Default 12)"), "text_strfex": QLabel("Strfex Expression"),
                        "text_log": self.text_log}

        self.widget_pos = {"combobox_sel_folder": (0, 0, 1, 2), "combobox_cpu_cores": (4, 1), "text_combobox_cc": (4, 0),
                      "textbox_grid_density": (1, 1), "textbox_cutoff": (2, 1), "textbox_strfex": (3, 1),
                      "text_grid_density": (1, 0), "text_cutoff": (2, 0), "text_strfex": (3, 0),
                      "text_log": (1, 3, 5, 1),
                      "button_confirm": (0, 3),
                      "checkbox_perfect_dupe": (5, 0, 1, 2), "checkbox_remove_json": (6, 0, 1, 2),
                      "progress_bar": (7, 0, 1, 4)}

        self.allowed_cpu_cores = None

        self.thread, self.worker = None, None
        self.folder_name, self.folder_index, self.folder_file_len = None, None, None
        self.grid_density, self.cutoff, self.strfex = None, None, None
        self.toggle_rj, self.toggle_pd = None, None
        self.log = str()

        self.init_ui()

    def init_ui(self):
        self.widgets["combobox_sel_folder"].addItems(
            [dir.name + f', Files: {len([_ for _ in Path(Path.cwd(), dir).glob("*") if _.is_file()])}' for dir in
             Path.cwd().glob("*")
             if dir.is_dir()])
        self.widgets["combobox_cpu_cores"].addItems([str(_) for _ in range(round(mp.cpu_count()), 0, -1)])
        self.widgets["combobox_cpu_cores"].setCurrentIndex(round(mp.cpu_count() // 2))

        # Connect signal to our methods.
        self.widgets["combobox_sel_folder"].activated.connect(self.combobox_selected_folder)
        self.widgets["button_confirm"].clicked.connect(self.button_confirm_pressed)

        self.onlyInt = QIntValidator()  # setting the textboxes to only receive integers.
        self.widgets["textbox_grid_density"].setValidator(self.onlyInt)
        self.widgets["textbox_cutoff"].setValidator(self.onlyInt)

        self.widgets["textbox_grid_density"].setText("10")
        self.widgets["textbox_cutoff"].setText("12")
        self.widgets["textbox_strfex"].setText("%grp%-%grp_num%")

        self.widgets["checkbox_remove_json"].setChecked(True)
        self.widgets["checkbox_perfect_dupe"].setChecked(True)

        self.window.setWindowTitle('Duplicate & Similar Image Checker')
        qtRectangle = QWidget.frameGeometry(self)  # this code is to attempt to centre the window.
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        window_position = (qtRectangle.topLeft().x(), qtRectangle.topLeft().y())  # up to here.
        window_size = (600, 400)

        self.window.setGeometry(*window_position, *window_size)

        self.widgets["text_log"].setLineWrapMode(QTextEdit.NoWrap)

        for widget_name in self.widgets:
            self.layout.addWidget(self.widgets[widget_name], *self.widget_pos[widget_name])

        self.window.setLayout(self.layout)
        self.window.show()

    def combobox_selected_folder(self, _):
        self.folder_name = self.widgets["combobox_sel_folder"].currentText()
        self.folder_index = self.widgets["combobox_sel_folder"].currentIndex()

    def log_print(self, text):
        self.log += str(text) + "\n"
        self.widgets["text_log"].setText(self.log)

    def progress_update(self, percentage: int):
        self.widgets["progress_bar"].setValue(percentage)

    def button_confirm_pressed(self):

        self.log = str()  # clearing log
        self.widgets["text_log"].setText(self.log)

        self.grid_density = int(self.widgets["textbox_grid_density"].text())  # reading values from textboxes
        self.cutoff = int(self.widgets["textbox_cutoff"].text())
        self.strfex = str(self.widgets["textbox_strfex"].text())

        self.folder_index = self.widgets["combobox_sel_folder"].currentIndex()
        self.allowed_cpu_cores = int(self.widgets["combobox_cpu_cores"].currentText())

        self.toggle_rj = self.widgets["checkbox_remove_json"].isChecked()
        self.toggle_pd = self.widgets["checkbox_perfect_dupe"].isChecked()

        if self.grid_density > 20:
            self.log_print("Grid density is too high! Try a value of 20 or below.")
        else:
            self.run_worker()

    def run_worker(self):
        self.thread = QThread()
        self.worker = Worker(self.grid_density, self.cutoff, self.strfex,
                             self.toggle_rj, self.toggle_pd, self.folder_index,
                             self.allowed_cpu_cores)

        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.progress_update.connect(self.progress_update)
        self.worker.log_update.connect(self.log_print)
        self.thread.start()


class Worker(QObject):
    finished = pyqtSignal()  # signalling code for signalling to mother process of GUI.
    progress_update = pyqtSignal(int)
    log_update = pyqtSignal(str)

    def __init__(self, grid_density, cutoff, strfex, toggle_rj, toggle_pd, folder_index, allowed_cpu_cores):
        super().__init__()

        self.grid_density = grid_density
        self.cutoff = cutoff
        self.strfex = strfex
        self.toggle_rj = toggle_rj
        self.toggle_pd = toggle_pd
        self.folder_index = folder_index
        self.allowed_cpu_cores = allowed_cpu_cores

    def run(self):

        pyqt_signal_dict = {"progress_bar": self.progress_update,
                            "text_log": self.log_update}

        image_types = [".png", ".jpeg", ".jpg"]
        folders = [_.name for _ in Path.cwd().glob("*") if _.is_dir()]
        image_folder = Path(Path.cwd(), folders[self.folder_index])
        image_files = [_ for _ in image_folder.glob("*") if dil.f_type_return(_, image_types) in image_types]

        if len(image_files) == 0:
            self.log_update.emit("No images in this folder!")
            self.finished.emit()

        image_struct = dil.ImageStruct(directory=image_folder, allowed_cpu_cores=self.allowed_cpu_cores,
                                       pyqt_signals=pyqt_signal_dict)

        if not dil.check_json_exists(image_folder):
            dil.rename_to_num(image_folder, image_files, "_", image_types)
            image_files = [_.name for _ in image_folder.glob("*") if dil.f_type_return(_, image_types) in image_types]
            image_struct.generate_data(grid_density=self.grid_density, file_list=image_files)
        else:
            if self.toggle_rj:
                dil.rename_to_num(image_folder, image_files, "_", image_types)
                Path(image_folder, "hash_data", "fp_hash_data.json").unlink()  # removing/unlinking the json file
                image_files = [_.name for _ in image_folder.glob("*") if
                               dil.f_type_return(_, image_types) in image_types]
                image_struct.generate_data(grid_density=self.grid_density, file_list=image_files)
            else:
                image_struct.load_data()

        if self.toggle_pd:
            remove_list = dil.cross_compare_list(image_struct,
                                                 dil.compare_hashes, mode="identical")
            # will default to similar, i.e. cutoff 0. this is to remove identical duplicate
            image_struct = dil.move_files("moved_images", remove_list[1], image_struct)
            image_struct.save_data()

        try:
            dupe_list = dil.cross_compare_list(image_struct,
                                               dil.compare_hashes, cutoff=self.cutoff, mode="similar")
            # this is to group similar images
        except:
            traceback.print_exc()
            dupe_list = []

        if len(dupe_list) == 0:
            self.log_update.emit("No similar duplicates!")
        else:
            dil.regroup_files(dupe_list[1], image_struct, type_list=image_types,
                              expression=self.strfex)

        self.log_update.emit("Finished!")
        self.finished.emit()


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
