import numpy as np

from utils.utils import Logger


class TimeManager(Logger):
    def __init__(self, controller):
        self.controller = controller
        self.data = controller.data
        self.state = ""
        self.t = 0

    def check_state(self):
        if self.state == "beginning_time_step":
            if self.data.current_state["active_replied"]:
                self.state = "active_has_played"

        elif self.state == "active_has_played":
            if np.sum(self.data.current_state["customer_replies"] == self.data.param["game"]["n_customers"]):
                self.state += "_and_all_customers_replied"

        elif self.state == "active_has_played_and_all_customers_replied":
            if self.data.current_state["passive_gets_results"] and self.data.current_state["active_gets_results"]:
                
                self.state = "end_time_step"
                self.end_time_step()

                self.beginning_time_step()
                self.state = "beginning_time_step"

    def beginning_time_step(self):

        self.data.current_state["customer_replies"] = np.zeros(self.n_customers)
        self.data.current_state["active_replied"] = False
        self.data.current_state["passive_gets_results"] = False
        self.data.current_state["active_gets_results"] = False

    def end_time_step(self):

        self.log("Game server goes next step.")
        self.data.update_history()
