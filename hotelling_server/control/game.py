from utils.utils import Logger
import numpy as np
from sys import _getframe as func

class Game(Logger):

    name = "Game"

    def __init__(self, controller):

        self.controller = controller
        self.command = None

        self.t = 0

        self.game_parameters = self.controller.data.param["game"]
        self.interface_parameters = self.controller.data.param["interface"]

        self.n_customers = self.game_parameters["n_customers"]
        self.n_firms = self.game_parameters["n_firms"]

        self.continue_game = True

        self.data = self.controller.data

        self.save = None

    @staticmethod
    def get_name(arg):
        return arg.f_code.co_name

    def new(self):

        self.data.roles = ["firm" for i in range(self.n_firms)] + \
                          ["customer" for i in range(self.n_customers)]

        np.random.shuffle(self.data.roles)

    def handle_request(self, request):

        self.log("Got request: '{}'.".format(request))

        # retrieve whole command
        whole = [i for i in request.split("/") if i != ""]
   
        try:
            # retrieve method
            self.command = eval("self.{}".format(whole[0]))

            # retrieve method arguments
            args = [int(a) if a.isdigit() else a for a in whole[1:]]
   
            # call method
            to_client = self.command(*args)

        except Exception as e:
            to_client = (
                "Command contained in request not understood.\n"
                "{}".format(e),
                None)

        self.log("Reply '{}' to request '{}'.".format(to_client, request))
        return to_client

    def end_time_step(self):

        self.t += 1
        self.data.update_history()
        
        if not self.continue_game:
            self.end_game()

    def check_time_step(self, client_t):

        if not client_t == self.t:
            raise Exception("Time is not synchronized you cunt!")

    def record_and_get_opponent_choices(self, opponent_id):
        
        opponent_choices = [
            self.data.history[self.t - 1][key][opponent_id]
            for key in ["firm_positions", "firm_prices"]
        ]
 
        return opponent_choices[0], opponent_choices[1] 

    @staticmethod
    def reply(*args):
        return "reply/{}".format("/".join([str(a) for a in args]))

    def ask_init(self, android_id):

        game_id = self.controller.id_manager.get_game_id_from_android_id(android_id, max_n=len(self.data.roles))

        if game_id != -1:

            # pick role
            role = self.data.roles[game_id]

            if role == "firm":
                firm_id = len(self.data.firms_id) if len(self.data.firms_id) != 0 else 0
                self.data.firms_id[game_id] = firm_id
                position = self.data.current_state["firm_positions"][firm_id]
                price = self.data.current_state["firm_prices"][firm_id]

                return self.reply(self.get_name(func()), game_id, self.t, role, position, price)

            else:
                customer_id = len(self.data.firms_id) if len(self.data.firms_id) != 0 else 0
                self.data.customer_id[game_id] = customer_id
                position = customer_id + 1
                exploration_cost = self.interface_parameters["exploration_cost"]
                utility_consumption = self.interface_parameters["utility_consumption"]

                return self.reply(
                    self.get_name(func()),
                    game_id, self.t,
                    role, position, exploration_cost, utility_consumption)

        else:
            return "Error with ID manager. Maybe not authorized to participate."

    def ask_end_of_turn(self):

        current_state = self.data.current_state

        cond0 = all(
            [len(current_state[k]) == self.n_customers
             for k in ["customer_extra_view_choices", "customer_firm_choices"]]
        )

        cond1 = all(
            [len(current_state[k]) == self.n_firms
             for k in ["firm_positions", "firm_prices"]]
        )

        if cond0 and cond1:
            self.end_time_step()

    def stop_as_soon_as_possible(self):

        self.continue_game = False

    def end_game(self):

        self.controller.queue.put(("game_stop_game", ))

    def ask_customer_firm_choices(self, game_id, t):

        self.log("Customer {} asks for firms strategies.".format(game_id))

        self.check_time_step(t)

        x = self.data.current_state["firm_positions"]
        prices = self.data.current_state["firm_prices"]
        
        return self.reply(self.get_name(func()), self.t, x[0], x[1], prices[0], prices[1])

    def ask_firm_opponent_choice(self, game_id, t):

        assert self.n_firms == 2, "only works if firms are 2"

        self.log("Firm {} asks for opponent strategy.".format(game_id))

        self.check_time_step(t)

        # opponent_id = (self.data.firms_id[game_id] + 1) % 2
        opponent_id = [int(k) for k in self.data.firms_id.keys() if k != str(game_id)][0]

        return self.reply(
            self.get_name(func()),
            self.t,
            self.data.current_state["firm_positions"][opponent_id],
            self.data.current_state["firm_prices"][opponent_id]
        )

    def ask_firm_choice_recording(self, game_id, t, position, price):

        self.log("Firm {} asks to save its price and position.".format(game_id))

        self.check_time_step(t)

        opponent_id = [int(k) for k in self.data.firms_id.keys() if k != str(game_id)][0]

        opponent_pos, opponent_price = self.record_and_get_opponent_choices(opponent_id)

        for ids, pos, px in [[game_id, position, price], [opponent_id, opponent_pos, opponent_price]]:
            self.data.write("firm_positions", int(ids), pos)
            self.data.write("firm_prices", int(ids), px)

        return self.reply(self.get_name(func()))

    def ask_customer_choice_recording(self, game_id, t, extra_view, firm):

        self.log("Customer {} asks to save its exploration perimeter and firm choice.".format(game_id))

        self.check_time_step(t)

        self.data.write("customer_extra_view_choice", game_id, extra_view)
        self.data.write("customer_firm_choices", game_id, firm)

        return self.reply(self.get_name(func()))

    def ask_firm_n_clients(self, game_id, t):

        self.log("Firm {} asks the number of its clients.".format(game_id))

        self.check_time_step(t)

        firm_choices = np.asarray(self.data.current_state["customer_firm_choices"])
        cond = firm_choices == game_id

        n = len(firm_choices[cond])

        return self.reply(self.get_name(func()), self.t, n)
