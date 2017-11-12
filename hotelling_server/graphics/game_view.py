from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLabel
import numpy as np

from hotelling_server.graphics.widgets.plot_layouts import PlotLayout
from hotelling_server.graphics.widgets.plot import OneLinePlot, TwoLinesPlot
from hotelling_server.graphics.widgets.trial_counter import TrialCounter
from hotelling_server.graphics.widgets.table_layouts import TableLayout

from utils.utils import Logger


class GameFrame(QWidget, Logger):

    name = "GameFrame"

    def __init__(self, parent, param):

        super().__init__(parent=parent)

        self.layout = QVBoxLayout()

        self.param = param

        self.assignment = None

        self.stop_button = QPushButton()
        self.switch_button = QPushButton()

        self.trial_counter = TrialCounter()

        self.address_label = QLabel()
        self.address_text = None

        self.plot_layout = dict()
        self.table_layout = dict()

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

        self.table_layout["firm"] = TableLayout(
            parent=self,
            role="firm",
            labels=self._get_labels(role="firm")
        )

        self.table_layout["customer"] = TableLayout(
            parent=self,
            role="customer",
            labels=self._get_labels(role="customer")
        )

        self._setup()

    def _setup(self):

        self.setLayout(self.layout)
        self.layout.addLayout(self.trial_counter, stretch=0)

        self.layout.addWidget(self.switch_button, stretch=0)

        # add plots and then hide it
        for key, widget in sorted(self.plot_layout.items()):
            self.layout.addWidget(widget, stretch=1)
            widget.hide()

        # add tables
        for key, widget in sorted(self.table_layout.items()):
            self.layout.addWidget(widget)

        self.layout.addWidget(self.stop_button, stretch=0, alignment=Qt.AlignBottom)

        # add to layout
        self.layout.addWidget(self.address_label, alignment=Qt.AlignCenter)

        # noinspection PyUnresolvedReferences
        self.stop_button.clicked.connect(self.push_stop_button)
        # noinspection PyUnresolvedReferences
        self.switch_button.clicked.connect(self.push_switch_button)

    def set_server_address(self, address):
        self.address_text = address

    def set_assignment(self, assignment):
        self.assignment = assignment

    def prepare(self):

        self.log("Preparing...")
        self._prepare_figures()
        self._prepare_buttons()
        self._prepare_tables()
        self._prepare_address_label()
        self.log("Preparation done!")

    def _prepare_address_label(self):

        self.address_label.setText(self.address_text)
        font = QFont()
        font.setPointSize(20)
        self.address_label.setFont(font)

    def _prepare_figures(self):

        self._initialize_figures()

    def _prepare_tables(self):

        self._initialize_tables()

    def _prepare_buttons(self):

        self.stop_button.setText("Stop task")
        self.stop_button.setEnabled(True)
        self.switch_button.setText("View figures")

    def push_switch_button(self):

        self.switch_button.setEnabled(False)

        switch = self.switch_button.text() == "View figures"
        self.switch_button.setText(("View figures", "View tables")[switch])

        to_hide = (self.plot_layout, self.table_layout)[switch]
        to_show = (self.table_layout, self.plot_layout)[switch]

        self._hide_and_show(to_hide=to_hide, to_show=to_show)

        self.switch_button.setEnabled(True)

    @staticmethod
    def _hide_and_show(to_hide, to_show):

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

    def _initialize_tables(self):

        for key, table in self.table_layout.items():
            table.prepare(
                rows=[(player["name"], game_id) for game_id, player in sorted(self.assignment.items()) if player["role"] == key]
            )

    # -------------------------------------- These methods need to be moved elsewhere ------------------------- #

    @staticmethod
    def _get_labels(role):

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

        return {"labels": labels[role],
                "fancy_labels": fancy_labels[role]}

    # ----------------------------------------------------------------------------------------------- #

    def update_tables(self, parameters):

        ids = {}

        for role in self.table_layout.keys():

            ids[role] = [(player["name"], game_id) for game_id, player in sorted(self.assignment.items()) if player["role"] == role]

            self.table_layout[role].update(ids[role], parameters)

    def _initialize_figures(self):

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
