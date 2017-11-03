from PyQt5.QtWidgets import QWidget, QTabWidget, QFormLayout, QLabel, \
        QLineEdit, QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox


from utils.utils import Logger


class MissingPlayersFrame(QWidget):

    name = "MissingPlayersFrame"

    def __init__(self, parent, param):
        
        super().__init__()
        
        self._parent = parent
        self.setWindowTitle("Set missing players variable manually")
        self.param = param

        self.update_button = QPushButton("Update table")

        self.missing_player_value = QLineEdit()

        self.setup()

    def parent(self):
        return self._parent

    def setup(self):
    
        self.fill_layout()

        self.missing_player_value.setText(
                str(self.param["game"]["n_firms"]))

        # noinspection PyUnresolvedReferences
        self.update_button.clicked.connect(self.push_update_button)

        self.update_button.setDefault(True)

    def fill_layout(self):

        vertical_layout = QVBoxLayout()

        form_layout = QFormLayout()
        
        form_layout.addRow(QLabel("missing players"), self.missing_player_value)

        vertical_layout.addLayout(form_layout)

        vertical_layout.addWidget(self.update_button)

        self.setLayout(vertical_layout)

    def push_update_button(self):
        
        self.parent().set_missing_players(self.missing_player_value.text())
        self.hide()





