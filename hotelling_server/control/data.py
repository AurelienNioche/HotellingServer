import json
from utils.utils import Logger


class Data(Logger):

    def __init__(self, controller):

        self.controller = controller

        # --- game variables --- #

        self.entries = [
            "firm_positions", "firm_prices", "firm_profits", 
            "firm_cumulative_profits", "customer_firm_choices",
            "customer_extra_view_choices", "customer_utility", 
            "n_client", "customer_replies", "active_replied",
            "passive_gets_results", "active_gets_results", 
            "firm_status", "time_since_last_request_firms",
            "time_since_last_request_customers", "init_done", 
            "firm_states", "customer_states"
        ]

        self.history = {s: [] for s in self.entries}

        self.current_state = {s: [] for s in self.entries}

        self.firms_id = {}  # key: game_id, value: firm_id
        self.customers_id = {}  # key: game_id, value: customer_id

        self.bot_firms_id = {}
        self.bot_customers_id = {}

        self.map_server_id_android_id = {}
        self.map_server_id_game_id = {}

        self.server_id_in_use = {}

        self.time_manager_state = "beginning_init"
        self.time_manager_t = 0
        self.time_manager_ending_t = None
        self.continue_game = True

        self.assignment_tcp = {}
        self.assignment_php = {}
        self.assignment = {}

        self.parametrization = {}
        self.roles = []

        # --- server parameters --- #

        self.keys = [
            "network", "game", "folders", "map_android_id_server_id",
            "parametrization", "assignment_tcp", "assignment_php", "map_php"]

        self.param = {}
        self.setup()

    def new(self):
        """when a new game is launched"""
        
        self.current_state = {s: [] for s in self.entries}

        self.firms_id = {}  # key: game_id, value: firm_id
        self.customers_id = {}  # key: game_id, value: customer_id

        self.bot_firms_id = {}
        self.bot_customers_id = {}
        
        self.map_server_id_android_id = {}
        self.map_server_id_game_id = {}

        self.server_id_in_use = {}

        self.time_manager_state = "beginning_init"
        self.time_manager_t = 0
        self.time_manager_ending_t = None
        self.continue_game = True

    def setup(self):

        for key in self.keys:

            # noinspection SpellCheckingInspection
            with open("hotelling_server/parameters/{}.json".format(key)) as file:
                self.param[key] = json.load(file)

    def write_param(self, key, new_value):

        self.controller.backup.write_param(key, new_value)

    def save(self):

        self.controller.backup.write(
            {
                "history": self.history,
                "current_state": self.current_state,
                "firms_id": self.firms_id,
                "customers_id": self.customers_id,
                "bot_firms_id": self.bot_firms_id,
                "bot_customers_id": self.bot_customers_id,
                "map_server_id_android_id": self.map_server_id_android_id,
                "map_server_id_game_id": self.map_server_id_game_id,
                "server_id_in_use": self.server_id_in_use,
                "roles": self.roles,
                "time_manager_t": self.controller.time_manager.t,
                "time_manager_ending_t": self.controller.time_manager.ending_t,
                "continue": self.controller.time_manager.continue_game,
                "time_manager_state": self.controller.time_manager.state,
                "assignment_tcp": self.assignment_tcp,
                "assignment_php": self.assignment_php,
                "parametrization": self.parametrization
            }
        )

    def write(self, key, game_id, value):

        self.current_state[key][game_id] = value

    def load(self, file):

        data = self.controller.backup.load(file=file)
        self.history = data["history"]
        self.current_state = data["current_state"]
        self.firms_id = data["firms_id"]
        self.customers_id = data["customers_id"]
        self.bot_firms_id = data["bot_firms_id"]
        self.bot_customers_id = data["bot_customers_id"]
        self.map_server_id_android_id = data["map_server_id_android_id"]
        self.map_server_id_game_id = data["map_server_id_game_id"]
        self.server_id_in_use = data["server_id_in_use"]
        self.roles = data["roles"]
        self.time_manager_state = data["time_manager_state"]
        self.time_manager_t = data["time_manager_t"]
        self.time_manager_ending_t = data["time_manager_ending_t"]
        self.continue_game = data["continue"]
        self.assignment_tcp = data["assignment_tcp"]
        self.assignment_php = data["assignment_php"]
        self.parametrization = data["parametrization"]

    def update_history(self):

        for s in self.entries:
            self.history[s].append(self.current_state[s])

