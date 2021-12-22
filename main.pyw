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

        self.combobox = QComboBox()
        self.confirm_button = QPushButton("Confirm")
        self.progress_bar = QProgressBar()
        self.checkbox_remove_json = QCheckBox("Remove previous json?")
        self.checkbox_perfect_dupe = QCheckBox("Check for perfect dupes?")
        self.textbox_grid = QLineEdit()
        self.textbox_cutoff = QLineEdit()
        self.textbox_strfex = QLineEdit()
        self.text_grid = QLabel("Grid Density (Default 10, max 20)")
        self.text_cutoff = QLabel("Cutoff (Default 12)")
        self.text_strfex = QLabel("Strfex Expression")
        self.text_log_widget = QGroupBox()
        self.text_log = QTextBrowser(self.text_log_widget)

        self.thread, self.worker = None, None
        self.folder_name, self.folder_index, self.folder_file_len = None, None, None
        self.grid_density, self.cutoff, self.strfex = None, None, None
        self.toggle_rj, self.toggle_pd = None, None
        self.log = str()

        self.init_ui()

    def init_ui(self):
        self.combobox.addItems(
            [dir.name + f', Files: {len([_ for _ in Path(Path.cwd(), dir).glob("*") if _.is_file()])}' for dir in
             Path.cwd().glob("*")
             if dir.is_dir()])

        # Connect signal to our methods.
        self.combobox.activated.connect(self.combobox_info)
        self.confirm_button.clicked.connect(self.button_confirm_pressed)

        self.onlyInt = QIntValidator()  # setting the textboxes to only receive integers.
        self.textbox_grid.setValidator(self.onlyInt)
        self.textbox_cutoff.setValidator(self.onlyInt)

        self.textbox_grid.setText("10")
        self.textbox_cutoff.setText("12")
        self.textbox_strfex.setText("%grp%-%grp_num%")

        self.checkbox_remove_json.setChecked(True)
        self.checkbox_perfect_dupe.setChecked(True)

        self.window.setWindowTitle('Duplicate & Similar Image Checker')
        qtRectangle = QWidget.frameGeometry(self)  # this code is to attempt to centre the window.
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        window_position = (qtRectangle.topLeft().x(), qtRectangle.topLeft().y())  # up to here.
        window_size = (600, 400)

        self.window.setGeometry(*window_position, *window_size)

        widget_pos = {"combobox": (0, 0, 1, 2), "button_confirm": (0, 3),
                      "textbox_grid_density": (1, 1), "textbox_cutoff": (2, 1), "textbox_strfex": (3, 1),
                      "text_grid": (1, 0), "text_cutoff": (2, 0), "text_strxfex": (3, 0), "text_log": (1, 3, 5, 1),
                      "checkbox_pd": (4, 0, 1, 2), "checkbox_rj": (5, 0, 1, 2),
                      "progress_bar": (6, 0, 1, 4)}

        self.text_log.setLineWrapMode(QTextEdit.NoWrap)

        self.layout.addWidget(self.confirm_button, *widget_pos["button_confirm"])
        self.layout.addWidget(self.combobox, *widget_pos["combobox"])
        self.layout.addWidget(self.progress_bar, *widget_pos["progress_bar"])
        self.layout.addWidget(self.textbox_grid, *widget_pos["textbox_grid_density"])
        self.layout.addWidget(self.textbox_cutoff, *widget_pos["textbox_cutoff"])
        self.layout.addWidget(self.textbox_strfex, *widget_pos["textbox_strfex"])
        self.layout.addWidget(self.text_grid, *widget_pos["text_grid"])
        self.layout.addWidget(self.text_cutoff, *widget_pos["text_cutoff"])
        self.layout.addWidget(self.text_strfex, *widget_pos["text_strxfex"])
        self.layout.addWidget(self.text_log, *widget_pos["text_log"])
        self.layout.addWidget(self.checkbox_perfect_dupe, *widget_pos["checkbox_pd"])
        self.layout.addWidget(self.checkbox_remove_json, *widget_pos["checkbox_rj"])

        self.window.setLayout(self.layout)
        self.window.show()

    def combobox_info(self, _):
        self.folder_name = self.combobox.currentText()
        self.folder_index = self.combobox.currentIndex()

    def log_print(self, text):
        self.log += str(text) + "\n"
        self.text_log.setText(self.log)

    def progress_update(self, percentage: int):
        self.progress_bar.setValue(percentage)

    def button_confirm_pressed(self):

        self.log = str()  # clearing log
        self.text_log.setText(self.log)

        self.grid_density = int(self.textbox_grid.text())
        self.cutoff = int(self.textbox_cutoff.text())
        self.strfex = str(self.textbox_strfex.text())
        self.folder_index = self.combobox.currentIndex()

        if self.checkbox_remove_json.isChecked():
            self.toggle_rj = True
        else:
            self.toggle_rj = False
        if self.checkbox_perfect_dupe.isChecked():
            self.toggle_pd = True
        else:
            self.toggle_pd = False

        if self.grid_density > 20:
            self.log_print("Grid density is too high! Try a value of 20 or below.")

        self.run_worker()

    def run_worker(self):
        self.thread = QThread()
        self.worker = Worker(self.grid_density, self.cutoff, self.strfex,
                             self.toggle_rj, self.toggle_pd, self.folder_index)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.progress_update.connect(self.progress_update)
        self.worker.log_update.connect(self.log_print)
        self.thread.start()


class Worker(QObject):
    finished = pyqtSignal()
    progress_update = pyqtSignal(int)
    log_update = pyqtSignal(str)

    def __init__(self, grid_density, cutoff, strfex, toggle_rj, toggle_pd, folder_index):
        super().__init__()

        self.grid_density = grid_density
        self.cutoff = cutoff
        self.strfex = strfex
        self.toggle_rj = toggle_rj
        self.toggle_pd = toggle_pd
        self.folder_index = folder_index

    def run(self):

        emitters = {"progress_emit": self.progress_update, "log_emit": self.log_update}

        image_types = [".png", ".jpeg", ".jpg"]
        folders = [_.name for _ in Path.cwd().glob("*") if _.is_dir()]
        image_folder = Path(Path.cwd(), folders[self.folder_index])
        image_files = [_ for _ in image_folder.glob("*") if dil.f_type_return(_, image_types) in image_types]

        if len(image_files) == 0:
            self.log_update.emit("No images in this folder!")
            self.finished.emit()

        image_struct = dil.ImageStruct(directory=image_folder, emitters={"progress_bar": self.progress_update,
                                                                         "text_log": self.log_update})

        if not dil.check_json_exists(image_folder):
            dil.rename_to_num(image_folder, image_files, "_", image_types)
            image_files = [_.name for _ in image_folder.glob("*") if dil.f_type_return(_, image_types) in image_types]
            self.log_update.emit("Loading image hashes...")
            image_struct.generate_data(grid_density=self.grid_density, file_list=image_files)
        else:
            if self.toggle_rj:
                dil.rename_to_num(image_folder, image_files, "_", image_types)
                Path(image_folder, "hash_data", "fp_hash_data.json").unlink()  # removing/unlinking the json file
                image_files = [_.name for _ in image_folder.glob("*") if
                               dil.f_type_return(_, image_types) in image_types]
                self.log_update.emit("Loading image hashes")
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
