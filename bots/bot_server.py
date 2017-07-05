from multiprocessing import Queue, Event
import json

from utils.utils import Logger

from hotelling_server.control import server


class BotController(Logger):

    name = "BotController"

    def __init__(self):

        self.parameters = {}
        self.shutdown = Event()
        self.queue = Queue()

        self.setup()

        self.server = server.Server(controller=self)
        self.game = BotGame(controller=self)

    def setup(self):

        for key in ["network", "game", "folders", "map_android_id_server_id", "interface"]:
            with open("hotelling_server/parameters/{}.json".format(key)) as file:
                self.parameters[key] = json.load(file)

    def run(self):

        self.server.start()

        self.server.queue.put(("Go", ))

        while not self.shutdown.is_set():
            self.log("Waiting for a message.")
            message = self.queue.get()
            if message == "break":
                break
            else:
                self.handle_message(message)

        self.close_program()

    def close_program(self):
        self.log("Close program.")
        self.server.shutdown()
        self.server.end()
        self.shutdown.set()

    def handle_message(self, message):

        command = message[0]
        args = message[1:]
        if len(args):
            eval("self.{}(*args)".format(command))
        else:
            eval("self.{}()".format(command))

    def server_running(self):
        self.log("Server running.")

    def server_error(self):
        self.log("Server error.")
        self.queue.put("break")

    def server_request(self, server_data):
        response = self.game.handle_request(server_data)
        self.server.queue.put(("reply", response))

    def get_parameters(self, key):

        return self.parameters[key]


class BotGame(Logger):

    name = "BotGame"

    def __init__(self, controller):
        super().__init__()

        self.controller = controller

    def handle_request(self, request):

        self.log("Got request: '{}'.".format(request))

        # retrieve whole command
        whole = [i for i in request.split("/") if i != ""]

        try:
            # retrieve method
            command = eval("self.{}".format(whole[0]))

            # retrieve method arguments
            args = [int(a) if a.isdigit() else a for a in whole[1:]]

            # call method
            to_client = command(*args)

        except Exception as e:
            to_client, to_controller = (
                "Command contained in request not understood.\n"
                "{}".format(e),
                None)

        self.log("Reply '{}' to request '{}'.".format(to_client, request))
        return to_client

    def ask_init(self, *args):

        print(args)
        return "Va chier connard"



def main():

    bot_c = BotController()
    bot_c.run()


if __name__ == "__main__":

    main()