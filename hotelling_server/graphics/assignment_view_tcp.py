from PyQt5.QtCore import Qt, QObject, QEvent
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QCheckBox, \
    QLineEdit, QMessageBox, QGridLayout, QRadioButton, QButtonGroup, QHBoxLayout

from utils.utils import Logger


class AssignmentFrameTCP(Logger, QWidget):
    name = "AssignmentFrameTCP"

    def __init__(self, parent, param):

        # noinspection PyArgumentList
        super().__init__(parent=parent)

        self.param = param
        self.layout = QVBoxLayout()

        self.next_button = QPushButton("Next")
        self.previous_button = QPushButton("Previous")

        self.group = QButtonGroup()

        self.group.addButton(self.previous_button)
        self.group.addButton(self.next_button)

        self.parameters = dict()

        self.error = None

        self.setup_done = False
        self.setup()

    def setup(self):

        # noinspection PyUnusedLocal
        roles = \
            ["firm" for i in range(self.param["game"]["n_firms"])] \
            + ["customer" for i in range(self.param["game"]["n_customers"])]

        n_agents = len(roles)

        labels = ("Server id", "Firm " + " Customer", "Bot")

        # noinspection PyUnusedLocal
        self.parameters["assign"] = [[] for i in range(n_agents)]

        # ----- check if an old config exists --------- #

        old_assign = self.param["assignment_tcp"]

        if len(old_assign) != len(self.parameters["assign"]):
            self.show_warning(msg="assignment_tcp.json not matching game.json config file!")
            self.new_setup(n_agents, roles)
        else:
            self.load_setup(old_assign)

        # --------- fill layout ----------------------------------- #

        self.fill_layout(labels, n_agents)

        # noinspection PyUnresolvedReferences
        self.next_button.clicked.connect(self.push_next_button)
        # noinspection PyUnresolvedReferences
        self.previous_button.clicked.connect(self.push_previous_button)

        self.setup_done = True

    def fill_layout(self, labels, n_agents):

        # prepare layout
        grid_layout = QGridLayout()

        # add labels
        for y, label in enumerate(labels):
            grid_layout.addWidget(QLabel(label), 0, y)

        # grid layout coordinates
        coordinates = [(x, y) for x in range(1, n_agents + 1) for y in range(len(labels))]

        # parameters index
        index = [(i, j) for i in range(n_agents) for j in range(len(labels))]

        for (i, j), (x, y) in zip(index, coordinates):
            self.parameters["assign"][i][j].add_to_grid_layout(grid_layout, x, y)

        horizontal_layout = QHBoxLayout()
        horizontal_layout.addWidget(self.previous_button, alignment=Qt.AlignCenter)
        horizontal_layout.addWidget(self.next_button, alignment=Qt.AlignCenter)

        self.layout.addLayout(grid_layout)
        self.layout.addLayout(horizontal_layout)

        self.setLayout(self.layout)

    def load_setup(self, assignment):

        for i, (server_id, role, bot) in enumerate(assignment):
            self.parameters["assign"][i].append(IntParameter(parent=self, value=server_id, idx=i))

            self.parameters["assign"][i].append(RadioParameter(checked=role))

            self.parameters["assign"][i].append(CheckParameter(parent=self, checked=bot, idx=i))

    def new_setup(self, n_agents, roles):

        for i in range(n_agents):
            self.parameters["assign"][i].append(IntParameter(parent=self, value="Bot", idx=i))

            self.parameters["assign"][i].append(RadioParameter(checked=roles[i]))

            self.parameters["assign"][i].append(CheckParameter(parent=self, checked=True, idx=i))

    def push_next_button(self):

        warning = self.check_assignment_validity()

        if warning:
            self.show_warning(msg=warning)

        else:
            self.log("Push 'next' button.")
            
            self.param["assignment_tcp"] = self.get_parameters()
            self.parent().save_parameters("assignment_tcp", self.param["assignment_tcp"])
            self.parent().set_assignment(assignment=self.param["assignment_tcp"])
            self.parent().show_frame_parametrization()

    def push_previous_button(self):

        if self.error:

            self.show_warning(msg=self.error)

        else:
            self.log("Push 'previous' button.")
            self.parent().show_frame_load_game_new_game_tcp()

    def check_assignment_validity(self):

        assignment = list(enumerate(self.get_parameters()))

        for i, (server_id, role, bot) in assignment:

            if server_id != "Bot" and not server_id.isdigit():
                return "Wrong input: '{}'.".format(server_id)

            for j, (other_id, other_role, other_bot) in assignment:

                if other_id == server_id and other_id != "Bot" and i != j:
                    return "Two identical inputs: '{}'.".format(server_id)

    def get_parameters(self):
        return [[i.get_value(), j.get_value(), k.get_value()] for i, j, k in self.parameters["assign"]]

    def show_warning(self, **instructions):

        QMessageBox().warning(
            self, "", instructions["msg"],
            QMessageBox.Ok
        )

    def switch_line_edit(self, idx, from_line):

        if self.setup_done:

            # get desired widgets
            line_edit = self.parameters["assign"][idx][0].edit
            check_box = self.parameters["assign"][idx][2].check_box

            # if line edit (containing server ids) is not enabled
            if not line_edit.isEnabled():
                self.enable_line_edit(line_edit, check_box)

            # if line edit is enabled and signal comes from check box
            elif line_edit.isEnabled() and not from_line:
                self.disable_line_edit(line_edit)

    @staticmethod
    def disable_line_edit(line_edit):

        line_edit.setText("Bot")
        line_edit.setEnabled(False)
        line_edit.setStyleSheet(line_edit.greyed_style)

    @staticmethod
    def enable_line_edit(line_edit, check_box, name=""):

        check_box.setChecked(False)
        line_edit.setEnabled(True)
        line_edit.setText(name)
        line_edit.setStyleSheet("")
        line_edit.setFocus(True)

    def prepare(self):

        self.setFocus()
        self.next_button.setFocus()
        self.next_button.setEnabled(True)

        # --------------------------------- Widgets used in assignment menu --------------------------------- #


class RadioParameter(object):
    """role (firm/customer)"""

    def __init__(self, checked):

        self.layout = QHBoxLayout()

        self.group = QButtonGroup()

        self.firm = QRadioButton()
        self.customer = QRadioButton()

        self.setup(checked)

    def setup(self, checked):

        if checked == "customer":
            self.customer.setChecked(True)
            self.customer.setEnabled(False)
            self.firm.setEnabled(False)
        else:
            self.firm.setChecked(True)
            self.firm.setEnabled(False)
            self.customer.setEnabled(False)

        self.group.addButton(self.firm)
        self.group.addButton(self.customer)

        self.layout.addWidget(self.firm)
        self.layout.addWidget(self.customer)

    def get_value(self):

        return ("customer", "firm")[self.firm.isChecked()]

    def add_to_grid_layout(self, layout, x, y):

        layout.addLayout(self.layout, x, y)


class IntParameter(object):
    """server_id"""

    def __init__(self, parent, value, idx):

        self.idx = idx
        self.edit = QLineEdit(str(value))
        self.edit.greyed_style = '''color: #808080;
                              background-color: #F0F0F0;
                              border: 1px solid #B0B0B0;
                              border-radius: 2px;'''

        self.filter = MouseClick(parent, idx)
        self.setup(value)

    def setup(self, value):

        if value == "Bot":
            self.edit.setEnabled(False)
            self.edit.setStyleSheet(self.edit.greyed_style)
        else:
            self.edit.setEnabled(True)

        self.edit.installEventFilter(self.filter)

    def get_value(self):

        return self.edit.text()

    def add_to_grid_layout(self, layout, x, y):

        layout.addWidget(self.edit, x, y, alignment=Qt.AlignCenter)


class CheckParameter(object):
    """bot or not"""

    def __init__(self, parent, checked, idx):
        self.parent = parent
        self.idx = idx
        self.check_box = QCheckBox()
        self.setup(checked)

    def setup(self, checked):
        # noinspection PyUnresolvedReferences
        self.check_box.stateChanged.connect(
            lambda: self.parent.switch_line_edit(idx=self.idx, from_line=False))

        self.check_box.setChecked(checked)

    def get_value(self):
        return self.check_box.isChecked()

    def add_to_grid_layout(self, layout, x, y):
        layout.addWidget(self.check_box, x, y)


class MouseClick(QObject):
    """class used in order
    to detect if QLineEdit widget
    has been clicked"""

    def __init__(self, parent, idx):
        super().__init__()
        self.idx = idx
        self.parent = parent

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            self.parent.switch_line_edit(idx=self.idx, from_line=True)
            return True

        return False
