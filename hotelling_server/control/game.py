import numpy as np
from bots.local_bot_client import HotellingLocalBots

from utils.utils import Logger, function_name


class Game(Logger):

    name = "Game"

    def __init__(self, controller):

        # get controller attributes
        self.controller = controller
        self.data = self.controller.data
        self.time_manager = self.controller.time_manager

        # get parameters from interface and json files
        self.game_parameters = self.data.param["game"]
        self.parametrization = self.data.param["parametrization"]
        self.assignment = None

        # set number of type of players
        self.n_customers = self.game_parameters["n_customers"]
        self.n_firms = self.game_parameters["n_firms"]
        self.n_agents = self.n_firms + self.n_customers

        # ---------------- #
        self.bots = None
        self.interface_parameters = None
        self.unexpected_id_list = None

        # ----------------------------------- sides methods --------------------------------------#

    def new(self):
        """called if new game is launched"""

        self.assignment = self.data.assignment
        self.interface_parameters = self.data.parametrization

        self.unexpected_id_list = []

        self.data.roles = [""] * self.n_agents

        self.data.current_state["time_since_last_request_firms"] = [""] * self.n_firms
        self.data.current_state["time_since_last_request_customers"] = [""] * self.n_customers
        self.data.current_state["firm_states"] = [""] * self.n_firms
        self.data.current_state["customer_states"] = [""] * self.n_customers

        self.data.current_state["firm_status"] = ["active", "passive"]
        self.data.current_state["n_client"] = [0, 0]
        self.data.current_state["firm_profits"] = [0, 0]
        self.data.current_state["firm_cumulative_profits"] = [0, 0]

        self.data.current_state["firm_positions"] = \
            np.random.choice(range(1, self.game_parameters["n_positions"]), size=2, replace=False)

        self.data.current_state["firm_prices"] = \
            np.random.randint(1, self.game_parameters["n_prices"], size=2)
        
        # init customer current_state arrays
        customer_keys = (
            "customer_extra_view_choices",
            "customer_firm_choices",
            "customer_utility",
            "customer_replies",
            "customer_cumulative_utility"
        )

        for key in customer_keys:
            self.data.current_state[key] = \
                np.zeros(self.game_parameters["n_customers"], dtype=int)

        self.launch_bots()

    def load(self):
        """called if a previous game is loaded"""

        self.data.setup()
        self.interface_parameters = self.data.parametrization
        self.unexpected_id_list = []
        self.assignment = self.data.assignment

        self.launch_bots()

    # -------------------------------| bots |------------------------------------------------------------ #

    def launch_bots(self):
        """launch bots based on assignment settings"""

        n_firms = 0
        n_customers = 0
        n_agents_to_wait = 0

        for game_id, server_id, role, bot in self.assignment:
            if bot:
                n_firms += role == "firm"
                n_customers += role == "customer"
            else:
                n_agents_to_wait += 1

        if n_firms > 0 or n_customers > 0:
            self.bots = \
                HotellingLocalBots(self.controller, n_firms, n_customers, n_agents_to_wait,
                self.interface_parameters["condition"])
            self.bots.start()

    def stop_bots(self):
        self.bots.stop()

    # -------------------------------| network related method |----------------------------------------- #

    def handle_request(self, request):

        self.log("Got request: '{}'.".format(request))
        self.log("Current state: {}".format(self.time_manager.state))

        # save data in case server shuts down
        self.data.save()

        # retrieve whole command
        whole = [i for i in request.split("/") if i != ""]

        # retrieve method
        command = eval("self.{}".format(whole[0]))

        # retrieve method arguments
        args = [int(a) if a.isdigit() else a for a in whole[1:]]

        # don't launch methods if init is not done
        if not self.data.current_state["init_done"]:
            to_client = self.reply_error("wait_init")

        # regular launch method
        else:
            to_client = command(*args)

        self.log("Reply '{}' to request '{}'.".format(to_client, request))

        # save in case server shuts down
        self.data.save()

        return to_client

    # ---------------------------| firms sides methods |----------------------------------------- #

    def get_opponent_choices(self, opponent_id):

        if self.time_manager.t == 0:
            opponent_choices = [
                self.data.current_state[key][opponent_id]
                for key in ["firm_positions", "firm_prices"]
            ]

        else:
            opponent_choices = [
                self.data.history[key][self.time_manager.t - 1][opponent_id]
                for key in ["firm_positions", "firm_prices"]
            ]

        return opponent_choices[0], opponent_choices[1]

    def get_nb_of_clients(self, firm_id, opponent_id, t):
        """get own and opponent number of clients"""

        if self.time_manager.t == t:
            firm_choices = np.asarray(self.data.current_state["customer_firm_choices"])
        else:
            firm_choices = np.asarray(self.data.history["customer_firm_choices"][t])

        cond = firm_choices == firm_id
        n = sum(cond)

        cond = firm_choices == opponent_id
        n_opp = sum(cond)

        return n, n_opp

    def get_client_choices(self, firm_id, t):
        """returns a string, 0 if clients bought from the opponent, 1 otherwise.
        Also -1 if client didn't make a choice"""

        if self.time_manager.t == t:
            firm_choices = np.asarray(self.data.current_state["customer_firm_choices"])
        else:
            firm_choices = np.asarray(self.data.history["customer_firm_choices"][t])

        return "/".join([str(int(c == firm_id)) if c != -1 else str(-1) for c in firm_choices])

    def firm_active_first_step(self, firm_id, price, position, state):
        """firm active first call of a turn"""

        # Register choice
        opponent_id = (firm_id + 1) % 2
        opponent_pos, opponent_price = self.get_opponent_choices(opponent_id)

        for ids, pos, px in [(firm_id, position, price), (opponent_id, opponent_pos, opponent_price)]:
            self.data.current_state["firm_positions"][int(ids)] = pos
            self.data.current_state["firm_prices"][int(ids)] = px

        # check state
        self.data.current_state["active_replied"] = True
        self.data.current_state["firm_states"][firm_id] = state

    def firm_end_of_turn(self, firm_id, t, status):
        """both firm end of turn"""

        opponent_id = (firm_id + 1) % 2

        n, n_opp = self.get_nb_of_clients(firm_id, opponent_id, t)
        price = self.data.current_state["firm_prices"][firm_id]

        self.data.current_state["firm_cumulative_profits"][firm_id] += n * price
        self.data.current_state["firm_profits"][firm_id] = n * price
        self.data.current_state["n_client"][firm_id] = n
        self.data.current_state["{}_gets_results".format(status)] = True

    # --------------------------------| customer sides methods |------------------------------------- #

    def compute_utility(self, customer_id):

        uc = self.interface_parameters["utility_consumption"]
        ec = self.interface_parameters["exploration_cost"]
        firm_choice = self.data.current_state["customer_firm_choices"][customer_id]
        view_choice = self.data.current_state["customer_extra_view_choices"][customer_id]
        price = self.data.current_state["firm_prices"][firm_choice]
        found = int(firm_choice >= 0)

        utility = found * uc - ((ec * view_choice) + found * price)

        self.data.current_state["customer_utility"][customer_id] = utility
        self.data.current_state["customer_cumulative_utility"][customer_id] += utility

    def customer_end_of_turn(self, customer_id, extra_view, firm):

        self.data.current_state["customer_extra_view_choices"][customer_id] = extra_view
        self.data.current_state["customer_firm_choices"][customer_id] = int(firm)
        self.data.current_state["customer_replies"][customer_id] = 1

        self.compute_utility(customer_id)

    # --------------------------------| one liner methods |------------------------------------------ #

    def check_end(self, client_t):
        return int(client_t == self.time_manager.ending_t) if self.time_manager.ending_t else 0

    def is_php(self):
        return self.controller.server.name == "PHPServer"

    def reply(self, *args):

        msg = {
            "game_id": args[0],
            "response": "reply/{}".format("/".join(
                [str(a) if type(a) in (int, np.int64) else a.replace("ask", "reply") for a in args[1:]]
            ))}

        return ("reply", msg) if self.is_php() else ("reply", msg["response"])

    def reply_error(self, msg):
        return ("error", msg) if self.is_php() else ("reply", "error/{}".format(msg))

    def get_all_states(self):
        return self.data.current_state["firm_states"] + self.data.current_state["customer_states"]

    def is_ended(self):
        return all(state == "end_game" for state in self.get_all_states())
    
    def get_prices_and_positions(self):
        return self.data.current_state["firm_positions"], self.data.current_state["firm_prices"]
    
    def set_state(self, role, role_id, state):
        self.data.current_state["{}_states".format(role)][role_id] = state

    # -----------------------------------| customer demands |--------------------------------------#

    def ask_customer_firm_choices(self, game_id, t):

        customer_id = self.data.customers_id[game_id]

        self.log("Customer {} asks for firm choices as t {}.".format(customer_id, t))
        self.log("Client's time is {}, server's time is {}.".format(t, self.time_manager.t))

        if t == self.time_manager.t:
            if self.time_manager.state == "active_has_played":

                x, prices = self.get_prices_and_positions()

                self.set_state(role="customer", role_id=customer_id, state=function_name())

                return self.reply(game_id, function_name(), self.time_manager.t, x[0], x[1], prices[0], prices[1])
            else:
                return self.reply_error("wait")

        elif t > self.time_manager.t:
            return self.reply_error("time_is_superior")

        else:
            x = self.data.history["firm_positions"][t]
            prices = self.data.history["firm_prices"][t]

            return self.reply(game_id, function_name(), t, x[0], x[1], prices[0], prices[1])

    def ask_customer_choice_recording(self, game_id, t, extra_view, firm):

        customer_id = self.data.customers_id[game_id]

        self.log("Customer {} asks for recording his choice as t {}: "
                 "{} for extra view, {} for firm.".format(game_id, t, extra_view, firm))
        self.log("Client's time is {}, server's time is {}.".format(t, self.time_manager.t))

        if t == self.time_manager.t:

            out = self.reply(game_id, function_name(), self.time_manager.t, self.check_end(t))

            if not self.data.current_state["customer_replies"][customer_id]:

                self.customer_end_of_turn(customer_id=customer_id, extra_view=extra_view, firm=firm)
                self.time_manager.check_state()

            else:
                self.log("Customer {} asks for recording his choice as t {} but already replied"
                         .format(game_id, t, extra_view, firm))

            state = "end_game" if self.check_end(t) else function_name()
            self.set_state(role="customer", role_id=customer_id, state=state)

            return out

        elif t > self.time_manager.t:
            return self.reply_error("time_is_superior")

        else:
            return self.reply(game_id, function_name(), t, self.check_end(t))

    # ----------------------------------| passive firm demands |-------------------------------------- #

    def ask_firm_passive_opponent_choice(self, game_id, t):
        """called by a passive firm"""

        firm_id = self.data.firms_id[game_id]
        opponent_id = (firm_id + 1) % 2
        self.log("Firm passive {} asks for opponent strategy.".format(firm_id))
        self.log("Client's time is {}, server's time is {}.".format(t, self.time_manager.t))

        if t == self.time_manager.t:

            if self.time_manager.state == "active_has_played" or \
                    self.time_manager.state == "active_has_played_and_all_customers_replied":

                out = self.reply(
                    game_id,
                    function_name(),
                    self.time_manager.t,
                    self.data.current_state["firm_positions"][opponent_id],
                    self.data.current_state["firm_prices"][opponent_id],
                )

                self.time_manager.check_state()
                self.set_state(role="firm", role_id=firm_id, state=function_name())

                return out

            else:
                return self.reply_error("wait")

        elif t > self.time_manager.t:
            return self.reply_error("time_is_superior")

        else:

            return self.reply(
                game_id,
                function_name(),
                t,
                self.data.history["firm_positions"][t][opponent_id],
                self.data.history["firm_prices"][t][opponent_id],
            )

    def ask_firm_passive_customer_choices(self, game_id, t):

        firm_id = self.data.firms_id[game_id]

        self.log("Firm passive {} asks for its number of clients.".format(firm_id))
        self.log("Client's time is {}, server's time is {}.".format(t, self.time_manager.t))

        if t == self.time_manager.t:

            if self.time_manager.state == "active_has_played_and_all_customers_replied":

                if not self.data.current_state["passive_gets_results"]:

                    choices = self.get_client_choices(firm_id, t)

                    out = self.reply(game_id, function_name(), self.time_manager.t, choices, self.check_end(t))
                    
                    self.firm_end_of_turn(firm_id=firm_id, t=t, status="passive")

                    state = "end_game" if self.check_end(t) else function_name()
                    self.set_state(role="firm", role_id=firm_id, state=state)

                    self.time_manager.check_state()

                    return out

            else:
                return self.reply_error("wait")

        elif t > self.time_manager.t:
            return self.reply_error("time_is_superior")

        else:
            choices = self.get_client_choices(firm_id, t)
            return self.reply(game_id, function_name(), t, choices, self.check_end(t))

    # -----------------------------------| active firm demands |-------------------------------------- #

    def ask_firm_active_choice_recording(self, game_id, t, position, price):
        """called by active firm"""

        firm_id = self.data.firms_id[game_id]

        self.log("Firm active {} asks to save its price and position.".format(firm_id))
        self.log("Client's time is {}, server's time is {}.".format(t, self.time_manager.t))

        if t == self.time_manager.t:

            out = self.reply(game_id, function_name(), self.time_manager.t)

            if not self.data.current_state["active_replied"]:

                self.firm_active_first_step(firm_id, price, position, function_name())

                self.set_state(role="firm", role_id=firm_id, state=function_name())

                self.time_manager.check_state()

            return out

        elif t > self.time_manager.t:
            return self.reply_error("time_is_superior")

        else:
            return self.reply(game_id, function_name(), t)

    def ask_firm_active_customer_choices(self, game_id, t):
        """called by active firm"""

        firm_id = self.data.firms_id[game_id]

        self.log("Firm active {} asks the number of its clients.".format(firm_id))
        self.log("Client's time is {}, server's time is {}.".format(t, self.time_manager.t))

        if t == self.time_manager.t:

            if self.time_manager.state == "active_has_played_and_all_customers_replied":

                choices = self.get_client_choices(firm_id, t)

                out = self.reply(game_id, function_name(), self.time_manager.t, choices, self.check_end(t))

                self.firm_end_of_turn(firm_id=firm_id, t=t, status="active")
                
                state = "end_game" if self.check_end(t) else function_name()
                self.set_state(role="firm", role_id=firm_id, state=state)

                self.time_manager.check_state()

                return out

            else:
                return self.reply_error("wait")

        elif t > self.time_manager.t:
            return self.reply_error("time_is_superior")

        else:
            choices = self.get_client_choices(firm_id, t)
            return self.reply(game_id, function_name(), t, choices, self.check_end(t))
