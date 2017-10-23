import numpy as np

from utils.utils import Logger


class TimeManager(Logger):

    def __init__(self, controller):
        self.controller = controller
        self.data = controller.data
        self.state = ""
        self.t = 0
        self.ending_t = None
        self.continue_game = True

    def setup(self):
        
        self.state = self.data.time_manager_state

        self.log("NEW STATE: {}.".format(self.state))

        self.t = self.data.time_manager_t
        self.ending_t = None
        self.continue_game = True
        self.beginning_time_step()

    def check_state(self):
        
        # Time to init
        if self.state == "beginning_init":
            if self.data.current_state["init_done"]:
                self.state = "beginning_time_step"
                self.log("NEW STATE: {}.".format(self.state))
        
        # Active firm must play
        elif self.state == "beginning_time_step":
            if self.data.current_state["active_replied"]:
                self.state = "active_has_played"
                self.log("NEW STATE: {}.".format(self.state))
        
        # Then customers need to choose a perimeter as well as a firm to buy from
        elif self.state == "active_has_played":
            if np.sum(self.data.current_state["customer_replies"]) == self.data.param["game"]["n_customers"]:
                self.state += "_and_all_customers_replied"
                self.log("NEW STATE: {}.".format(self.state))

        # Firms need to know their respective scores, then it is the end of the turn
        elif self.state == "active_has_played_and_all_customers_replied":
            if self.data.current_state["passive_gets_results"] and self.data.current_state["active_gets_results"]:

                self.state = "end_time_step"
                self.log("NEW STATE: {}.".format(self.state))
                self.end_time_step()
                
                # If the game did not end
                if self.state != "end_game":
                    self.beginning_time_step()
                    self.state = "beginning_time_step"
                    self.log("NEW STATE: {}.".format(self.state))

    def beginning_time_step(self):
        
        # Reset conditions (which are used in order to pass to another state)
        self.data.current_state["customer_replies"] = np.zeros(self.data.param["game"]["n_customers"])
        self.data.current_state["active_replied"] = False
        self.data.current_state["passive_gets_results"] = False
        self.data.current_state["active_gets_results"] = False

    def end_time_step(self):

        self.log("Game server goes next turn.")

        # Save history
        self.data.update_history()
        
        # Reverse firm status (passive/active)
        self.data.current_state["firm_status"] = self.data.current_state["firm_status"][::-1]
        
        # Compute figures in order to show them in game view
        self.controller.queue.put(("time_manager_compute_figures", ))
        self.t += 1
        
        # The game is going to stop, it's time to declare ending time
        if not self.continue_game and self.ending_t is None:
            self.log("This turn is going to be the last one!")
            self.ending_t = self.t

        # Ending time is defined and all clients got it
        elif not self.continue_game and self.ending_t is not None:
            self.log("GAME ENDS NOW.")
            self.state = "end_game"
            self.controller.queue.put(("time_manager_stop_game", ))

    def stop_as_soon_as_possible(self):
        self.continue_game = False
