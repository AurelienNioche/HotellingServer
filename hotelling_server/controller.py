from multiprocessing import Queue, Event
from threading import Thread

from utils.utils import Logger
from hotelling_server.control import backup, data, game, statistician, \
        id_manager, time_manager, initialization


class Controller(Thread, Logger):

    name = "Controller"

    def __init__(self, model):

        super().__init__()

        self.mod = model

        # For receiving inputs
        self.queue = Queue()

        self.running_game = Event()
        self.running_server = Event()

        self.shutdown = Event()
        self.fatal_error = Event()
        self.continue_game = Event()
        self.device_scanning_event = Event()

        self.data = data.Data(controller=self)
        self.time_manager = time_manager.TimeManager(controller=self)
        self.id_manager = id_manager.IDManager(controller=self)
        self.backup = backup.Backup(controller=self)
        self.statistician = statistician.Statistician(controller=self)
        self.game = game.Game(controller=self)
        self.init = initialization.Init(controller=self)

        self.server = None

        # For giving instructions to graphic process
        self.graphic_queue = self.mod.ui.queue
        self.communicate = self.mod.ui.communicate

        # For giving go signal to server
        self.server_queue = None

    def run(self):

        self.log("Waiting for a message.")
        go_signal_from_ui = self.queue.get()
        self.log("Got go signal from UI: '{}'.".format(go_signal_from_ui))

        # Send previous params to UI
        self.ask_interface("set_previous_parameters", self.data.param)

        # Prepares ui frames
        self.ask_interface("prepare_frames")
        self.ask_interface("prepare_window")

        self.ask_interface("show_frame_setting_up")

        # Start
        self.ask_interface("show_frame_start")

        while not self.shutdown.is_set():

            self.log("Waiting for a message.", level=1)
            message = self.queue.get()
            self.handle_message(message)

        self.close_program()

    def launch_game(self):

        self.ask_interface("show_frame_setting_up")

        self.fatal_error.clear()
        self.continue_game.set()
        self.running_game.set()
        self.server.running_game.set()
        self.ask_interface("show_frame_game")
        self.log("Game launched.")

    def stop_game_first_phase(self):

        self.log("Received stop task")
        self.continue_game.clear()
        self.time_manager.stop_as_soon_as_possible()

    def stop_game_second_phase(self):

        self.continue_game.clear()
        self.running_game.clear()
        self.server.running_game.clear()

    def close_program(self):

        self.log("Close program.")
        self.running_game.set()

        if self.server_queue is not None:
            self.erase_tables()
            self.server_queue.put(("Abort",))
            self.stop_server()
            self.server.end()

        self.shutdown.set()

    def fatal_error_of_communication(self):

        if not self.fatal_error.is_set():

            self.fatal_error.set()
            self.running_game.clear()
            self.continue_game.clear()

            self.ask_interface("fatal_error_of_communication")

    def ask_interface(self, instruction, arg=None):

        if arg is not None:
            self.graphic_queue.put((instruction, arg))
        else:
            self.graphic_queue.put((instruction, ))

        self.communicate.signal.emit()

    def stop_server(self):

        self.log("Stop server.")
        self.server.stop_to_serve()

    def start_server(self):

        if not self.running_server.is_set():
            self.server.start()
            self.server_queue.put(("serve", ))

        self.running_server.set()
        self.log("Server running.")

    def scan_network_for_new_devices(self):

        self.start_server()
        self.device_scanning_event.set()

    def add_device_to_map_android_id_server_id(self, server_data):

        android_id = server_data.split("/")[-1]
        self.id_manager.get_ids_from_android_id(android_id, max_n=1)

        response = "error/adding_new_device"
        self.server_queue.put(("reply", response))
        self.stop_server()

        self.device_scanning_event.clear()
        self.ask_interface("stop_scanning_network")

    def erase_tables(self):
        """ 
        this method does not use 
        server queue because it needs to be run at 
        shutdown. Otherwise server does not have the time 
        to treat_requests and tables are not erased.
        """
        tables = "participants", "waiting_list", "request", "response"
        self.server.ask_for_erasing_tables(tables=tables)

    # ------------------------------- Message handling ----------------------------------------------- #

    def handle_message(self, message):

        command = message[0]
        args = message[1:]
        func = getattr(self, command)

        if len(args):
            func(*args)
        else:
            func()

    # ------------------------------ Server interface ----------------------------------------#

    def server_error(self, error_message):

        self.log("Server error.")
        self.ask_interface("server_error", error_message)

    def server_request(self, server_data):
        
        # when using device manager to add new clients to json mapping
        if self.device_scanning_event.is_set():
            self.add_device_to_map_android_id_server_id(server_data)
        
        # When game is launched
        elif "ask_init" in server_data:
            response = self.init.ask_init(server_data)
            self.server_queue.put((response[0], response[1]))

        # init admin
        elif "ask_admin_init" in server_data:
            response = self.init.ask_admin_init()
            self.server_queue.put((response[0], response[1]))

        else:
            response = self.game.handle_request(server_data)
            self.server_queue.put((response[0], response[1]))

    def server_update_client_time_on_interface(self, args):
        """
        param 0: role
        param 1: role_id
        param 2: time since last request
        """
        self.data.current_state["time_since_last_request_{}s".format(
            args[0])][args[1]] = str(args[2])

    def server_new_message(self, user_name, message):

        self.log("Got new message from distant server coming from {}: '{}'.".format(user_name, message))
        self.ask_interface("controller_new_message", (user_name, message))

    def server_update_assignment_frame(self, waiting_list):

        n_player = self.data.param["game"]["n_customers"] + self.data.param["game"]["n_firms"]

        if len(waiting_list) <= n_player:
            participants = waiting_list
        else:
            participants = waiting_list[:n_player]

        self.ask_interface("update_waiting_list_assignment_frame", participants)
   
    # ------------------------------ UI interface  -------------------------------------------#

    def ui_set_server(self, server_class):
        """
        instantiate server if it doesn't exists. 
        if it exists check if its a different type of server
        if it is the case instantiate new server
        else do nothing
        """
        
        server = getattr(self, "server")
        
        if server is None or server.name != server_class.name: 

            self.log("Server's class: {}".format(server_class), level=1)
            self.server = server_class(controller=self)
            self.server_queue = self.server.main_queue
            self.init.set_server_class(server_class)
            self.ask_interface("set_server_class_parametrization_frame", server_class)
            self.ask_interface("enable_server_related_menubar")

    def ui_set_server_parameters(self, param):
        self.log("Setting server parameters from interface: {}".format(param), level=1)
        self.server.setup(param)

        # start server
        self.start_server()

        self.ask_interface("set_server_address_game_frame", self.server.server_address)

    def ui_set_assignment(self, assignment):
        self.log("Setting game assignement from interface: {}".format(assignment), level=1)
        self.data.assignment = assignment
        self.init.set_assignment(assignment)
        self.ask_interface("set_assignment_game_frame", assignment)

    def ui_set_parametrization(self, param):
        self.log("Setting parametrization from interface : {}".format(param), level=0)
        self.data.parametrization = param

    def ui_tcp_run_game(self):
        self.log("UI ask 'run game'.")
        self.data.new()
        self.time_manager.setup()
        self.launch_game()
        self.game.new()

    def ui_load_game(self, file):
        self.log("UI ask 'load game'.")
        self.data.load(file)
        
        # set assignment for interface (display game_view) and init
        assignment = self.data.assignment
        self.init.set_assignment(assignment)
        self.ask_interface("set_assignment_game_frame", assignment)

        self.time_manager.setup()
        self.launch_game()
        self.game.load()

    def ui_stop_game(self):
        self.log("UI ask 'stop game'.")
        self.stop_game_first_phase()

    def ui_force_to_stop_game(self):
        self.log("UI asks 'force to stop game'.")
        self.stop_game_second_phase()

    def ui_close_window(self):
        self.log("UI ask 'close window'.")
        self.close_program()

    def ui_retry_server(self):
        self.log("UI ask 'retry server'.")
        self.server_queue.put(("game",))

    def ui_write_parameters(self, key, value):
        self.log("UI ask 'write parameters'.")
        self.data.write_param(key, value)
        self.log("Write interface parameters to json files.")

    def ui_update_game_view_data(self):
        """
        update figures and tables 
        on game view.
        does it only when game is running
        """

        if self.running_game.is_set():
            self.log("UI asks 'update data'.", level=1)
            self.ask_interface("update_tables", self.get_current_data())
            self.ask_interface("update_figures", self.get_current_data())

    def ui_stop_bots(self):
        self.log("UI ask 'stop bots'.")
        self.game.stop_bots()

    def ui_stop_server(self):
        self.log("UI asks 'stop server'.")
        self.stop_server()

    def ui_look_for_alive_players(self):

        self.log("UI asks 'look for alive players'.")
        
        if self.game.is_ended():
            
            # display start frame
            self.ask_interface("show_frame_start")

            # stop bots 
            self.game.stop_bots()

        else:

            self.ask_interface("force_to_quit_game")

    def ui_new_message(self, user_name, message):

        self.log("Got new message from ui for {}: '{}'.".format(user_name, message))
        self.server.side_queue.put(("send_message", user_name, message))

    def ui_php_run_game(self):

        # ---------- get roles, participants, and game_ids in assignment ------- # 
        roles = [i[2] for i in self.data.assignment if i[3] is False]
        participants = [i[1] for i in self.data.assignment if i[3] is False]
        game_ids = [i[0] for i in self.data.assignment if i[3] is False]
        # --------------------------------------------------- # 

        # ----- write participants mapping to json file ---- # 
        mapping = {str(game_id): name for game_id, name, role, bot in self.data.assignment}
        
        self.data.param["map_php"] = mapping
        self.data.write_param("map_php", mapping)
        self.data.write_param("assignment_php", self.data.assignment)
        # --------------------------------------------------- # 

        # --------- Authorize participants to run game ------ # 
        self.server.side_queue.put(("authorize_participants", participants, roles, game_ids))
        # --------------------------------------------------- # 

        self.ask_interface("show_frame_parametrization")

        # ------- Run game -----------------------------------# 
        self.log("UI ask 'run game'.")
        self.data.new()
        self.time_manager.setup()
        self.launch_game()
        self.game.new()
        # --------------------------------------------------- # 

    def ui_php_scan_button(self):

        self.server.side_queue.put(("get_waiting_list", ))

    def ui_php_erase_sql_tables(self, tables):
        
        if self.running_server.is_set():
            self.server.side_queue.put(("erase_sql_tables", tables))

        else:
            self.ask_interface("show_warning", "Server is not configured!")

    def ui_php_set_missing_players(self, value):

        if self.server is not None and self.server.server_address is not None:

            self.server.side_queue.put(("set_missing_players", value))

    # ------------------------------ Time Manager interface ------------------------------------ #

    def time_manager_stop_game(self):
        self.log("'TimeManager' asks 'stop game'.")
        self.stop_game_second_phase()

    def time_manager_compute_figures(self):

        self.log("'TimeManager' asks 'compute_figures'")

        # Needs to be moved elsewhere?
        self.statistician.compute_distance()
        self.statistician.compute_mean_extra_view_choices()
        self.statistician.compute_profits()
        self.statistician.compute_mean_utility()

    # ------------------------------ Initialization interface ------------------------------------ #

    def init_get_ids_from_client_name_tcp(self, server_id, game_id):

        self.init.queue.put(*(server_id, game_id))

    def init_get_client_name_from_game_id_php(self, game_id):

        name = self.id_manager.get_client_name_from_game_id(game_id)

        self.init.queue.put(name)
        
    # ---------------------- Parameters management -------------------------------------------- #

    def get_current_data(self):

        return {
            "current_state": self.data.current_state,
            "bot_firms_id": self.data.bot_firms_id,
            "firms_id": self.data.firms_id,
            "bot_customers_id": self.data.bot_customers_id,
            "customers_id": self.data.customers_id,
            "roles": self.data.roles,
            "time_manager_t": self.data.controller.time_manager.t,
            "statistics": self.statistician.data,
            "map_server_id_game_id": self.data.map_server_id_game_id,
            "assignment": self.data.assignment
        }

    def get_parameters(self, key):

        return self.data.param[key]
