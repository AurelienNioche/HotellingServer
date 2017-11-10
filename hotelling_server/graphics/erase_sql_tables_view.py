from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QCheckBox,\
        QPushButton, QFormLayout, QLabel, QGroupBox
from PyQt5.QtCore import Qt


class EraseSQLTablesFrame(QWidget):

    name = "EraseSQLTablesFrame"

    def __init__(self, parent, param):

        super().__init__()

        self.parent = parent

        self.setWindowTitle("Erase sql tables")

        self.tables = param["sql_tables"]["table_names"]

        self.tables_check_boxes = dict()

        self.tables_group = QGroupBox("Select tables")

        self.ok_button = QPushButton("Ok")
        self.cancel_button = QPushButton("Cancel")

        self.layout = QVBoxLayout()

        self.setup()

    def setup(self):

        self.fill_layout()
        self.ok_button.clicked.connect(self.push_ok_button)
        self.cancel_button.clicked.connect(self.push_cancel_button)

    def fill_layout(self):

        form_layout = QFormLayout()

        for label in self.tables:
            self.tables_check_boxes[label] = QCheckBox()
            self.tables_check_boxes[label].setChecked(True)
            form_layout.addRow(QLabel(label), self.tables_check_boxes[label])

        form_layout.setFormAlignment(Qt.AlignCenter)
        form_layout.setAlignment(Qt.AlignCenter)
        form_layout.setLabelAlignment(Qt.AlignCenter)

        self.tables_group.setLayout(form_layout)

        horizontal_layout = QHBoxLayout()

        horizontal_layout.addWidget(self.ok_button, alignment=Qt.AlignRight)
        horizontal_layout.addWidget(self.cancel_button, alignment=Qt.AlignRight)

        self.layout.addWidget(self.tables_group)
        self.layout.addLayout(horizontal_layout)

        self.setLayout(self.layout)

    def push_cancel_button(self):

        self.cancel_button.setEnabled(False)

        self.hide()

        self.cancel_button.setEnabled(True)

    def push_ok_button(self):

        self.ok_button.setEnabled(False)

        checked_tables = [k for k, v in self.tables_check_boxes.items() if v.isChecked()]

        if checked_tables:
            self.parent.php_erase_sql_tables(checked_tables)

        self.hide()
        self.ok_button.setEnabled(True)
