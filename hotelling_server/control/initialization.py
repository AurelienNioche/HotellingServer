from copy import deepcopy


from multiprocessing import Queue
import numpy as np


class Init:

    name = "Init"

    def __init__(self, controller):

        self.controller = controller
        self.data = controller.data
        self.time_manager = controller.time_manager

        self.assignment = None

        self.queue = Queue()

    def set_assignment(self, assignment):
        self.assignment = assignment

    def ask_init(self, data):

        game_id = int(data.split("/")[1])

        role = self.get_role(game_id)

        self.data.roles[game_id] = role

        if role == "firm":
            return self.init_firms("ask_init", game_id)
        else:
            return self.init_customers("ask_init", game_id)

    def init_customers(self, func_name, game_id):

        if game_id not in self.data.customers_id.keys():
            customer_id = len(self.data.customers_id)
            self.data.customers_id[game_id] = customer_id

        else:
            customer_id = self.data.customers_id[game_id]

        position, exploration_cost, utility_consumption, utility = self.get_customers_data(customer_id)

        self.check_remaining_agents()

        return self.reply(
            game_id, func_name, self.time_manager.t, position, exploration_cost,
            utility_consumption, utility)

    def get_customers_data(self, customer_id):

        position = customer_id + 1
        exploration_cost = self.data.parametrization["exploration_cost"]
        utility_consumption = self.data.parametrization["utility_consumption"]
        utility = self.data.current_state["customer_cumulative_utility"][customer_id]

        return position, exploration_cost, utility_consumption, utility

    def init_firms(self, func_name, game_id):

        if game_id not in self.data.firms_id.keys():
            firm_id = len(self.data.firms_id)
            self.data.firms_id[game_id] = firm_id

        # if device already asked for init, get id
        else:
            firm_id = self.data.firms_id[game_id]

        t, state, position, price, opp_position, opp_price, profits, opp_profits = self.get_firms_data(firm_id)

        self.check_remaining_agents()

        return self.reply(
            game_id,
            func_name,
            t,
            position,
            state,
            price,
            opp_position,
            opp_price,
            profits,
            opp_profits)

    def get_firms_data(self, firm_id):

        opponent_id = (firm_id + 1) % 2

        t = self.time_manager.t
        cs = deepcopy(self.data.current_state)

        position = cs["firm_positions"][firm_id]
        price = cs["firm_prices"][firm_id]
        profits = cs["firm_cumulative_profits"][firm_id]

        opp_position = cs["firm_positions"][opponent_id]
        opp_price = cs["firm_prices"][opponent_id]
        opp_profits = cs["firm_cumulative_profits"][opponent_id]

        state = cs["firm_status"][firm_id]

        if (state == "passive" and cs["active_gets_results"] is True) or \
                (state == "active" and cs["passive_gets_results"] is True):
            firm_choices = np.asarray(cs["customer_firm_choices"])
            n_opp = sum(firm_choices == opponent_id)
            opp_profits -= n_opp * opp_price

        if (state == "active" and cs["active_gets_results"] is True) or \
                (state == "passive" and cs["passive_gets_results"] is True):
            firm_choices = np.asarray(cs["customer_firm_choices"])
            n = sum(firm_choices == firm_id)
            profits -= n * price

        return (t,
                state,
                position,
                price,
                opp_position,
                opp_price,
                profits,
                opp_profits)

    @staticmethod
    def reply(*args):

        msg = {
            "game_id": args[0],
            "response": "reply/{}".format("/".join(
                [str(a) if type(a) in (int, np.int64) else a.replace("ask", "reply") for a in args[1:]]
            ))}
        return "reply", msg

    def get_role(self, game_id):

        return self.assignment[game_id]["role"]

    def check_remaining_agents(self):

        remaining = len(self.data.roles) - (len(self.data.firms_id) + len(self.data.customers_id))

        if not remaining:
            self.data.current_state["init_done"] = True
            self.time_manager.check_state()

    # ------------------------------- Admin init ----------------------------------------------------------- #

    def ask_admin_init(self):

        # default admin game_id is -1
        game_id = -1

        try:
            firm_0 = self.data.firms_id[0]
            firm_1 = self.data.firms_id[1]

            state = self.data.current_state["firm_status"][firm_0]

            position = self.data.current_state["firm_positions"][firm_0]
            price = self.data.current_state["firm_prices"][firm_0]
            profits = self.data.current_state["firm_cumulative_profits"][firm_0]

            opp_position = self.data.current_state["firm_positions"][firm_1]
            opp_price = self.data.current_state["firm_prices"][firm_1]
            opp_profits = self.data.current_state["firm_cumulative_profits"][firm_1]

            return self.reply(
                game_id,
                "ask_admin_init",
                self.time_manager.t,
                (1, 0)[state == "active"],
                position,
                price,
                profits,
                opp_position,
                opp_price,
                opp_profits)

        except:
            return self.reply("error", "players_are_not_connected_yet")
