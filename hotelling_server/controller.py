from multiprocessing import Queue, Event
from threading import Thread

from utils.utils import Logger 
from hotelling_server.control import backup, data, game, server, statistician, id_manager, time_manager


class Controller(Thread, Logger):

    name = "Controller"

    def __init__(self, model):

        super().__init__()

        self.mod = model

        # For receiving inputs
        self.queue = Queue()

        self.data = data.Data(controller=self)
        self.time_manager = time_manager.TimeManager(controller=self)
        self.id_manager = id_manager.IDManager(controller=self)
        self.backup = backup.Backup(controller=self)
        self.statistician = statistician.Statistician(controller=self)
        self.server = server.Server(controller=self)
        self.game = game.Game(controller=self)

        # For giving instructions to graphic process
        self.graphic_queue = self.mod.ui.queue
        self.communicate = self.mod.ui.communicate

        # For giving go signal to server
        self.server_queue = self.server.queue
        self.running_game = Event()

        self.shutdown = Event()
        self.fatal_error = Event()
        self.continue_game = Event()

    def run(self):

        self.log("Waiting for a message.")
        go_signal_from_ui = self.queue.get()
        self.log("Got go signal from UI: '{}'.".format(go_signal_from_ui))

        self.ask_interface("show_frame_setting_up")

        # Launch server manager
        self.server.start()
        self.server_queue.put(("Go", ))

        while not self.shutdown.is_set():
            self.log("Waiting for a message.")
            message = self.queue.get()
            self.handle_message(message)

        self.close_program()

    def launch_game(self):

        self.ask_interface("show_frame_setting_up")

        # Go signal for launching the (properly speaking) server

        self.fatal_error.clear()
        self.continue_game.set()
        self.running_game.set()

        self.ask_interface("show_frame_game", self.get_current_data())

        self.log("Game launched.")

    def stop_game_first_phase(self):

        self.log("Received stop task")
        self.continue_game.clear()
        self.time_manager.stop_as_soon_as_possible()
        # Wait then for a signal of the request manager for allowing interface to show a button to starting menu

    def stop_game_second_phase(self):

        self.running_game.clear()
        self.ask_interface("show_frame_load_game_new_game")

    def close_program(self):

        self.log("Close program.")
        self.shutdown.set()
        self.running_game.set()

        # For aborting launching of the (properly speaking) server if it was not launched
        self.server_queue.put(("Abort",))

        # Stop server if it was running
        self.server.end()
        self.server.shutdown()
        self.log("Program closed.")

    def fatal_error_of_communication(self):

        if not self.fatal_error.is_set():
            self.fatal_error.set()
            self.running_game.clear()
            self.continue_game.clear()

            self.ask_interface("fatal_error_of_communication")

    def ask_interface(self, instruction, arg=None):

        self.graphic_queue.put((instruction, arg))
        self.communicate.signal.emit()

    # ------------------------------- Message handling ----------------------------------------------- #

    def handle_message(self, message):

        command = message[0]
        args = message[1:]
        if len(args):
            eval("self.{}(*args)".format(command))
        else:
            eval("self.{}()".format(command))

    # ------------------------------ Server interface -----------------------#

    def server_running(self):
        self.log("Server running.")
        self.ask_interface("show_frame_load_game_new_game")
        # self.server_queue.put(("reply", response))

    def server_error(self, error_message):
        self.log("Server error.")
        self.ask_interface("server_error", error_message)

    def server_request(self, server_data):
        response = self.game.handle_request(server_data)
        self.server_queue.put(("reply", response))

    # ------------------------------ UI interface (!!!) ----------------------#

    def ui_run_game(self, interface_parameters):
        self.log("UI ask 'run game'.")
        self.time_manager.setup()
        self.game.new(interface_parameters)
        self.launch_game()

    def ui_load_game(self, file):
        self.log("UI ask 'load game'.")
        self.data.load(file)
        self.time_manager.setup()
        self.launch_game()
        self.game.launch_bots()

    def ui_stop_game(self):
        self.log("UI ask 'stop game'.")
        self.stop_game_first_phase()

    def ui_close_window(self):
        self.log("UI ask 'close window'.")
        self.close_program()

    def ui_retry_server(self):
        self.log("UI ask 'retry server'.")
        self.server_queue.put(("Go",))

    def ui_save_interface_parameters(self, param):
        self.log("UI ask 'save game parameters'.")
        self.data.save_param("interface", param)
        self.log("Save interface parameters.")

    # ------------------------------ Game interface (!!!) -------------------------------------- #

    def game_stop_game(self):
        self.log("'Game' ask 'stop game'.")
        self.stop_game_second_phase()

    def update_data_viewer(self):
        self.log("'Game' ask 'update_data_viewer'.")

        # needs to be moved elsewhere?
        self.statistician.compute_distance()
        self.statistician.compute_mean_extra_view_choices()
        self.statistician.compute_profits()
        self.statistician.compute_mean_utility()

        parameters = self.get_current_data()
        self.ask_interface("update_data_viewer", parameters)

    # ---------------------- Parameters management -------------------------------------------- #
    
    def get_current_data(self):
        
        return {
                    "history": self.data.history,
                    "current_state": self.data.current_state,
                    "bot_firms_id": self.data.bot_firms_id,
                    "firms_id": self.data.firms_id,
                    "bot_customers_id": self.data.bot_customers_id,
                    "customers_id": self.data.customers_id,
                    "server_id_in_use": self.data.server_id_in_use,
                    "roles": self.data.roles,
                    "time_manager_t": self.data.controller.time_manager.t,
                    "time_manager_state": self.data.controller.time_manager.state,
                    "statistics": self.statistician.data,
                    "map_server_id_game_id": self.data.map_server_id_game_id
                    
               }

    def get_parameters(self, key):

        return self.data.param[key]
