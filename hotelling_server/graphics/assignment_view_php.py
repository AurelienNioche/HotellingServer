from PyQt5.QtCore import Qt, QObject, QEvent
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, \
    QGridLayout, QButtonGroup, QHBoxLayout, QLineEdit, QCheckBox, QRadioButton, \
    QScrollArea, QMessageBox, QFormLayout, QDialog, QGroupBox

from threading import Thread, Event
import numpy as np

from utils.utils import Logger



class AssignmentFramePHP(Logger, QWidget):
    name = "AssignmentFramePHP"

    def __init__(self, parent, param):

        # noinspection PyArgumentList
        super().__init__(parent=parent)
        
        self.param = param

        self.layout = QVBoxLayout()

        self.next_button = QPushButton("Next")
        self.previous_button = QPushButton("Previous")
        self.erase_tables_button = QPushButton("Erase SQL tables")
        self.missing_players_button = QPushButton("Set missing players")

        self.group = QButtonGroup()

        self.group.addButton(self.previous_button)
        self.group.addButton(self.next_button)
        self.group.addButton(self.erase_tables_button)
        
        # assignments widgets (list of game id, server id, role, bot)
        self.list_group = QGroupBox("Set assignments")
        self.list_widget = QWidget()
        self.list_scroll_area = QScrollArea()

        self.timer = None 
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

        labels = ("Game id", "Name", "Firm " + " Customer", "Bot")

        # noinspection PyUnusedLocal
        self.parameters["assign"] = [{} for i in range(n_agents)]

        self.new_setup(n_agents=n_agents, roles=roles)
        
        # --------- fill layout ----------------------------------- #

        self.fill_layout(labels, n_agents)

        self.list_scroll_area.setFixedHeight(500)
        self.list_scroll_area.setFixedWidth(500)

        # noinspection PyUnresolvedReferences
        self.next_button.clicked.connect(self.push_next_button)
        # noinspection PyUnresolvedReferences
        self.previous_button.clicked.connect(self.push_previous_button)
        # noinspection PyUnresolvedReferences
        self.erase_tables_button.clicked.connect(self.push_erase_tables_button)
        # noinspection PyUnresolvedReferences
        self.missing_players_button.clicked.connect(self.push_missing_players_button)

        self.next_button.setAutoDefault(True)
        self.next_button.setDefault(True)

        self.setup_done = True

    def fill_layout(self, labels, n_agents):
        
        # prepare layout
        grid_layout = QGridLayout()

        # add labels
        for y, label in enumerate(labels):
            grid_layout.addWidget(QLabel(label), 0, y)

        keys = ("game_id", "server_id", "role", "bot")

        # grid layout coordinates
        coordinates = [(x, y) for x in range(1, n_agents + 1) for y in range(len(keys))]

        # parameters index
        index = [(i, j) for i in range(n_agents) for j in keys]

        for (i, j), (x, y) in zip(index, coordinates):
            self.parameters["assign"][i][j].add_to_grid_layout(grid_layout, x, y)

        horizontal_layout = QHBoxLayout()
        horizontal_layout.addWidget(self.previous_button, alignment=Qt.AlignCenter)
        horizontal_layout.addWidget(self.next_button, alignment=Qt.AlignCenter)
        
        self.list_widget.setLayout(grid_layout)
        self.list_scroll_area.setWidget(self.list_widget)

        list_scroll_area_layout = QHBoxLayout()
        list_scroll_area_layout.addWidget(self.list_scroll_area)

        self.list_group.setLayout(list_scroll_area_layout)

        self.layout.addWidget(self.list_group, alignment=Qt.AlignCenter)
        self.layout.addLayout(horizontal_layout)
        
        self.layout.addWidget(self.missing_players_button, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.erase_tables_button, alignment=Qt.AlignCenter)

        self.setLayout(self.layout)

    def prepare(self):
        
        self.next_button.setEnabled(True)
        self.next_button.setFocus()
        self.setFocus()
        self.timer = Timer(self, self.ask_for_updating_waiting_list, 1000)
        self.timer.start()

    def new_setup(self, n_agents, roles):

        for i in range(n_agents):
            self.parameters["assign"][i]["game_id"] = IntParameter(parent=self, 
                value=i, idx=i)
            
            self.parameters["assign"][i]["server_id"] = IntParameter(parent=self,
                value="Bot", idx=i)

            self.parameters["assign"][i]["role"] = RadioParameter(parent=self,
                checked=roles[i], idx=i)

            self.parameters["assign"][i]["bot"] = CheckParameter(parent=self,
                checked=True, idx=i)

    # ---------------------- PUSH BUTTONS --------------------------------- #

    def push_next_button(self):

        warning = self.check_assignment_validity()

        if warning:
            self.show_warning(msg=warning)

        else:
            self.log("Push 'next' button.")
                  
            self.param["assignment_php"] = self.get_parameters()
            self.parent().save_parameters("assignment_php", self.param["assignment_php"])
            self.parent().set_assignment(assignment=self.param["assignment_php"])
            self.parent().show_frame_parametrization()
            self.timer.stop()

    def push_previous_button(self):

        if self.error:

            self.show_warning(msg=self.error)

        else:
            self.log("Push 'previous' button.")
            self.parent().show_frame_load_game_new_game_php()

    def push_erase_tables_button(self):

        self.erase_tables_button.setEnabled(False)

        self.parent().show_menubar_frame_erase_sql_tables()

        self.erase_tables_button.setEnabled(True)

    def push_missing_players_button(self):

        self.missing_players_button.setEnabled(False)

        self.parent().show_menubar_frame_missing_players()

        self.missing_players_button.setEnabled(True)
    # ------------------------------------------------------------------------------- #
    def ask_for_updating_waiting_list(self):
        self.parent().php_scan_button()

    def update_waiting_list(self, participants):
        
        if participants:

            for i, name in enumerate(participants):
                line_edit = self.parameters["assign"][i]["server_id"].edit  # line edit widget (server id)
                check_box = self.parameters["assign"][i]["bot"].check_box  # check box widget (bot or not)

                self.enable_line_edit(line_edit=line_edit, check_box=check_box, name=name)

        else:
            
            # if not participants reset server_id widget
            for line in self.parameters["assign"]:
                self.disable_line_edit(line["server_id"].edit)

    # ----------------------------- assignment validity checking -------------------------------------------------- #

    def check_assignment_validity(self, **kwargs):

        assignment = list(enumerate(self.get_parameters()))
        n_firm = 0

        for i, (game_id, server_id, role, bot) in assignment:

            n_firm += role == "firm"

            for j, (other_game_id, other_server_id, other_role, other_bot) in assignment:

                if other_server_id == server_id and other_server_id != "Bot" and i != j:
                    return "Two identical server ids: '{}'.".format(server_id)

                if other_game_id == game_id and i != j:
                    return "Two identical game_id ids: '{}'.".format(game_id)

        # if role config is not respected
        if n_firm != self.param["game"]["n_firms"]:
            self.remove_or_add_firms(n_firm=n_firm, assignment=assignment, idx=kwargs["idx"])

    def remove_or_add_firms(self, n_firm, assignment, idx):

        nb_of_firm_to_add_or_remove = self.param["game"]["n_firms"] - n_firm

        for i, (game_id, server_id, role, bot) in assignment:
            
            if i != idx:

                if nb_of_firm_to_add_or_remove < 0:
                    
                    if role == "firm":
                        self.parameters["assign"][i]["role"].customer.setChecked(True)
                        nb_of_firm_to_add_or_remove += 1
                
                elif  nb_of_firm_to_add_or_remove > 0:

                    if role == "customer":
                        self.parameters["assign"][i]["role"].firm.setChecked(True)
                        nb_of_firm_to_add_or_remove -= 1

    # ----------------------------------------------------------------------------------------------------------------- #

    def get_parameters(self):
        return [[int(i["game_id"].get_value()), i["server_id"].get_value(), i["role"].get_value(), i["bot"].get_value()]
                for i in self.parameters["assign"]]
    
    def show_warning(self, **instructions):

        QMessageBox().warning(
            self, "", instructions["msg"],
            QMessageBox.Ok
        )

    def switch_line_edit(self, idx, from_line):

        if self.setup_done:

            # get desired widgets
            line_edit = self.parameters["assign"][idx]["server_id"].edit  # line edit widget (server_id)
            check_box = self.parameters["assign"][idx]["bot"].check_box  # check box widget (bot or not)

            # if line edit (containing server ids) is not enabled
            if not line_edit.isEnabled() and from_line :
                self.enable_line_edit(line_edit, check_box)

            # if line edit is enabled and signal comes from check box
            elif not line_edit.isEnabled() and not from_line:
                self.disable_line_edit(line_edit)

    @staticmethod
    def disable_line_edit(line_edit):

        line_edit.setText("Bot")

    @staticmethod
    def enable_line_edit(line_edit, check_box, name=""):

        check_box.setChecked(False)
        line_edit.setText(name)

    # --------------------------------- Widgets used in assignment menu --------------------------------- #

class RadioParameter(object):
    """role (firm/customer)"""

    def __init__(self, parent, checked, idx):

        self.layout = QHBoxLayout()

        self.group = QButtonGroup()

        self.firm = QRadioButton()
        self.customer = QRadioButton()

        self.filter = MouseClick(parent=parent, idx=idx)

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

        self.firm.installEventFilter(self.filter)
        self.customer.installEventFilter(self.filter)

    def get_value(self):

        return ("customer", "firm")[self.firm.isChecked()]

    def add_to_grid_layout(self, layout, x, y):

        layout.addLayout(self.layout, x, y)


class IntParameter(object):
    """game_id and server_id"""

    def __init__(self, parent, value, idx):

        self.idx = idx
        self.edit = QLineEdit(str(value))

        self.setup()

    def setup(self):
        
        self.edit.setEnabled(False)

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
    to detect if QLineEdit/QRadioButton
    (respectively roles and server_id widget)
    has been clicked"""

    def __init__(self, parent, idx):
        super().__init__()
        self.idx = idx
        self.parent = parent

    def eventFilter(self, obj, event):

        if event.type() == QEvent.MouseButtonPress:

            if type(obj) == QRadioButton:

                widget = self.parent.parameters["assign"][self.idx]["role"]

                if widget.firm.isChecked():
                    widget.customer.setChecked(True)
                else:
                    widget.firm.setChecked(True)

                self.parent.check_assignment_validity(idx=self.idx)
                return True

            else:
                self.parent.switch_line_edit(idx=self.idx, from_line=True)
                return True

        return False


class Timer(Thread):
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
                Event().wait(np.random.randint(4))
            except:
                Event().wait(np.random.randint(4))

