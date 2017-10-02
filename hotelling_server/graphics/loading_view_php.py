from os import path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFileDialog, QGridLayout, \
    QLineEdit, QLabel, QHBoxLayout

from utils.utils import Logger


class LoadGameNewGameFramePHP(QWidget, Logger):

    name = "LoadGameNewGamePHP"

    def __init__(self, parent, param):

        super().__init__(parent=parent)
        
        self.layout = QVBoxLayout()
        self.buttons = dict()
        self.widgets = dict()
        self.param = param
        
        self.setup()
    
    def setup(self):

        self.fill_layout()

        self.buttons["new"].clicked.connect(self.click_new_game)
        self.buttons["load"].clicked.connect(self.click_load_game)

    def fill_layout(self):

        grid_layout = QGridLayout()

        self.widgets["php_server"] = QLineEdit()
        
        for i, (label, widget) in sorted(enumerate(self.widgets.items())):

            grid_layout.addWidget(QLabel(label), i, 0, alignment=Qt.AlignLeft)
            grid_layout.addWidget(widget, i, 1, alignment=Qt.AlignCenter)

        self.layout.addLayout(grid_layout)

        horizontal_layout = QHBoxLayout()

        self.buttons["new"] = QPushButton("New game")
        self.buttons["load"] = QPushButton("Load game")

        horizontal_layout.addWidget(self.buttons["new"], alignment=Qt.AlignCenter)
        horizontal_layout.addWidget(self.buttons["load"], alignment=Qt.AlignCenter)

        self.layout.addLayout(horizontal_layout)

        self.setLayout(self.layout)

    def prepare(self):

        self.setFocus()
        self.buttons["new"].setFocus()
        self.set_buttons_activation(True)
        self.prepare_network()

    def prepare_network(self):

        label = self.param["network"]["php_server"]
        self.widgets["php_server"].setText(label)

    def click_new_game(self):

        self.save_network_parameters()
        self.set_buttons_activation(False)
        self.parent().show_frame_assignment_php()

    def click_load_game(self):

        self.save_network_parameters()
        self.set_buttons_activation(False)
        self.open_file_dialog()

    def set_buttons_activation(self, value):

        for b in self.buttons.values():
            b.setEnabled(value)

    def open_file_dialog(self):

        folder_to_open = path.expanduser(self.param["folders"]["save"])

        # noinspection PyArgumentList
        file_choice = QFileDialog().getOpenFileName(
            self, '',
            folder_to_open,
            "Backup files (*.p)")
        self.log("User choose file '{}'.".format(file_choice))
        file = file_choice[0]
        if file:
            self.parent().load_game(file)

        else:
            self.set_buttons_activation(True)

    def save_network_parameters(self):

        self.param["network"]["php_server"] = self.widgets["php_server"].text()

        self.parent().set_server_parameters(self.param)
        self.parent().save_parameters("network", self.param["network"])
