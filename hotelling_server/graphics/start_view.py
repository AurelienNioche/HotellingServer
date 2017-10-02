from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton

from utils.utils import Logger
from hotelling_server.control import php_server, tcp_server


class StartFrame(QWidget, Logger):

    name = "StartFrame"

    def __init__(self, parent):

        super().__init__(parent=parent)

        self.controller_queue = self.parent().controller_queue

        self.layout = QVBoxLayout()
        self.buttons = dict()

        self.setup()

    def setup(self):

        self.fill_layout()

        self.buttons["tcp_server"].clicked.connect(self.click_tcp_server)
        self.buttons["php_server"].clicked.connect(self.click_php_server)

    def fill_layout(self):

        self.buttons["tcp_server"] = QPushButton("TCP server")
        self.buttons["php_server"] = QPushButton("PHP server")
        
        for key, value in self.buttons.items():
            self.layout.addWidget(value, alignment=Qt.AlignCenter)

        self.setLayout(self.layout)

    def prepare(self):

        self.setFocus()
        self.set_buttons_activation(True)

    def click_php_server(self):

        self.set_buttons_activation(False)
        self.parent().show_frame_load_game_new_game_php()
        self.controller_queue.put(("ui_set_server", php_server.PHPServer))

    def click_tcp_server(self):

        self.set_buttons_activation(False)
        self.parent().show_frame_load_game_new_game_tcp()
        self.controller_queue.put(("ui_set_server", tcp_server.TCPServer))

    def set_buttons_activation(self, value):

        for b in self.buttons.values():
            b.setEnabled(value)
