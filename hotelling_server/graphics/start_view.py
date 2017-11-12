from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QGridLayout, \
    QLineEdit, QLabel, QHBoxLayout, QCheckBox, QGroupBox, QButtonGroup, QRadioButton

from utils.utils import Logger


class ParametersFrame:

    def __init__(self):

        self.widgets = {}
        self.layout = None

    def fill_layout(self):

        grid_layout = QGridLayout()

        for i, widget in sorted(enumerate(self.widgets.values())):
            widget.add_to_grid_layout(grid_layout, i, 0)

        self.layout = grid_layout

    def get_widgets_values(self):

        return {k: v.get_value() for k, v  in self.widgets.items()}


class NetworkParameters(ParametersFrame):

    def __init__(self, param):

        super().__init__()

        self.widgets["autostart"] = \
                CheckParameter(text="Autostart", checked=param["autostart"])

        self.widgets["php_server"] = \
                StringParameter(text="Server address", initial_value=param["php_server"])

        self.widgets["messenger"] = \
                StringParameter(text="Messenger address", initial_value=param["messenger"])

        self.widgets["missing_players"] = \
                IntParameter(text="Real players", initial_value=param["missing_players"], value_range=[0, 100])

        self.fill_layout()


class GameParameters(ParametersFrame):

    def __init__(self, param):

        super().__init__()

        self.widgets["save"] = \
            CheckParameter(text="Save results", checked=param["save"])

        self.widgets["exploration_cost"] = \
            IntParameter(text="Exploration cost",
                         initial_value=param["exploration_cost"], value_range=[0, 100])

        self.widgets["utility_consumption"] = \
            IntParameter(text="Utility consumption",
                         initial_value=param["utility_consumption"], value_range=[0, 100])

        self.widgets["condition"] = \
             RadioParameter(text="Transportation Cost", checked=param["condition"])


        self.fill_layout()


class StartFrame(QWidget, Logger):

    name = "StartFrame"

    def __init__(self, parent, param):

        super().__init__(parent=parent)

        self.layout = QVBoxLayout()

        self.buttons = dict()

        self.param = param

        self.game_frame = GameParameters(param=self.param["parametrization"])
        self.network_frame = NetworkParameters(param=self.param["network"])

        self.group_game = QGroupBox("Game parametrization")
        self.group_network = QGroupBox("Network parameters")

        self.setup()

    def setup(self):

        self.buttons["new"] = QPushButton("New game")

        self.fill_frames()
        self.fill_layout()

        self.buttons["new"].clicked.connect(self.push_new_game)

    def fill_frames(self):

        self.group_game.setLayout(self.game_frame.layout)
        self.group_network.setLayout(self.network_frame.layout)

    def fill_layout(self):

        self.layout.addWidget(self.group_network)
        self.layout.addWidget(self.group_game)

        horizontal_layout = QHBoxLayout()

        horizontal_layout.addWidget(self.buttons["new"], alignment=Qt.AlignCenter)

        self.layout.addLayout(horizontal_layout)

        self.setLayout(self.layout)

    def prepare(self):

        self.setFocus()
        self.buttons["new"].setFocus()
        self.set_buttons_activation(True)

    def push_new_game(self):

        self.log("Push 'new game' button.")

        # save interface parameters
        self.save_network_parameters()
        self.save_parametrization()

        # do stuff...
        self.erase_sql_tables()
        self.set_missing_players()

        self.set_buttons_activation(False)

        self.parent().show_frame_assignment_php()

    def set_buttons_activation(self, value):

        for b in self.buttons.values():
            b.setEnabled(value)

    def save_network_parameters(self):

        self.param["network"] = self.network_frame.get_widgets_values()

        self.parent().save_parameters("network", self.param["network"])
        self.parent().set_server_parameters(self.param)

    def save_parametrization(self):

        self.param["parametrization"] = self.game_frame.get_widgets_values()
        self.parent().save_parameters("parametrization", self.param["parametrization"])
        self.parent().set_parametrization(self.param["parametrization"])

    def set_missing_players(self):

        self.parent().set_missing_players(self.param["network"]["missing_players"])

    def erase_sql_tables(self):

        self.parent().check_for_erasing_tables()

    # ----------------------------------------  Widgets -------------------------------------------------------- #

class StringParameter:

    def __init__(self, text, initial_value):

        self.initial_value = initial_value

        self.label = QLabel(text)
        self.edit = QLineEdit(str(initial_value))
        self.edit.setFixedWidth(310)

    def get_value(self):

        return self.edit.text()

    def add_to_form_layout(self, layout):

        layout.addRow(self.label, self.edit)

    def add_to_grid_layout(self, layout, x, y):

        layout.addWidget(self.label, x, y, alignment=Qt.AlignCenter)
        layout.addWidget(self.edit, x, y + 1, alignment=Qt.AlignCenter)


class IntParameter:

    def __init__(self, text, initial_value, value_range):

        self.initial_value = initial_value
        self.value_range = value_range

        self.label = QLabel(text)
        self.edit = QLineEdit(str(initial_value))
        self.edit.setFixedWidth(310)

    def get_value(self):

        try:
            value = int(self.edit.text())

            if self.value_range[0] <= value <= self.value_range[1]:
                return value
            else:
                return "!Error: Value for '{}' should be an integer comprised in range {} - {}.".format(
                    self.label.text(), self.value_range[0], self.value_range[1]
                )

        except ValueError:

            return "!Error: Value given for '{}' should be an integer.".format(
                self.label.text()
            )

    def add_to_form_layout(self, layout):

        layout.addRow(self.label, self.edit)

    def add_to_grid_layout(self, layout, x, y):

        layout.addWidget(self.label, x, y, alignment=Qt.AlignCenter)
        layout.addWidget(self.edit, x, y + 1, alignment=Qt.AlignCenter)


class CheckParameter(object):

    def __init__(self, text, checked=True):

        self.label = QLabel(text)
        self.check_box = QCheckBox()

        self.check_box.setChecked(checked)

    def get_value(self):

        return self.check_box.isChecked()

    def add_to_form_layout(self, layout):

        layout.addRow(self.label, self.check_box)

    def add_to_grid_layout(self, layout, x, y):

        layout.addWidget(self.label, x, y, alignment=Qt.AlignCenter)
        layout.addWidget(self.check_box, x, y + 1, alignment=Qt.AlignLeft)


class RadioParameter:

    def __init__(self, text, checked):

        self.text = QLabel(text)

        self.layout = QHBoxLayout()

        self.group = QButtonGroup()
        self.high = QRadioButton()
        self.low = QRadioButton()

        if "low" in checked:
            self.low.setChecked(True)
        else:
            self.high.setChecked(True)

        self.label = {0: QLabel("low"), 1: QLabel("high")}

        self.setup()

    def setup(self):

        self.layout.addWidget(self.label[0])
        self.layout.addWidget(self.low)

        self.layout.addWidget(self.label[1])
        self.layout.addWidget(self.high)

        self.group.addButton(self.high)
        self.group.addButton(self.low)

    def get_value(self):

        return ("low_t_cost", "high_t_cost")[self.high.isChecked()]

    def add_to_grid_layout(self, layout, x, y):

        layout.addWidget(self.text, x, y, alignment=Qt.AlignLeft)
        layout.addLayout(self.layout, x, y + 1, alignment=Qt.AlignCenter)
