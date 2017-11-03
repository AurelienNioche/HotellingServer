from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QPushButton, QLabel, \
    QCheckBox, QLineEdit, QMessageBox, QHBoxLayout, QButtonGroup, QRadioButton
from utils.utils import Logger


class ParametersFrame(QWidget, Logger):

    name = "ParametersFrame"

    def __init__(self, parent, param):

        # noinspection PyArgumentList
        QWidget.__init__(self, parent=parent)

        self.param = param

        self.layout = QVBoxLayout()

        self.run_button = QPushButton("Run!")
        self.previous_button = QPushButton("Previous")

        self.group = QButtonGroup()

        self.group.addButton(self.previous_button)
        self.group.addButton(self.run_button)

        self.widgets = dict()

        self.error = None

        self.order = ["save",
                      "exploration_cost",
                      "utility_consumption",
                      "condition"]
        
        # These two depends on server class choice
        self.show_frame_assignment = None
        self.show_frame_game = None

        self.setup()

    def setup(self):
        
        param = self.param["parametrization"]

        self.widgets["save"] = \
            CheckParameter(text="Save results", checked=param["save"])

        self.widgets["exploration_cost"] = \
            IntParameter(text="Exploration cost",
                         initial_value=param["exploration_cost"], value_range=[0, 100])

        self.widgets["utility_consumption"] = \
            IntParameter(text="Utility consumption",
                         initial_value=param["utility_consumption"], value_range=[0, 100])

        self.widgets["condition"] = \
             IntParameter(text="Transportation Cost (high=1, low=0)", initial_value=0,
                value_range=[0, 1])

        self.fill_layout()

        # noinspection PyUnresolvedReferences
        self.run_button.clicked.connect(self.push_run_button)

        # noinspection PyUnresolvedReferences
        self.previous_button.clicked.connect(self.push_previous_button)
    
    def set_next_frame_previous_frame_methods(self, server_name):

        self.show_frame_assignment = (self.parent().show_frame_assignment_tcp, 
                self.parent().show_frame_assignment_php)[server_name == "PHPServer"]

        self.show_frame_game = (self.parent().tcp_run_game, 
                self.parent().php_run_game)[server_name == "PHPServer"]

    def fill_layout(self):

        # prepare layout
        grid_layout = QGridLayout()

        for i, key in enumerate(self.order):
            self.widgets[key].add_to_grid_layout(grid_layout, i, 0)

        horizontal_layout = QHBoxLayout()
        horizontal_layout.addWidget(self.previous_button, alignment=Qt.AlignCenter)
        horizontal_layout.addWidget(self.run_button, alignment=Qt.AlignCenter)

        self.layout.addLayout(grid_layout)
        self.layout.addLayout(horizontal_layout)

        self.setLayout(self.layout)

    def push_run_button(self):

        if self.error:

            self.show_warning(msg=self.error)

        else:
            self.log("Push 'run' button.")

            self.param["parametrization"] = self.get_widgets_values()
            self.parent().save_parameters("parametrization", self.param["parametrization"])
            self.parent().set_parametrization(self.param["parametrization"])

            # maybe one of those 2 methods: 
            # self.parent().tcp_run_game() / self.parent().php_run_game()
            self.show_frame_game()

    def push_previous_button(self):

        if self.error:

            self.show_warning(msg=self.error)

        else:
            self.log("Push 'previous' button.")
            
            # maybe one of those 2 methods: 
            # self.parent().show_frame_assignement_tcp/php()
            self.show_frame_assignment()

    def get_widgets_values(self):

        values = {}

        self.error = 0
        for parameter_name in self.widgets:

            value = self.widgets[parameter_name].get_value()
            if type(value) == str and value[0] == "!":

                self.error = value[1:]
                break
            else:
                values[parameter_name] = value

        return values

    def show_warning(self, **instructions):

        QMessageBox().warning(
            self, "", instructions["msg"],
            QMessageBox.Ok
        )

    def prepare(self):

        self.setFocus()
        self.run_button.setFocus()
        self.run_button.setEnabled(True)


class IntParameter(object):

    def __init__(self, text, initial_value, value_range):

        self.initial_value = initial_value
        self.value_range = value_range

        self.label = QLabel(text)
        self.edit = QLineEdit(str(initial_value))

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
