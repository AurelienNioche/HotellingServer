from threading import Thread, Event

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, \
    QGridLayout, QButtonGroup, QHBoxLayout, QLineEdit, QCheckBox, QRadioButton, \
    QScrollArea, QGroupBox

import numpy as np

from utils.utils import Logger


class AssignmentWidget(QWidget):

    """
    widget containing
    the assignment menu
    """

    name = "WaitingList"

    def __init__(self, labels, roles):

        super().__init__()

        self.layout = QGridLayout()

        self.roles = roles
        self.n_player = len(roles)

        self.labels = labels

        self.players = {}

        self.setup()

    def setup(self):

        for game_id, role in enumerate(self.roles):

            self.players[game_id] = {

                "name": StringParameter(parent=self, initial_value=""),

                "role": RadioParameter(parent=self, checked=role),

                "bot": CheckParameter(parent=self, checked=True),
            }

        self.fill_layout()

    def fill_layout(self):

        self.layout.setHorizontalSpacing(40)

        # add labels to the first row
        for y, label in enumerate(self.labels):
            self.layout.addWidget(QLabel(label.capitalize()), 0, y)

        # coordinates for player list (after first row)
        coordinates = ((x, y) for x in range(1, self.n_player + 1) for y in range(len(self.labels)))

        # fill layout
        for game_id in range(self.n_player):

            for key in ["name", "role", "bot"]:

                self.players[game_id][key].add_to_grid_layout(self.layout, *next(coordinates))

        self.setLayout(self.layout)

    def get_assignment(self):

        return {

            i: {

                "name": self.players[i]["name"].get_value(),
                "role": self.players[i]["role"].get_value(),
                "bot": self.players[i]["bot"].get_value(),

            }

            for i in range(self.n_player)
        }

    def set_missing_players(self, missing_players):

        for game_id in range(self.n_player):

            self.players[game_id]["name"].edit.setText("" if game_id < missing_players else "Bot")
            self.players[game_id]["bot"].check_box.setChecked(game_id >= missing_players)

    def set_participant(self, row, name):

        self.players[row]["name"].edit.setText(name)


class AssignmentFramePHP(Logger, QWidget):

    """
    Main frame
    containing the assignment widget
    + previous and run buttons
    """

    name = "AssignmentFramePHP"

    def __init__(self, parent, param):

        # noinspection PyArgumentList
        super().__init__(parent=parent)

        self.param = param

        self.layout = QVBoxLayout()

        self.next_button = QPushButton("Run!")
        self.previous_button = QPushButton("Previous")

        self.group = QButtonGroup()

        self.group.addButton(self.previous_button)
        self.group.addButton(self.next_button)

        # assignments widgets
        self.assignment_group = QGroupBox("Waiting for users to connect...")
        self.assignment_area = QScrollArea()

        # those attributs will be set in setup and prepare method
        self.assignment_widget = None
        self.missing_players = None
        self.timer = None
        self.autostart = None

        self.error = None

        self.setup()

    def setup(self):

        # noinspection PyUnusedLocal
        roles = \
            ["firm" for i in range(self.param["game"]["n_firms"])] \
            + ["customer" for i in range(self.param["game"]["n_customers"])]

        self.assignment_widget = AssignmentWidget(
            labels=("name", "firm  customer", "bot"),
            roles=roles
        )

        self.fill_layout()

        self.assignment_area.setFixedHeight(500)
        self.assignment_area.setFixedWidth(400)

        # noinspection PyUnresolvedReferences
        self.next_button.clicked.connect(self.push_next_button)
        # noinspection PyUnresolvedReferences
        self.previous_button.clicked.connect(self.push_previous_button)

        self.next_button.setAutoDefault(True)
        self.next_button.setDefault(True)

    def fill_layout(self):

        horizontal_layout = QHBoxLayout()
        horizontal_layout.addWidget(self.previous_button, alignment=Qt.AlignCenter)
        horizontal_layout.addWidget(self.next_button, alignment=Qt.AlignCenter)

        self.assignment_area.setWidget(self.assignment_widget)

        assignment_area_layout = QHBoxLayout()
        assignment_area_layout.addWidget(self.assignment_area, alignment=Qt.AlignCenter)

        self.assignment_group.setLayout(assignment_area_layout)

        self.layout.addWidget(self.assignment_group, alignment=Qt.AlignCenter)
        self.layout.addLayout(horizontal_layout)

        self.setLayout(self.layout)

    def prepare(self, param):

        # get params from interface
        self.missing_players = param["network"]["missing_players"]
        self.autostart = param["network"]["autostart"]

        self.assignment_widget.set_missing_players(self.missing_players)

        self.next_button.setEnabled(True)
        self.next_button.setFocus()
        self.setFocus()

        # update waiting list view
        self.timer = Timer(self, self.ask_for_updating_waiting_list, 1000)
        self.timer.start()

    # ---------------------- PUSH BUTTONS --------------------------------- #

    def push_next_button(self):

        warning = self.check_assignment_validity()

        if warning:
            self.parent().show_warning(msg=warning)

        else:
            self.log("Push 'next' button.")

            # get assignment
            self.param["assignment_php"] = self.assignment_widget.get_assignment()

            self.parent().save_parameters("assignment_php", self.param["assignment_php"])

            # set assignment and wait for controller to show game view
            self.parent().set_assignment(assignment=self.param["assignment_php"])

            # run game
            self.parent().php_run_game()

            # stop refreshing waiting list
            self.timer.stop()

    def push_previous_button(self):

        if self.error:

            self.parent().show_warning(msg=self.error)

        else:
            self.log("Push 'previous' button.")
            self.parent().show_frame_start()
            self.timer.stop()

    # ------------------------------------------------------------------------------- #

    def ask_for_updating_waiting_list(self):

        self.parent().php_scan_button()

    def update_waiting_list(self, participants):

        if participants:

            for i, name in enumerate(participants):
                self.assignment_widget.set_participant(row=i, name=name)

            # if autostart is set run the game
            if len(participants) == self.missing_players and self.autostart:
                self.push_next_button()

    # ----------------------------- assignment validity checking -------------------------------------------------- #

    def check_assignment_validity(self):

        assignment = self.assignment_widget.get_assignment().items()
        n_firm = 0
        non_bot = 0

        for i, player in assignment:

            n_firm += player["role"] == "firm"
            non_bot += player["name"] != "Bot"

            if not player["name"]:
                return "Players are still missing!"

        # after count is done...
        if non_bot != self.missing_players:
            return "More real players than expected!"

        if n_firm != self.param["game"]["n_firms"]:
            return "Bad role configuration!"

    # --------------------------------- Widgets used in assignment menu --------------------------------- #


class StringParameter:

    """
    name
    """

    def __init__(self, parent, initial_value):

        self.parent = parent

        self.initial_value = initial_value
        self.edit = QLineEdit(str(initial_value))
        self.edit.setEnabled(False)

    def get_value(self):

        return self.edit.text()

    def add_to_grid_layout(self, layout, x, y):

        layout.addWidget(self.edit, x, y, alignment=Qt.AlignCenter)


class RadioParameter:

    """
    role (firm/customer)
    """

    def __init__(self, parent, checked):

        self.parent = parent

        self.layout = QHBoxLayout()

        self.group = QButtonGroup()

        self.firm = QRadioButton()
        self.customer = QRadioButton()

        self.setup(checked)

    def setup(self, checked):

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


class CheckParameter:

    """
    bot or not
    """

    def __init__(self, parent, checked):
        self.parent = parent
        self.check_box = QCheckBox()
        self.setup(checked)

    def setup(self, checked):

        self.check_box.setChecked(checked)
        self.check_box.setEnabled(False)

    def get_value(self):
        return self.check_box.isChecked()

    def add_to_grid_layout(self, layout, x, y):
        layout.addWidget(self.check_box, x, y)


class Timer(Thread):

    """
    used in order
    to refresh participant list
    """

    def __init__(self, parent, func, interval):

        super().__init__()
        self.interval = interval
        self.func = func
        self._parent = parent

    def stop(self):
        self._is_stopped = True

    def stopped(self):
        return self._is_stopped

    def parent(self):
        return self._parent

    def run(self):

        while not self.stopped():

            try:
                self.func()
                Event().wait(np.random.randint(2))
            except:
                Event().wait(np.random.randint(2))
