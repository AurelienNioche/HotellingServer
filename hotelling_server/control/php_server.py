from multiprocessing import Queue, Event
from threading import Thread, Timer
import requests as rq
import time
import json

from utils.utils import Logger


class PHPServer(Thread, Logger):

    name = "PHPServer"

    def __init__(self, controller):

        Thread.__init__(self)

        self.cont = controller

        self.queue = Queue()

        self.clients = {}

        self.shutdown_event = Event()
        self.wait_event = Event()

        self.server_address = None
        self.param = None

    def setup(self, param):

        self.param = param
        self.server_address = self.param["network"]["php_server"]
        self.server_address_messenger = self.param["network"]["messenger"]
        
    def run(self):

        while not self.shutdown_event.is_set():

            self.log("Waiting for a message...", level=1)
            msg = self.queue.get()
            self.log("I received msg '{}'.".format(msg), level=1)

            if msg and msg[0] == "Go":
                
                self.wait_event.clear()
                self.serve()

            if msg and msg[0] == "send_message":

                self.wait_event.clear()
                self.send_message(msg[1], msg[2])
                self.serve()

            if msg and msg[0] == "get_message":

                self.wait_event.clear()
                self.receive_messages()
                self.serve()

        self.log("I'm dead.")

    def get_waiting_list(self):

        while True:

            self.log("I will ask the distant server to the 'waiting_list' table.")

            response = self.send_request(
                demand_type="reading",
                table="waiting_list"
            )

            if response.text and response.text.split("&")[0] == "waiting_list":
            
                participants = [i for i in response.text.split("&")[1:] if i]
                break

        return participants

    def authorize_participants(self, participants, roles, game_ids):

        names = json.dumps(participants)
        game_ids = json.dumps(game_ids)
        roles = json.dumps(roles)

        while True:

            self.log("I will ask the distant server to fill the 'participants' table with {}".format(participants))

            response = self.send_request(
                demand_type="writing",
                table="participants",
                gameIds=game_ids,
                names=names,
                roles=roles
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

    def send_request(self, **kwargs):

        return rq.get(self.server_address, params=kwargs)
    
    def send_request_messenger(self, **kwargs):

        return rq.post(self.server_address_messenger, data=kwargs)

    def serve(self):

        while not self.wait_event.is_set():

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
                
    def treat_requests(self, n_requests):

        for i in range(n_requests):

            self.log("I'm treating the request no {}.".format(i))

            should_be_reply, response = self.queue.get()

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

    def shutdown(self):
        self.wait_event.set()

    def end(self):
        self.shutdown_event.set()
        self.queue.put("break")

