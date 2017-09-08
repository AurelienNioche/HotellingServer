from multiprocessing import Queue, Event
from subprocess import getoutput

from PyQt5.QtCore import QObject, pyqtSignal, QTimer, Qt, QSettings
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QMessageBox, QDesktopWidget

from .graphics import game_view, loading_view, parametrization_view, setting_up_view, assignement_view, devices_view
from utils.utils import Logger


class Communicate(QObject):
    signal = pyqtSignal()


class UI(QWidget, Logger):

    name = "Interface"
    app_name = "Android Experiment"

    def __init__(self, model):

        super().__init__()

        self.mod = model

        self.occupied = Event()

        self.layout = QVBoxLayout()

        self.frames = dict()

        # refresh interface and update data (tables, figures) 
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_data)
        self.timer.start()

        self.already_asked_for_saving_parameters = 0

        self.queue = Queue()

        self.communicate = Communicate()

        self.controller_queue = None

    @property
    def dimensions(self):

        desktop = QDesktopWidget()
        dimensions = desktop.screenGeometry()  # get screen geometry
        w = dimensions.width() * 0.9  # 90% of the screen width
        h = dimensions.height() * 0.8  # 80% of the screen height

        return 300, 100, w, h

    def setup(self):

        self.check_update()

        self.controller_queue = self.mod.controller.queue

        self.frames["devices"] = \
            devices_view.DevicesFrame(parent=self)

        self.frames["assign"] = \
            assignement_view.AssignementFrame(parent=self)

        self.frames["parameters"] = \
            parametrization_view.ParametersFrame(parent=self)

        self.frames["game"] = \
            game_view.GameFrame(parent=self)

        self.frames["setting_up"] = \
            setting_up_view.SettingUpFrame(parent=self)

        self.frames["load_game_new_game"] = \
            loading_view.LoadGameNewGameFrame(parent=self)

        self.setWindowTitle(self.app_name)

        self.communicate.signal.connect(self.look_for_msg)

        self.setGeometry(*self.dimensions)

        grid = QGridLayout()

        for frame in self.frames.values():

            # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
            grid.addWidget(frame, 0, 0)

        grid.setAlignment(Qt.AlignCenter)
        self.layout.addLayout(grid, stretch=1)

        self.setLayout(self.layout)
        
        # get saved geometry
        try: 
            settings = QSettings("tamere", "duopoly")
            self.restoreGeometry(settings.value("geometry"))

        except Exception as e:
            self.log(str(e)) 

        self.send_go_signal()

    def check_update(self):

        self.log("I check for updates.")
        getoutput("git fetch")
        git_msg = getoutput("git diff origin/master")
        self.log("Git message is: '{}'".format(git_msg))
        if git_msg and "remote: Counting objects: " in git_msg:
            if self.show_question(
                    "An update is available.",
                    question="Do you want to update now?", yes="Yes", no="No", focus="Yes"):
                git_output = getoutput("git pull")
                self.log("User wants to update. Git message is: {}".format(git_output))
                success = 0
                if "Updating" in git_output:
                    success = 1
                else:
                    for msg in ["git stash", "git pull", "git stash pop"]:
                        git_output = getoutput(msg)
                        self.log("Command is '{}' Git message is: '{}'".format(msg, git_output))
                    if "Updating" in git_output:
                        success = 1
                if success:
                    if self.show_question(
                            "You have to close the app and relaunch it for modifications to apply.",
                            question="Do you close the app now?", yes="Yes", no="No", focus="Yes"):
                        self.close()
                else:
                    self.show_warning("An error occured. No modifications have been done.")

    def closeEvent(self, event):

        if self.isVisible() and self.show_question("Are you sure you want to quit?"):

            if not self.already_asked_for_saving_parameters:

                self.check_for_saving_parameters()

            self.save_geometry()
            self.log("Close window")
            self.close_window()
            event.accept()

        else:
            self.log("Ignore close window.")
            event.ignore()

    def save_geometry(self):

        settings = QSettings("tamere", "duopoly")
        settings.setValue("geometry", self.saveGeometry())

    def check_for_saving_parameters(self):

        self.already_asked_for_saving_parameters = 1

        cond1 = sorted(self.mod.controller.data.param["parametrization"].items()) != \
            sorted(self.frames["parameters"].get_parameters().items())

        cond2 = sorted(self.mod.controller.data.param["assignement"]) != \
            sorted(self.frames["assign"].get_parameters())

        if cond1 or cond2:

            if self.show_question("Do you want to save the change in parameters and assignement?"):

                self.save_parameters("parametrization", self.frames["parameters"].get_parameters())
                self.save_parameters("assignement", self.frames["assign"].get_parameters())

            else:
                self.log('Saving of parameters aborted.')

    def update_data(self):

        if self.mod.controller.running_game.is_set():
            self.update_tables()
            self.update_figures()

    def update_figures(self, *args):

        data = self.mod.controller.get_current_data()["statistics"]
        self.frames["game"].update_statistics(data)

    def update_tables(self, *args):

        data = self.mod.controller.get_current_data()
        self.frames["game"].update_tables(data)
        self.frames["game"].set_trial_number(data["time_manager_t"])

    def show_frame_devices(self, *args):

        for frame in self.frames.values():
            frame.hide()

        self.frames["devices"].prepare()
        self.frames["devices"].show()

    def show_frame_load_game_new_game(self, *args):

        for frame in self.frames.values():
            frame.hide()

        self.frames["load_game_new_game"].prepare()
        self.frames["load_game_new_game"].show()

    def show_frame_game(self, *args):

        self.frames["game"].prepare(args[0])

        for frame in self.frames.values():
            frame.hide()

        self.frames["game"].show()

    def show_frame_setting_up(self, *args):

        for frame in self.frames.values():
            frame.hide()

        self.frames["setting_up"].show()

    def show_frame_parameters(self, *args):

        for frame in self.frames.values():
            frame.hide()

        self.frames["parameters"].prepare()
        self.frames["parameters"].show()

    def show_frame_assignement(self, *args):

        for frame in self.frames.values():
            frame.hide()

        self.frames["assign"].prepare()
        self.frames["assign"].show()

    def show_question(self, msg, question="", yes="Yes", no="No", focus="No"):
        """question with customs buttons"""

        msgbox = QMessageBox()
        msgbox.setText(msg)
        msgbox.setInformativeText(question)
        msgbox.setIcon(QMessageBox.Question)
        quit = msgbox.addButton(yes, QMessageBox.ActionRole)
        dont = msgbox.addButton(no, QMessageBox.ActionRole)
        msgbox.setDefaultButton((quit, dont)[focus==no])

        msgbox.exec_()

        return msgbox.clickedButton() == quit

    def show_warning(self, msg):

        button_reply = QMessageBox().warning(
            self, "", msg,
            QMessageBox.Ok
        )

        return button_reply == QMessageBox.Yes

    def show_critical_and_retry(self, msg):

        button_reply = QMessageBox().critical(
            self, "", msg,  # Parent, title, message
            QMessageBox.Close | QMessageBox.Retry,  # Buttons
            QMessageBox.Retry  # Default button
        )

        return button_reply == QMessageBox.Retry

    def show_critical_and_ok(self, msg):

        button_reply = QMessageBox().critical(
            self, "", msg,  # Parent, title, message
            QMessageBox.Close | QMessageBox.Ok,  # Buttons
            QMessageBox.Ok  # Default button
        )

        return button_reply == QMessageBox.Ok

    def show_critical(self, msg):

        QMessageBox().critical(
            self, "", msg,  # Parent, title, message
            QMessageBox.Close
        )

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

    def force_to_quit_game(self, *args):

        msg = "Some players did not end their last turn!"
        question = "Do you want to quit anyway?"
        yes = "Quit game"
        no = "Do not quit"

        quit = self.show_question(msg=msg, question=question, yes=yes, no=no)

        if quit:
            self.show_frame_load_game_new_game()
            self.stop_bots()
            self.stop_server()
        else:
            self.frames["game"].stop_button.setEnabled(True)

    def unexpected_client_id(self, client_id):

        msg = "Unexpected id: '{}'.".format(client_id)

        question = "Do you want to go back to assignement menu?"

        yes = "Quit game and go back to assignement"
        no = "Do not quit"

        go_back = self.show_question(msg=msg, question=question, yes=yes, no=no)

        if go_back:
            self.show_frame_assignement()
            self.stop_bots()
            self.stop_server()
        else:
            self.frames["game"].stop_button.setEnabled(True)

    def devices_quit_without_saving(self):

        msg = "You did not save your modifications."
        question = "Quit without saving?"
        yes = "Quit"
        no = "Save and quit"
        focus = "Quit"

        quit = self.show_question(msg=msg, question=question, yes=yes, no=no, focus=focus)

        if not quit:
            self.frames["devices"].save_mapping()

        self.show_frame_load_game_new_game()

    def fatal_error_of_communication(self):

        ok = self.show_critical_and_ok(msg="Fatal error of communication. You need to relaunch the game AFTER "
                                           "having relaunched the apps on Android's clients.")

        if ok:
            self.show_load_game_new_game_frame()

        else:
            if not self.close():
                self.manage_fatal_error_of_communication()
                
    def stop_scanning_network(self, *args):

        self.log("Controller asks 'stop scanning network'")
        self.frames["devices"].show_device_added()

    def look_for_msg(self):

        if not self.occupied.is_set():
            self.occupied.set()

            msg = self.queue.get()
            self.log("I received message '{}'.".format(msg))

            command = eval("self.{}".format(msg[0]))
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

    def get_parameters(self):
        return self.mod.controller.data.param["parametrization"]

    def get_current_interface_parameters(self):
        return {"parametrization": self.frames["parameters"].get_parameters(),
                "assignement": self.frames["assign"].get_parameters()}

    def get_game_parameters(self):
        return self.mod.controller.data.param["game"]

    def run_game(self):
        self.controller_queue.put(("ui_run_game", self.get_current_interface_parameters()))

    def load_game(self, file):
        self.controller_queue.put(("ui_load_game", file))

    def stop_game(self):
        self.controller_queue.put(("ui_stop_game", ))

    def close_window(self):
        self.controller_queue.put(("ui_close_window", ))

    def retry_server(self):
        self.controller_queue.put(("ui_retry_server", ))

    def save_parameters(self, key, data):
        self.controller_queue.put(("ui_save_game_parameters", key, data))

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

