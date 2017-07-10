import json
from utils.utils import Logger


class Data(Logger):

    def __init__(self, controller):

        self.controller = controller

        # --- game variables --- #

        self.entries = [
            "firm_positions", "firm_prices", "firm_profits",
            "customer_firm_choices", "customer_extra_view_choices", "customer_utility", "n_client", 
            "customer_replies", "active_replied", "passive_gets_results", "active_gets_results",
            "firm_states", "init_done"
        ]

        self.history = {s: [] for s in self.entries}
        self.current_state = {s: [] for s in self.entries}

        self.firms_id = {}  # key: game_id, value: firm_id
        self.customers_id = {}  # key: game_id, value: customer_id

        self.map_server_id_android_id = {}
        self.map_server_id_game_id = {}

        self.server_id_in_use = {}

        self.time_manager_state = ""

        self.roles = []

        # --- server parameters --- #

        self.keys = ["network", "game", "folders", "map_android_id_server_id", "interface"]
        self.isparam = False
        self.param = {}
        self.setup()

    def setup(self):

        for key in self.keys:
            with open("hotelling_server/parameters/{}.json".format(key)) as file:
                self.param[key] = json.load(file)

    def save_param(self, key, new_value):
       
        self.controller.backup.save_param(key, new_value)
    
    def save(self):

        self.controller.backup.write(
                {
                    "history": self.history,
                    "current_state": self.current_state,
                    "firms_id": self.firms_id,
                    "customers_id": self.customers_id,
                    "map_server_id_android_id": self.map_server_id_android_id,
                    "map_server_id_game_id": self.map_server_id_game_id,
                    "server_id_in_use": self.server_id_in_use,
                    "roles": self.roles,
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
        self.map_server_id_android_id = data["map_server_id_android_id"]
        self.map_server_id_game_id = data["map_server_id_game_id"]
        self.server_id_in_use = data["server_id_in_use"]
        self.roles = data["roles"]

    def update_history(self):

        for s in self.entries:
            self.history[s].append(self.current_state[s])

