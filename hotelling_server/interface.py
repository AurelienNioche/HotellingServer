from os import path
from multiprocessing import Queue, Event

from PyQt5.QtCore import QObject, pyqtSignal, QTimer, Qt, QSettings
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QDesktopWidget, QFileDialog

from utils.utils import Logger

from .graphics import game_view, start_view, \
        setting_up_view, assignment_view_php, menubar, config_files_view, \
        erase_sql_tables_view, messenger, missing_players_view

from .message_box import MessageBox


class Communicate(QObject):
    signal = pyqtSignal()


class UI(QWidget, Logger, MessageBox):

    name = "Interface"
    app_name = "Duopoly Experiment"

    def __init__(self, model):

        super().__init__()

        self.mod = model

        self.occupied = Event()

        self.layout = QVBoxLayout()

        self.frames = dict()
        self.menubar_frames = dict()

        self.param = dict()
        self.old_param = dict()

        # refresh interface and update data (tables, figures, messenger)
        self.timer = QTimer(self)
        self.timer.setInterval(1000)

        # noinspection PyUnresolvedReferences
        self.timer.timeout.connect(self.update_game_view_data)
        self.timer.start()

        self.already_asked_for_saving_parameters = 0

        self.queue = Queue()

        self.communicate = Communicate()

        self.settings = QSettings("HumanoidVsAndroid", "Duopoly")

        self.controller_queue = None

        self.menubar = menubar.MenuBar(parent=self)

    # ------------------------ Default dimensions -------------------------------------------------- #
    @property
    def dimensions(self):

        desktop = QDesktopWidget()
        dimensions = desktop.screenGeometry()  # get screen geometry
        w = dimensions.width() * 0.9  # 90% of the screen width
        h = dimensions.height() * 0.8  # 80% of the screen height

        return 300, 100, w, h

    # ------------------------ Called by controller methods ---------------------------------------- #

    def set_previous_parameters(self, params):
        """Set previous json parameters from data through controller.
        These params are going to be passed to views."""

        self.param = params.copy()

        # save old params
        self.old_param = params.copy()

    def set_server_address_game_frame(self, address):
        """Set server address displayed in game_view"""

        self.frames["game"].set_server_address(address)

    def set_assignment_game_frame(self, assignment):
        """Set assignment displayed in game view rows"""

        self.frames["game"].set_assignment(assignment)

    def update_waiting_list_assignment_frame(self, participants):

        self.frames["assign_php"].update_waiting_list(participants)

    def controller_new_message(self, args):

        self.menubar_frames["messenger"].new_message_from_user(args[0], args[1])

    # ----------------- called by views methods -------------------------------------------------------- #
    def save_parameters(self, key, data):

        self.param[key] = data
    # -------------------------------------------------------------------------------------------------- #

    def _get_parameters(self, *keys):
        """get selected params in order to pass them to view's constructors"""
        return {k: v for k, v in self.param.items() if k in keys}

    def setup(self):

        self.controller_queue = self.mod.controller.queue
        self.send_go_signal()
        self.communicate.signal.connect(self.look_for_msg)

        # get saved geometry or set regular geometry
        try:
            self.restoreGeometry(self.settings.value("geometry"))

        except Exception as e:
            self.log(str(e), level=3)
            self.log("Setting regular dimensions", level=1)
            self.setGeometry(*self.dimensions)

    def prepare_frames(self):

        # ------------------- Main window frames ---------------------------- #
        self.frames["start"] = \
            start_view.StartFrame(parent=self,
                param=self._get_parameters("network", "folders", "game", "parametrization"))

        self.frames["assign_php"] = \
            assignment_view_php.AssignmentFramePHP(parent=self,
                param=self._get_parameters("game", "assignment_php", "sql_tables"))

        self.frames["game"] = \
            game_view.GameFrame(parent=self,
                param=self._get_parameters("network"))

        self.frames["setting_up"] = \
            setting_up_view.SettingUpFrame(parent=self)

        # ------------------- Menu bar frames ---------------------------- #

        self.menubar_frames["config_files"] = \
            config_files_view.ConfigFilesWindow(parent=self,
            param=self._get_parameters("parametrization", "network", "game", "sql_tables", "folders"))

        self.menubar_frames["erase_sql_tables"] = \
            erase_sql_tables_view.EraseSQLTablesFrame(parent=self,
            param=self._get_parameters("sql_tables"))

        self.menubar_frames["messenger"] = \
            messenger.MessengerFrame(parent=self)

        self.menubar_frames["missing_players"] = \
            missing_players_view.MissingPlayersFrame(parent=self,
            param=self._get_parameters("game"))

        # ---------------------------------------------------------------- #

    def prepare_window(self):

        self.setWindowTitle(self.app_name)

        grid = QGridLayout()

        for frame in self.frames.values():

            # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
            grid.addWidget(frame, 0, 0)

        grid.setAlignment(Qt.AlignCenter)

        self.layout.addLayout(grid, stretch=1)
        self.setLayout(self.layout)

    def closeEvent(self, event):

        msg = "By quitting, you will erase ('participants', 'response', 'request'," "'waiting_list') sql tables."
        question = "Are you sure you want to quit?"
        focus = "Yes"

        if self.isVisible() and self.show_question(msg=msg, question=question, focus=focus):

            if not self.already_asked_for_saving_parameters:

                self.check_for_saving_parameters()

            self.save_geometry()
            self.log("Close window", level=1)
            self.close_menubar_windows()

            # ---- stop timers ----- #

            if getattr(self.frames["assign_php"], "timer") is not None:
                self.frames["assign_php"].timer.stop()

            self.close_window()
            event.accept()

        else:
            self.log("Ignore close window.", level=1)
            event.ignore()

    def close_menubar_windows(self):

        for window in self.menubar_frames.values():
            window.close()

    def save_geometry(self):

        self.settings.setValue("geometry", self.saveGeometry())

    def check_for_erasing_tables(self):

        tables = "participants", "waiting_list", "request", "response"
        self.php_erase_sql_tables(tables=tables)

    def check_for_saving_parameters(self):

        self.already_asked_for_saving_parameters = 1

        cond = sorted(self.old_param.items()) != sorted(self.param.items())

        if cond:

            if self.show_question("Do you want to save the change in parameters and assignment?"):

                # assignment_php is the only param we do not want to save
                self.param.pop("assignment_php")

                for key in self.param.keys():
                    self.write_parameters(key, self.param[key])

            else:
                self.log('Saving of parameters aborted.', level=1)

    # ------------------------- Called every second methods ------------------------------------- #

    def update_figures(self, data):
        self.frames["game"].update_statistics(data["statistics"])

    def update_tables(self, data):
        self.frames["game"].update_tables(data)
        self.frames["game"].set_trial_number(data["time_manager_t"])

    # ------------------------- Method used in order to treat requests from controller ------------ #

    def look_for_msg(self):

        if not self.occupied.is_set():
            self.occupied.set()

            msg = self.queue.get()
            self.log("I received message '{}'.".format(msg))

            command = getattr(self, msg[0])
            args = msg[1:]
            if args:
                command(*args)
            else:
                command()

            # Able now to handle a new display instruction
            self.occupied.clear()

        else:
            # noinspection PyCallByClass, PyTypeChecker
            QTimer.singleShot(100, self.look_for_msg)

    # ------------------------- "Show" methods -------------------------------------------------- #
    def show_frame_game(self):

        self.frames["game"].prepare()

        for frame in self.frames.values():
            frame.hide()

        self.frames["game"].show()

    def show_frame_setting_up(self):

        for frame in self.frames.values():
            frame.hide()

        self.frames["setting_up"].show()

    def show_frame_start(self):

        for frame in self.frames.values():
            frame.hide()

        self.frames["start"].prepare()
        self.frames["start"].show()

    def show_frame_assignment_php(self):

        for frame in self.frames.values():
            frame.hide()

        self.frames["assign_php"].prepare(param=self._get_parameters("network"))
        self.frames["assign_php"].show()

    def show_menubar_frame_config_files(self):

        self.menubar_frames["config_files"].show()

    def show_menubar_frame_erase_sql_tables(self):

        self.menubar_frames["erase_sql_tables"].show()

    def show_menubar_frame_messenger(self):

        self.menubar_frames["messenger"].show()

    def show_menubar_frame_missing_players(self):

        self.menubar_frames["missing_players"].show()

    # ---------------------------------------------------------------------------------------------------------- #

    def error_loading_session(self):

        self.show_warning(msg="Error in loading the selected file. Please select another one!")
        self.frames["setting_up"].show()
        self.frames["load_game_new_game"].open_file_dialog()

    def server_error(self, error_message):

        retry = self.show_critical_and_retry(msg="Server error.\nError message: '{}'.".format(error_message))

        if retry:
            self.show_frame_setting_up()
            self.retry_server()
        else:
            self.close_window()
            self.close()

    def fatal_error(self, error_message):

        self.show_critical(msg="Fatal error.\nError message: '{}'.".format(error_message))
        self.close_window()
        self.close()

    def force_to_quit_game(self):

        msg = "Some players did not end their last turn!"
        question = "Do you want to quit anyway?"
        yes = "Quit game"
        no = "Do not quit"

        reply_yes = self.show_question(msg=msg, question=question, yes=yes, no=no)

        if reply_yes:
            self.show_frame_start()
            self.stop_bots()
            self.force_to_stop_game()
            self.check_for_erasing_tables()

        else:
            self.frames["game"].stop_button.setEnabled(True)

    def unexpected_client_id(self, client_id):

        msg = "Unexpected id: '{}'.".format(client_id)

        question = "Do you want to go back to assignment menu?"

        yes = "Quit game and go back to assignment"
        no = "Do not quit"

        go_back = self.show_question(msg=msg, question=question, yes=yes, no=no)

        if go_back:
            self.stop_bots()
            self.stop_server()

        else:
            self.frames["game"].stop_button.setEnabled(True)

    def open_file_dialog(self):

        folder_to_open = path.expanduser(self.param["folders"]["save"])

        # noinspection PyArgumentList
        file_choice = QFileDialog().getOpenFileName(
            self, '',
            folder_to_open,
            "Backup files (*.p)")
        self.log("User choose file '{}'.".format(file_choice))
        file = file_choice[0]

        return file

    def open_file_to_load_game(self):

        file = self.open_file_dialog()

        if file:
            self.set_server_parameters(param=self.param)
            self.load_game(file)

        else:
            self.show_info(msg="No file selected.")

    # ----------------- Methods putting something in controller queue -------------- #

    def update_game_view_data(self):
        self.controller_queue.put(("ui_update_game_view_data", ))

    def load_game(self, file):
        self.controller_queue.put(("ui_load_game", file))

    def stop_game(self):
        self.controller_queue.put(("ui_stop_game", ))

    def force_to_stop_game(self):
        self.controller_queue.put(("ui_force_to_stop_game", ))

    def close_window(self):
        self.controller_queue.put(("ui_close_window", ))

    def retry_server(self):
        self.controller_queue.put(("ui_retry_server", ))

    def write_parameters(self, key, data):
        self.controller_queue.put(("ui_write_parameters", key, data))

    def send_go_signal(self):
        self.controller_queue.put(("ui_send_go_signal", ))

    def send_reboot_signal(self):
        self.controller_queue.put(("reboot", ))

    def stop_bots(self):
        self.controller_queue.put(("ui_stop_bots", ))

    def stop_server(self):
        self.controller_queue.put(("ui_stop_server",))

    def look_for_alive_players(self):
        self.controller_queue.put(("ui_look_for_alive_players", ))

    def php_scan_button(self):
        self.controller_queue.put(("ui_php_scan_button", ))

    def php_erase_sql_tables(self, tables):
        self.controller_queue.put(("ui_php_erase_sql_tables", tables))

    def php_run_game(self):
        self.controller_queue.put(("ui_php_run_game", ))

    def set_assignment(self, assignment):
        self.controller_queue.put(("ui_set_assignment", assignment))

    def set_parametrization(self, param):
        self.controller_queue.put(("ui_set_parametrization", param))

    def set_server_parameters(self, param):
        self.controller_queue.put(("ui_set_server_parameters", param))

    def send_message_to_user(self, user, msg):
        self.controller_queue.put(("ui_new_message", user, msg))

    def set_missing_players(self, value):
        self.controller_queue.put(("ui_php_set_missing_players", value))

    # ---------------------- #
