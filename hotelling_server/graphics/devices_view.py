from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget, QPushButton, QTableWidget, QTableWidgetItem, \
    QHeaderView, QVBoxLayout, QLabel, QMessageBox, QAbstractItemView, QGridLayout, \
    QHBoxLayout, QLineEdit, QFormLayout, QProgressBar, QDialog

from utils.utils import Logger
import operator


class DevicesFrame(QWidget, Logger):

    name = "DevicesFrame"

    def __init__(self, parent, param):

        super().__init__(parent=parent)

        self.param = param

        self.layout = QVBoxLayout()

        self.quit_button = QPushButton()
        self.save_button = QPushButton()
        self.add_button = QPushButton()
        self.remove_button = QPushButton()
        self.scan_button = QPushButton()
        
        # Window popping to add a device
        self.add_window = QDialog(self)
        self.add_window.setLayout(QVBoxLayout())
        self.add_window.setWindowTitle("Add a device")
        
        self.progress_bar = QProgressBar()
        self.label_scanning = QLabel("Scanning...")

        self.add_manually_button = QPushButton()
        self.ok_button = QPushButton()
        self.cancel_button = QPushButton()
        self.cancel_scanning_button = QPushButton()

        self.scanning_widgets = [
            self.progress_bar,
            self.label_scanning,
            self.add_manually_button,
            self.cancel_scanning_button]
        
        self.timer = QTimer()
        # noinspection PyUnresolvedReferences
        self.timer.timeout.connect(self.show_no_device_found)

        self.max_scanning_time = 15000  # ms

        self.table = QTableWidget()
        self.form_layout = QFormLayout()

        self.server_id = QLineEdit()
        self.device_name = QLineEdit()

        self.setup()

    def setup(self):

        self.setLayout(self.layout)
        
        # ---------------- main frame ------------------------------------ # 
        self.fill_layout()

        # noinspection PyUnresolvedReferences
        self.quit_button.clicked.connect(self.push_quit_button)

        # noinspection PyUnresolvedReferences
        self.add_button.clicked.connect(self.push_add_button)

        # noinspection PyUnresolvedReferences
        self.save_button.clicked.connect(self.push_save_button)

        # noinspection PyUnresolvedReferences
        self.remove_button.clicked.connect(self.push_remove_button)

        # ---------------- add  device window ------------------------------------ # 

        self.fill_add_window_layout()

        # noinspection PyUnresolvedReferences
        self.ok_button.clicked.connect(self.push_ok_button)

        # noinspection PyUnresolvedReferences
        self.cancel_button.clicked.connect(self.push_cancel_button)

        # noinspection PyUnresolvedReferences
        self.cancel_scanning_button.clicked.connect(self.push_cancel_scanning_button)

        # noinspection PyUnresolvedReferences
        self.add_manually_button.clicked.connect(self.push_add_manually_button)

        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)
        self.progress_bar.setMinimumWidth(200)

    def fill_add_window_layout(self):

        self.form_layout.addRow(QLabel("Device name"), self.device_name)
        self.form_layout.addRow(QLabel("Server id"), self.server_id)

        horizontal_layout = QHBoxLayout()

        horizontal_layout.addWidget(self.ok_button, alignment=Qt.AlignRight)
        horizontal_layout.addWidget(self.cancel_button, alignment=Qt.AlignRight)

        self.add_window.layout().addLayout(self.form_layout)
        self.add_window.layout().addLayout(horizontal_layout)

        self.add_window.layout().addWidget(self.label_scanning, alignment=Qt.AlignCenter)
        self.add_window.layout().addWidget(self.progress_bar, alignment=Qt.AlignCenter)
        self.add_window.layout().addWidget(self.add_manually_button, alignment=Qt.AlignBottom)
        self.add_window.layout().addWidget(self.cancel_scanning_button, alignment=Qt.AlignBottom)

    def fill_layout(self):

        # add tables
        self.layout.addWidget(self.table)

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
        self.quit_button.setText("Cancel")
        self.add_button.setText("Add device")
        self.save_button.setText("Save and quit")
        self.remove_button.setText("Remove device")

        # add device window buttons
        self.cancel_button.setText("Cancel")
        self.cancel_scanning_button.setText("Cancel")
        self.ok_button.setText("Ok")
        self.add_manually_button.setText("Enter manually")

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
            self.table.scrollToBottom()
        else:
            self.table.removeRow(n_rows)

    def push_cancel_scanning_button(self): 

        self.log("Push 'cancel scanning' button")
        self.timer.stop()
        self.add_window.close()

    def push_cancel_button(self):

        self.log("Push 'cancel add device' button")
        self.add_window.close()

    def push_quit_button(self):

        self.log("Push 'quit' button")

        self.parent().devices_quit_without_saving()

    def push_add_button(self):

        self.log("Push 'add' button")
        
        ip = self.param["network"]["ip_address"]
        self.label_scanning.setText("Scanning with ip '{}' ...".format(ip))

        self.show_scanning()
        self.hide_add_form()
        self.add_window.show()

    def push_add_manually_button(self):

        self.log("Push 'add add_manually_button' button")
        
        self.timer.stop()

        self.hide_scanning()
        self.show_add_form()

    def push_remove_button(self):
        self.log("Push 'remove device' button")

        if self.table.currentRow():
            self.table.removeRow(self.table.currentRow())
        else:
            self.show_info(msg="Please select a device to remove.")

    def launch_scan(self):
        
        self.timer.start(self.max_scanning_time)

        self.parent().scan_network_for_new_devices()
        
    def push_save_button(self):

        self.log("Push 'save' button")

        success = self.save_mapping()
        
        if success:

            self.show_info(msg="Mapping successfully saved in 'map_android_id_server_id.json'.")

            self.parent().show_frame_load_game_new_game_tcp()

    def check_mapping(self, mapping_to_check):

        warning = self.check_mapping_validity(mapping_to_check)

        if warning:
            self.show_warning(msg=warning)

        else:
            return 1

    def prepare_table(self):

        data = self.param["map_android_id_server_id"]

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
                    return "Device already exists at row {}.".format(i + 1)

    def save_mapping(self):

        new_mapping, mapping_to_check = self.get_new_mapping()
        is_correct = self.check_mapping(mapping_to_check)

        if is_correct:

            self.write_map_android_id_server_id(new_mapping)

            return 1

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

    def show_no_device_found(self):
       
        self.show_warning(msg="No device found.")
        self.add_window.close()
        self.timer.stop()

    def show_device_added(self):

        self.show_info(msg="New device added.")
        self.add_window.close()
        self.timer.stop()
        self.prepare_table()

    def hide_add_form(self):

        for widget in range(self.form_layout.count()):
            self.form_layout.itemAt(widget).widget().hide()

        self.ok_button.hide()
        self.cancel_button.hide()

    def show_add_form(self):

        for widget in range(self.form_layout.count()):
            self.form_layout.itemAt(widget).widget().show()

        self.ok_button.show()
        self.cancel_button.show()

    def hide_scanning(self):

        for widget in self.scanning_widgets:
            widget.hide()

    def show_scanning(self):
        
        for widget in self.scanning_widgets:
            widget.show()

    def write_map_android_id_server_id(self, new_mapping):

        self.parent().write_parameters("map_android_id_server_id", new_mapping)


