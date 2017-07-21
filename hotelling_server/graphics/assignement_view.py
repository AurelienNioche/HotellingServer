from PyQt5.QtCore import Qt, QObject, QEvent
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QPushButton,
        QLabel, QCheckBox, QLineEdit, QMessageBox, QGridLayout, QRadioButton, QButtonGroup, QHBoxLayout)

from utils.utils import Logger


class AssignementFrame(QWidget, Logger):

    name = "AssignementFrame"

    def __init__(self, parent):

        # noinspection PyArgumentList
        QWidget.__init__(self, parent=parent)

        self.layout = QVBoxLayout()
        self.next_button = QPushButton("Next")
        self.parameters = dict()

        self.error = None
        
        self.setup_done = False 
        self.setup()

    def setup(self):

        game_param = self.parent().get_game_parameters()

        roles = ["firm" for i in range(game_param["n_firms"])] \
                + ["customer" for i in range(game_param["n_customers"])]

        n_agents = len(roles)

        labels = "Server id", "Firm " + " Customer", "Bot"

        self.parameters["assign"] = [[] for i in range(n_agents)]
        
        # ----- check if an old config exists --------- #

        old_assign = self.parent().mod.controller.data.param["assignement"]

        if len(old_assign) != len(self.parameters["assign"]):
            self.show_warning(msg="assignement.json not matching game.json config file!")
            self.new_setup(n_agents, roles)
        else:
            self.load_setup(old_assign)

        # --------- fill layout ----------------------------------- #

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

        self.layout.addLayout(grid_layout)
        self.layout.addWidget(self.next_button, alignment=Qt.AlignCenter)

        self.setLayout(self.layout)

        self.next_button.clicked.connect(self.push_next_button)

        self.setup_done = True

    def load_setup(self, assignement):

        for i, (server_id, role, bot) in enumerate(assignement):

            self.parameters["assign"][i].append(IntParameter(parent=self, value=server_id, idx=i))

            self.parameters["assign"][i].append(RadioParameter(checked=role))

            self.parameters["assign"][i].append(CheckParameter(parent=self,
                checked=bot, idx=i))

    def new_setup(self, n_agents, roles):

        for i in range(n_agents):

            self.parameters["assign"][i].append(IntParameter(parent=self, value="Bot", idx=i))

            self.parameters["assign"][i].append(RadioParameter(checked=roles[i]))

            self.parameters["assign"][i].append(CheckParameter(parent=self,
                checked=True, idx=i))

    def push_next_button(self):

        self.next_button.setEnabled(False)

        if self.error:

            self.show_warning(msg=self.error)

        else:
            self.log("Push 'next' button.")

            self.parent().show_frame_parameters()

    def get_parameters(self):
        return [[i.get_value(), j.get_value(), k.get_value()] for i, j, k in self.parameters["assign"]]
    
    def show_warning(self, **instructions):

        QMessageBox().warning(
            self, "", instructions["msg"],
            QMessageBox.Ok
        )

    def switch_check_box(self, idx):

        if self.setup_done:

            line_edit = self.parameters["assign"][idx][0].edit

            if line_edit.isEnabled():
                line_edit.setText("Bot")
                line_edit.setEnabled(False)
                line_edit.setStyleSheet(line_edit.greyed_style)

            elif not line_edit.isEnabled():
                line_edit.setEnabled(True)
                line_edit.setText("")
                line_edit.setStyleSheet("")

    def switch_line_edit(self, idx):

        if self.setup_done:

            line_edit = self.parameters["assign"][idx][0].edit
            check_box = self.parameters["assign"][idx][2].check_box

            if not line_edit.isEnabled():
                line_edit.setEnabled(True)
                line_edit.setText("")
                line_edit.setStyleSheet("")
                line_edit.setFocus(True)
                check_box.setChecked(False)

    def prepare(self):

        self.setFocus()
        self.next_button.setFocus()
        self.next_button.setEnabled(True)


class RadioParameter(object):

    def __init__(self, checked):

        self.layout = QHBoxLayout()

        self.group = QButtonGroup()

        self.firm = QRadioButton()
        self.customer = QRadioButton()

        if checked == "customer":
            self.customer.setChecked(True)
        else:
            self.firm.setChecked(True)

        self.group.addButton(self.firm)
        self.group.addButton(self.customer)

        self.layout.addWidget(self.firm)
        self.layout.addWidget(self.customer)

    def get_value(self):

        return ("customer", "firm")[self.firm.isChecked()]

    def add_to_grid_layout(self, layout, x, y):

        layout.addLayout(self.layout, x, y)


class IntParameter(object):

    def __init__(self, parent, value, idx):

        self.idx = idx
        self.edit = QLineEdit(str(value))

        self.edit.greyed_style = '''color: #808080;
                              background-color: #F0F0F0;
                              border: 1px solid #B0B0B0;
                              border-radius: 2px;'''

        self.filter = MouseMoved(parent, idx)
        self.edit.installEventFilter(self.filter)

        if value == "Bot":
            self.edit.setStyleSheet(self.edit.greyed_style)
            self.edit.setEnabled(False)
        else:
            self.edit.setEnabled(True)

    def get_value(self):

        return self.edit.text()

    def add_to_grid_layout(self, layout, x, y):

        layout.addWidget(self.edit, x, y)


class CheckParameter(object):

    def __init__(self, parent, checked, idx):

        self.parent = parent
        self.idx = idx
        self.check_box = QCheckBox()

        self.check_box.stateChanged.connect(
                lambda: self.parent.switch_check_box(self.idx))

        self.check_box.setChecked(checked)

    def get_value(self):

        return self.check_box.isChecked()

    def add_to_grid_layout(self, layout, x, y):

        layout.addWidget(self.check_box, x, y)


class MouseMoved(QObject):

    def __init__(self, parent, idx):
        super().__init__()
        self.idx = idx
        self.parent = parent

    def eventFilter(self, obj, event):

        if event.type() == QEvent.MouseButtonPress:
            self.parent.switch_line_edit(self.idx)
            return True

        return False
      
