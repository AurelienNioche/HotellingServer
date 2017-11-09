from multiprocessing import Queue, Event
from threading import Thread, Event
import requests as rq
import json

from utils.utils import Logger


class BasePHPServer(Thread, Logger):

    request_frequency = 0.1

    def __init__(self, controller):

        Thread.__init__(self)

        self.cont = controller

        self.main_queue = Queue()
        self.side_queue = Queue()

        self.shutdown_event = Event()
        self.serve_event = Event()
        self.running_game = Event()

        self.server_address = None
        self.server_address_messenger = None
        self.param = None

    def setup(self, param):

        self.param = param
        self.server_address = self.param["network"]["php_server"]
        self.server_address_messenger = self.param["network"]["messenger"]

    def run(self):

        while not self.shutdown_event.is_set():

            self.log("Waiting for a message...", level=1)
            msg = self.main_queue.get()
            self.log("I received msg '{}'.".format(msg), level=1)

            if msg and msg[0] == "serve":
                
                self.serve_event.set()
                self.serve()

        self.log("I'm dead.")

    def serve(self):

        while self.serve_event.is_set():

            self.treat_sides_requests()
            
            if self.running_game.is_set(): 
                self.treat_game_requests()

            Event().wait(self.request_frequency)

    def treat_game_requests(self):

        response = self.send_request(
            demand_type="reading",
            table="request"
        )

        if response.text and response.text.split("&")[0] == "request":

            requests = [i for i in response.text.split("&")[1:] if i]

            if requests:
                for request in requests:
                    self.cont.queue.put(("server_request", request))

                self.log("I will treat {} request(s).".format(len(requests)))
                self.treat_requests(n_requests=len(requests))

    def treat_sides_requests(self):

        # check for new msg received
        self.receive_messages()

        # check for new interactions with sql tables
        if not self.side_queue.empty():

            msg = self.side_queue.get()

            if msg and msg[0] == "send_message":

                self.send_message(msg[1], msg[2])

            elif msg and msg[0] == "erase_sql_tables":
                self.ask_for_erasing_tables(tables=msg[1:])

            elif msg and msg[0] == "get_waiting_list":

                waiting_list = self.get_waiting_list()
                self.cont.queue.put(("server_update_assignment_frame", waiting_list))

            elif msg and msg[0] == "authorize_participants":

                self.authorize_participants(*msg[1:])

            elif msg and msg[0] == "set_missing_players":

                self.set_missing_players(msg[1])

    def treat_requests(self, n_requests):

        for i in range(n_requests):

            self.log("I'm treating the request no {}.".format(i))

            should_be_reply, response = self.main_queue.get()

            if should_be_reply == "reply":

                response = self.send_request(
                    demand_type="writing",
                    table="response",
                    gameId=response["game_id"],
                    response=response["response"]
                )

                self.log("Response from distant server is: '{}'.".format(response.text))

            elif should_be_reply == "error":

                self.log("I will not send response now (code error is '{}').".format(response))

            else:
                raise Exception("Something went wrong...")

    def receive_messages(self):

        self.log("I send a request for collecting the messages.", level=1)

        response = self.send_request_messenger(
            demandType="serverHears",
            userName="none",
            message="none"
        )

        if "reply" in response.text:
            args = [i for i in response.text.split("/") if i]
            n_messages = int(args[1])

            self.log("I received {} new message(s).".format(n_messages), level=1)

            if n_messages:
                for arg in args[2:]:
                    sep_args = arg.split("<>")

                    user_name, message = sep_args[0], sep_args[1]

                    self.cont.queue.put(("server_new_message", user_name, message))

                    self.log("I send confirmation for message '{}'.".format(arg))
                    self.send_request_messenger(
                        demandType="serverReceiptConfirmation",
                        userName=user_name,
                        message=message
                    )

    def send_message(self, user_name, message):

        self.log("I send a message for '{}': '{}'.".format(user_name, message))

        response = self.send_request_messenger(
            demandType="serverSpeaks",
            userName=user_name,
            message=message
        )

        self.log("I receive: {}".format(response))

    def stop_to_serve(self):
        self.serve_event.clear()

    def end(self):
        self.shutdown_event.set()
        self.serve_event.clear()

        self.main_queue.put("break")


class RequestManager:

    def send_request(self, **kwargs):
        
        while True:
            try:
                return rq.get(self.server_address, params=kwargs)

            except Exception:
                self.log("I got a connection error. Try again.", level=0)
                Event().wait(self.request_frequency)
    
    def send_request_messenger(self, **kwargs):

        while True:
            try:
                return rq.post(self.server_address_messenger, data=kwargs)

            except Exception:
                self.log("I got a connection error. Try again.", level=0)
                Event().wait(self.request_frequency)


class PHPServer(BasePHPServer, RequestManager):

    name = "PHPServer"

    def __init__(self, controller):
        
        super().__init__(controller)

    def get_waiting_list(self):

        while True:

            self.log("I will ask the distant server to the 'waiting_list' table.", level=1)

            response = self.send_request(
                demand_type="reading",
                table="waiting_list"
            )

            if response.text and response.text.split("&")[0] == "waiting_list":
            
                participants = [i for i in response.text.split("&")[1:] if i]
                break

        return participants

    def get_users(self):

        while True:

            self.log("I will ask the distant server to the 'users' table.")

            response = self.send_request(
                demand_type="reading",
                table="users"
            )

            if response.text and response.text.split("&")[0] == "users":
            
                users = [i.split("#") for i in response.text.split("&")[1:] if i]
                break

        return users 

    def register_users(self, usernames, passwords):

        while True:

            self.log("I will ask the distant server to write the 'users' table.")

            response = self.send_request(
                demand_type="writing",
                table="users",
                names=usernames,
                passwords=passwords
            )

            self.log("I got the response '{}' from the distant server.".format(response.text))

            if response.text == "I inserted users in 'users' table.":
                break

    def register_waiting_list(self, usernames):

        while True:

            self.log("I will ask the distant server to write the 'waiting_list' table.")

            response = self.send_request(
                demand_type="writing",
                table="waiting_list",
                names=usernames,
            )

            self.log("I got the response '{}' from the distant server.".format(response.text))


            if response.text == "I inserted names in 'waiting_list' table.":
                break

    def authorize_participants(self, participants, roles, game_ids):

        while True:

            self.log("I will ask the distant server to fill the 'participants' table with {}".format(participants))

            response = self.send_request(
                demand_type="writing",
                table="participants",
                gameIds=json.dumps(game_ids),
                names=json.dumps(participants),
                roles=json.dumps(roles)
            )

            self.log("I got the response '{}' from the distant server.".format(response.text))

            if response.text == "I inserted participants in 'participants' table.":
                break

    def ask_for_erasing_tables(self, tables):

        while True:

            self.log("I will ask the distant server to erase tables.")

            response = self.send_request(
                demand_type="empty_tables",
                table_names=json.dumps(tables)
            )

            self.log("I got the response '{}' from the distant server.".format(response.text))

            if "Tables" in response.text and "have been erased" in response.text:
                break

    def set_missing_players(self, value):

        while True:

            self.log("I will ask the distant server to update the 'missing_players' variable with {}".format(value))

            response = self.send_request(
                demand_type="writing",
                table="game",
                missingPlayers=value
            )

            self.log("I got the response '{}' from the distant server.".format(response.text))

            if response.text == "I updated missing players in 'game' table.":
                break

