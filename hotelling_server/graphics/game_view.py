from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QPushButton, QTableWidget, QTableWidgetItem, \
    QHeaderView, QVBoxLayout, QLabel, QAbstractItemView
import numpy as np

from hotelling_server.graphics.widgets.plot_layouts import PlotLayout
from hotelling_server.graphics.widgets.plot import OneLinePlot, TwoLinesPlot
from hotelling_server.graphics.widgets.trial_counter import TrialCounter
from utils.utils import Logger


class GameFrame(QWidget, Logger):

    name = "GameFrame"

    def __init__(self, parent, param):

        super().__init__(parent=parent)

        self.layout = QVBoxLayout()

        self.param = param

        self.controller = self.parent().mod.controller

        self.stop_button = QPushButton()
        self.switch_button = QPushButton()

        self.table = {"firm": QTableWidget(),
                      "customer": QTableWidget()}

        self.trial_counter = TrialCounter()

        self.address_label = QLabel()

        self.plot_layout = dict()

        self.plot_layout["firm_profits"] = PlotLayout(
            parent=self,
            title="",
            plot_class=TwoLinesPlot
        )

        self.plot_layout["firm_distance"] = PlotLayout(
            parent=self,
            title="",
            plot_class=TwoLinesPlot
        )

        self.plot_layout["customer_mean_extra_view_choices"] = PlotLayout(
            parent=self,
            title="",
            plot_class=OneLinePlot
        )

        self.plot_layout["customer_mean_utility"] = PlotLayout(
            parent=self,
            title="",
            plot_class=OneLinePlot
        )

        self.setup()

    def set_address_type(self, server_name):

        self.address_text = (
                "IP: {}".format(self.param["network"]["ip_address"]), 
                "Server url: {}".format(self.param["network"]["php_server"])
            )[server_name == "PHPServer"]

    def setup(self):

        self.setLayout(self.layout)
        self.layout.addLayout(self.trial_counter, stretch=0)

        self.layout.addWidget(self.switch_button, stretch=0)

        # add plots and then hide it
        for key, widget in sorted(self.plot_layout.items()):
            self.layout.addWidget(widget, stretch=1)
            widget.hide()

        # add tables
        for widget in self.table.values():
            self.layout.addWidget(widget)

        self.layout.addWidget(self.stop_button, stretch=0, alignment=Qt.AlignBottom)

        # add to layout
        self.layout.addWidget(self.address_label, alignment=Qt.AlignCenter)

        # noinspection PyUnresolvedReferences
        self.stop_button.clicked.connect(self.push_stop_button)
        # noinspection PyUnresolvedReferences
        self.switch_button.clicked.connect(self.push_switch_button)

    def prepare(self, parameters):

        self.log("Preparing...")
        self.prepare_figures()
        self.prepare_buttons()
        self.prepare_tables(parameters)
        self.prepare_address_label()
        self.log("Preparation done!")

    def prepare_address_label(self):
        
        self.address_label.setText(self.address_text)
        font = QFont()
        font.setPointSize(20)
        self.address_label.setFont(font)

    def prepare_figures(self):

        self.initialize_figures()

    def prepare_buttons(self):

        self.stop_button.setText("Stop task")
        self.stop_button.setEnabled(True)
        self.switch_button.setText("View figures")

    def push_switch_button(self):

        self.switch_button.setEnabled(False)

        switch = self.switch_button.text() == "View figures"
        self.switch_button.setText(("View figures", "View tables")[switch])

        to_hide = (self.plot_layout, self.table)[switch]
        to_show = (self.table, self.plot_layout)[switch]

        self.hide_and_show(to_hide=to_hide, to_show=to_show)

        self.switch_button.setEnabled(True)

    @staticmethod
    def hide_and_show(to_hide, to_show):

        for widget in to_hide.values():
            widget.hide()
        for widget in to_show.values():
            widget.show()

    def push_stop_button(self):

        self.stop_button.setEnabled(False)

        if self.stop_button.text() == "Stop task":

            self.stop_button.setText("Go to home menu")
            self.parent().stop_game()
            self.stop_button.setEnabled(True)

        elif self.stop_button.text() == "Go to home menu":

            self.parent().look_for_alive_players()

    def set_trial_number(self, trial_n):

        self.trial_counter.set_trial_number(trial_n)

    def prepare_tables(self, parameters):

        assignment, ids, labels, fancy_labels = self.get_tables_data(parameters)

        for role in ["firm", "customer"]:

            rows = [server_id for server_id, j, k in assignment if j == role]

            columns = fancy_labels[role]

            # empty tables
            self.table[role].clear()

            # set non editable and disable selection
            self.table[role].setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.table[role].setSelectionMode(QAbstractItemView.NoSelection)
            self.table[role].setFocusPolicy(Qt.NoFocus)

            # set height and width
            self.table[role].setColumnCount(len(columns))
            self.table[role].setRowCount(len(rows))

            # fit the widget
            self.table[role].horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.table[role].verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

            # set column names (parameters to print)
            for i, param in enumerate(columns):
                self.table[role].setHorizontalHeaderItem(i, QTableWidgetItem(param))

            # set rows names (server ids, then game ids)
            for i, idx in enumerate(rows):
                self.table[role].setVerticalHeaderItem(
                    i, QTableWidgetItem("Server id: {}".format(idx))
                )

    def update_tables(self, parameters):

        assignment, ids, labels, fancy_labels = self.get_tables_data(parameters)

        for role in ["firm", "customer"]:

            rows = ids[role]
            columns = labels[role]

            # set row names (server ids, game ids)
            for i, idx in enumerate(rows):
                    self.table[role].setVerticalHeaderItem(
                        i, QTableWidgetItem("Server id: {} | Game id: {}".format(*idx))   
                    )

            self.fill_tables(role, rows, columns, parameters)

    def fill_tables(self, role, rows, columns, parameters):

        # for each game_id
        for x, (server_id, game_id) in enumerate(rows):

            # for each label
            for y, label in enumerate(columns):

                data = parameters["current_state"][label]
                cond = game_id in parameters["{}s_id".format(role)].keys()

                if cond:
                    role_id = parameters["{}s_id".format(role)][game_id]

                    # if data is available
                    if len(data) > int(role_id):
                        string = str(data[role_id])
                        self.table[role].setItem(x, y, QTableWidgetItem(string))

    def get_tables_data(self, parameters):

        ids = self.get_ids(parameters)
        labels, fancy_labels = self.get_labels()
        assignment = parameters["assignment"]

        return assignment, ids, labels, fancy_labels

    @staticmethod
    def get_ids(parameters):

        server_id = list(parameters["map_server_id_game_id"].items())
        bot_firm_id = list(parameters["bot_firms_id"].items())
        bot_customer_id = list(parameters["bot_customers_id"].items())

        add = bot_firm_id + bot_customer_id

        bot_game_id = [("Bot", game_id) for game_id, i in add]

        server_id_game_id = server_id + bot_game_id

        ids = {"firm": [],
               "customer": []}

        # sort server ids and game ids by role (firm vs customer)
        for role in ["firm", "customer"]:
            ids[role] = [
                (server_id, game_id) for server_id, game_id in server_id_game_id
                if parameters["roles"][game_id] == role
            ]
        return ids

    @staticmethod
    def get_labels():

        # pick desired labels
        firm_labels = ("firm_profits",
                       "firm_prices",
                       "firm_positions",
                       "firm_status",
                       "n_client",
                       "firm_cumulative_profits",
                       "firm_states",
                       "time_since_last_request_firms",)

        customer_labels = ("customer_firm_choices",
                           "customer_extra_view_choices",
                           "customer_utility",
                           "customer_cumulative_utility",
                           "customer_states",
                           "time_since_last_request_customers")

        labels = {
            "firm": firm_labels,
            "customer": customer_labels}

        # transform into nicer labels
        fancy_labels = {
            "firm": [
                name.replace("_", " ").capitalize()
                for name in firm_labels],
            "customer": [
                name.replace("_", " ").capitalize()
                for name in customer_labels]}

        return labels, fancy_labels

    def initialize_figures(self):

        for widget in self.plot_layout.values():
            widget.plot.clear()

        self.plot_layout["firm_distance"].initialize_figure(
            initial_data=[np.arange(11), np.arange(11)], labels=["position A", "position B"]
        )

        self.plot_layout["firm_profits"].initialize_figure(
            initial_data=[np.arange(11), np.arange(11)], labels=["profits A", "profits B"]
        )

        self.plot_layout["customer_mean_extra_view_choices"].initialize_figure(
            initial_data=np.arange(11), labels="mean view choices"
        )

        self.plot_layout["customer_mean_utility"].initialize_figure(
            initial_data=np.arange(11), labels="mean customer utility"
        )

        self.log("Figure initialized.")

    def update_statistics(self, data):

        for key, value in self.plot_layout.items():
            if key in data.keys() and not value.isHidden():
                value.update_figure(data[key])

    def update_done_playing(self, done_playing):

        self.done_playing_layout.update_figure(done_playing)

    def update_done_playing_labels(self, done_playing_labels):

        self.done_playing_layout.update_labels(done_playing_labels)
