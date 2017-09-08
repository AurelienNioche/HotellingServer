from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QVBoxLayout, QLabel,
QMessageBox, QAbstractItemView, QGridLayout, QButtonGroup, QHBoxLayout, QProgressDialog, QLineEdit, QFormLayout,
QDialog)
from multiprocessing import Event

from utils.utils import Logger
import operator


class DevicesFrame(QWidget, Logger):

    name = "DevicesFrame"

    def __init__(self, parent):

        super().__init__(parent=parent)

        self.layout = QVBoxLayout()

        self.controller = parent.mod.controller

        self.quit_button = QPushButton()
        self.save_button = QPushButton()
        self.add_button = QPushButton()
        self.remove_button = QPushButton()
        self.scan_button = QPushButton()
        
        # window poppin to add a device 
        self.add_window = QDialog(self)
        self.add_window.setLayout(QVBoxLayout())
        self.add_window.setWindowTitle("Add a device")
        self.ok_button = QPushButton()
        self.cancel_button = QPushButton()

        self.table = QTableWidget()

        self.setup()

    def setup(self):

        self.setLayout(self.layout)
    
        self.fill_layout()

        self.fill_add_window_layout()

        # noinspection PyUnresolvedReferences
        self.quit_button.clicked.connect(self.push_quit_button)

        # noinspection PyUnresolvedReferences
        self.cancel_button.clicked.connect(self.push_cancel_button)

        # noinspection PyUnresolvedReferences
        self.ok_button.clicked.connect(self.push_ok_button)

        # noinspection PyUnresolvedReferences
        self.add_button.clicked.connect(self.push_add_button)

        # noinspection PyUnresolvedReferences
        self.save_button.clicked.connect(self.push_save_button)

        # noinspection PyUnresolvedReferences
        self.remove_button.clicked.connect(self.push_remove_button)

        # noinspection PyUnresolvedReferences
        self.scan_button.clicked.connect(self.push_scan_button)

    def fill_add_window_layout(self):

        form_layout = QFormLayout()

        self.server_id = QLineEdit()
        self.device_name = QLineEdit()

        form_layout.addRow(QLabel("Device name"), self.device_name)
        form_layout.addRow(QLabel("Server id"), self.server_id)

        horizontal_layout = QHBoxLayout()

        horizontal_layout.addWidget(self.ok_button, alignment=Qt.AlignRight)
        horizontal_layout.addWidget(self.cancel_button, alignment=Qt.AlignRight)

        self.add_window.layout().addLayout(form_layout)
        self.add_window.layout().addLayout(horizontal_layout)

    def fill_layout(self):

        # add tables
        self.layout.addWidget(self.table)

        # button layout :
        # | scan network  |
        # | remove | add  |
        # | quit | save |

        self.layout.addWidget(self.scan_button, stretch=0, alignment=Qt.AlignCenter)

        grid_layout = QGridLayout()

        horizontal_layout = QHBoxLayout()

        # in order to aggregate buttons in the center of the window
        horizontal_layout.addStretch(48)
        horizontal_layout.addLayout(grid_layout)
        horizontal_layout.addStretch(48)

        grid_layout.addWidget(self.remove_button, 0, 0, alignment=Qt.AlignCenter)
        grid_layout.addWidget(self.quit_button, 1, 0, alignment=Qt.AlignCenter)
        grid_layout.addWidget(self.add_button, 0, 1, alignment=Qt.AlignCenter)
        grid_layout.addWidget(self.save_button, 1, 1, alignment=Qt.AlignCenter)

        self.layout.addLayout(horizontal_layout)

    def prepare(self):

        self.log("Preparing...")
        self.prepare_buttons()
        self.prepare_table()
        self.log("Preparation done!")

    def prepare_buttons(self):
        
        # main window buttons
        self.quit_button.setText("Quit")
        self.add_button.setText("Add device")
        self.save_button.setText("Save")
        self.remove_button.setText("Remove device")
        self.scan_button.setText("Scan network for new devices...")

        # add device window buttons
        self.cancel_button.setText("Cancel")
        self.ok_button.setText("Ok")

    def push_ok_button(self):

        self.log("Push 'ok' button")
       
        n_rows = int(self.table.rowCount())
        self.table.insertRow(n_rows)
        self.table.setItem(n_rows, 0, QTableWidgetItem(self.device_name.text()))
        self.table.setItem(n_rows, 1, QTableWidgetItem(self.server_id.text()))

        mapping_to_check = self.get_new_mapping()[1]
        is_correct = self.check_mapping(mapping_to_check) 
        
        if is_correct:
            self.add_window.close()
        else:
            self.table.removeRow(n_rows)

        self.table.scrollToBottom()

    def push_cancel_button(self):

        self.add_window.close()

    def push_quit_button(self):

        self.log("Push 'quit' button")
        self.parent().devices_quit_without_saving()

    def push_add_button(self):

        self.log("Push 'add' button")
        self.add_window.show()

    def push_remove_button(self):
        self.log("Push 'remove device' button")

        if self.table.currentRow():
            self.table.removeRow(self.table.currentRow())
        else:
            self.show_info(msg="Please select a device to remove.")

    def push_scan_button(self):
        self.log("Push 'scan device' button")
        
        # get current json file mapping 
        old_data = len(self.controller.get_parameters("map_android_id_server_id"))
        
        self.controller.queue.put(("scan_network_for_new_devices", ))
        
        self.show_loading(msg="Scanning...")
        
        # load new json file mapping 
        self.controller.data.setup()
        
        # get the new config
        new_data = len(self.controller.get_parameters("map_android_id_server_id"))
        
        if old_data == new_data:
            self.show_warning(msg="No device found.")
        else:
            self.show_info(msg="Android device added.")

        self.prepare_table()

    def push_save_button(self):
        self.log("Push 'save' button")

        new_mapping, mapping_to_check = self.get_new_mapping()
        is_correct = self.check_mapping(mapping_to_check)

        if is_correct:

            self.write_map_android_id_server_id(new_mapping)
            self.show_info(msg="Mapping successfully saved in 'map_android_id_server_id.json'.")

            # update data
            self.controller.data.setup()

            self.parent().show_frame_load_game_new_game()

    def check_mapping(self, mapping_to_check):

        warning = self.check_mapping_validity(mapping_to_check)

        if warning:
            self.show_warning(msg=warning)

        else:
            return True

    def prepare_table(self):

        data = self.controller.get_parameters("map_android_id_server_id")

        sorted_data = sorted(data.items(), key=operator.itemgetter(1))

        labels = "Device name", "Server id"

        # set height and width
        self.table.setColumnCount(len(labels))
        self.table.setRowCount(len(sorted_data))

        # fit the widget
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # select whole rows when clicking
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)

        # set names
        for i in range(len(labels)):
            self.table.setHorizontalHeaderItem(i, QTableWidgetItem(labels[i]))

        self.fill_table(sorted_data)

    def fill_table(self, rows):

        for x, (name, server_id) in enumerate(rows):
            self.table.setItem(x, 0, QTableWidgetItem(str(name)))
            self.table.setItem(x, 1, QTableWidgetItem(str(server_id)))

    def get_new_mapping(self):

        n_rows = self.table.rowCount()

        item = self.table.item

        keys = [item(i, 0).text() if item(i, 0) else None for i in range(n_rows)]
        values = [item(i, 1).text() if item(i, 1) else None for i in range(n_rows)]

        mapping_to_check = list(enumerate(zip(keys, values)))
        new_mapping = {k: int(v) if str(v).isdigit() else v for k, v in zip(keys, values)}

        return new_mapping, mapping_to_check

    def write_map_android_id_server_id(self, new_mapping):

        self.controller.backup.save_param("map_android_id_server_id", new_mapping)

    @staticmethod
    def check_mapping_validity(mapping_to_check):

        for i, (k, v) in mapping_to_check:

            if not str(v).isdigit():
                return "Wrong input for server id '{}'.".format(v)

            for j, (other_k, other_v) in mapping_to_check:

                cond0 = k == other_k
                cond1 = v == other_v
                cond2 = i != j

                if cond0 and cond2 or cond1 and cond2:
                    return "Device already exist at row {}.".format(i + 1)

    def show_warning(self, **instructions):

        QMessageBox().warning(
            self, "warning", instructions["msg"],
            QMessageBox.Ok
        )

    def show_info(self, **instructions):

        QMessageBox().information(
            self, "info", instructions["msg"],
            QMessageBox.Ok
        )

    def show_loading(self, **instructions):

        self.progress_dialog = QProgressDialog(parent=self)
        self.progress_dialog.setWindowTitle("Hold on")
        self.progress_dialog.setModal(True)
        self.progress_dialog.setLabelText("Scanning...")
        self.progress_dialog.setMinimum(0)
        self.progress_dialog.setMaximum(0)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.exec_()

    def close_loading(self):

        self.progress_dialog.close()

