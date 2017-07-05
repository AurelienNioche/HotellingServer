from multiprocessing import Queue, Event
from threading import Thread

from utils.utils import log
from hotelling_server.control import backup, data, game, server, parameters, statistician


class Controller(Thread):

    name = "Controller"

    def __init__(self, model):

        super().__init__()

        self.mod = model

        # For receiving inputs
        self.queue = Queue()

        self.data = data.Data(controller=self)
        self.parameters = parameters.Parameters(controller=self)
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

        log("Waiting for a message.", name=self.name)
        go_signal_from_ui = self.queue.get()
        log("Got go signal from UI: '{}'.".format(go_signal_from_ui), name=self.name)

        self.ask_interface("show_frame_setting_up")

        # Launch server manager
        self.server.start()
        self.server_queue.put(("Go", ))

        while not self.shutdown.is_set():
            log("Waiting for a message.", name=self.name)
            message = self.queue.get()
            self.handle_message(message)

        self.close_program()

    def launch_game(self, param):

        self.ask_interface("show_frame_setting_up")

        # Go signal for launching the (properly speaking) server

        self.fatal_error.clear()
        self.continue_game.set()
        self.running_game.set()

        self.game.setup(param)

        self.ask_interface("show_frame_game", )

        log("Game launched.", self.name)

    def stop_game_first_phase(self):

        log("Received stop task", self.name)
        self.continue_game.clear()
        # Wait then for a signal of the request manager for allowing interface to show a button to starting menu

    def stop_game_second_phase(self):

        self.running_game.clear()
        self.ask_interface("show_frame_load_game_new_game")

    def close_program(self):

        log("Close program.", self.name)
        self.shutdown.set()
        self.running_game.set()

        # For aborting launching of the (properly speaking) server if it was not launched
        self.server_queue.put(("Abort",))

        # Stop server if it was running
        self.server.end()
        self.server.shutdown()
        log("Program closed.", self.name)

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

    # ------------------------------ Server interface ----------------------------------------------- #

    def server_running(self):
        log("Server running.", self.name)
        self.ask_interface("show_frame_load_game_new_game")
        # self.server_queue.put(("reply", response))

    # ------------------------------ UI interface (!!!) -------------------------------------- #

    def ui_run_game(self, interface_parameters):
        log("UI ask 'run game'.", self.name)
        self.launch_game(param=interface_parameters)

    def ui_load_game(self, file):
        self.data.load(file)
        self.launch_game(param=None)
        log("UI ask 'load game'.", self.name)

    def ui_stop_game(self):
        log("UI ask 'stop game'.", self.name)
        self.stop_game_first_phase()

    def ui_close_window(self):
        log("UI ask 'close window'.", self.name)
        self.close_program()

    def ui_retry_server(self):
        log("UI ask 'retry server'.", self.name)
        self.server_queue.put(("Go",))

    def ui_save_game_parameters(self, param):
        log("UI ask 'save game parameters'.", self.name)
        self.parameters.save("interface", param)
        log("Save interface parameters.", self.name)

    # ------------------------------ Game interface (!!!) -------------------------------------- #

    def game_stop_game(self):
        log("'Game' ask 'stop game'.", self.name)
        self.stop_game_second_phase()
