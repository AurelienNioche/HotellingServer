from multiprocessing import Queue, Event
from threading import Thread
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
        
    def run(self):

        while not self.shutdown_event.is_set():

            self.log("Waiting for a message...")
            msg = self.queue.get()
            self.log("I received msg '{}'.".format(msg))

            if msg and msg[0] == "Go":
                
                self.wait_event.clear()
                self.serve()

        self.log("I'm dead.")

    def get_waiting_list(self):

        data = {"demand_type": "reading", "table": "waiting_list"}

        while True:

            self.log("I will ask the distant server to the 'waiting_list' table.")
            response = rq.get(self.server_address, params=data)

            if response.text and response.text.split("&")[0] == "waiting_list":
            
                participants = [i for i in response.text.split("&")[1:] if i]
                break

        return participants

    def authorize_participants(self, participants, roles, game_ids):

        names = json.dumps(participants)
        game_ids = json.dumps(game_ids)
        roles = json.dumps(roles)

        data = {"demand_type": "writing",
                "table": "participants",
                "gameIds": game_ids,
                "names": names,
                "roles": roles}

        while True:

            self.log("I will ask the distant server to fill the 'participants' table with {}".format(participants))
            response = rq.get(self.server_address, params=data)

            self.log("I got the response '{}' from the distant server.".format(response.text))

            if response.text == "I inserted participants in 'participants' table.":
                break

    def ask_for_erasing_tables(self, tables):

        data = {"demand_type": "empty_tables", "table_names": json.dumps(tables)}

        while True:

            self.log("I will ask the distant server to erase tables.")
            response = rq.get(self.server_address, params=data)
            self.log("I got the response '{}' from the distant server.".format(response.text))

            if "Those tables have been erased." in response.text:
                break

    def serve(self):

        while not self.wait_event.is_set():

            try:

                data = {"demand_type": "reading", "table": "request"}
                response = rq.get(self.server_address, params=data)

                if response.text and response.text.split("&")[0] == "request":

                    requests = [i for i in response.text.split("&")[1:] if i]

                    if requests:
                        for request in requests:
                            self.cont.queue.put(("server_request", request))

                        self.log("I will treat {} request(s).".format(len(requests)))
                        self.treat_requests(n_requests=len(requests))

            except Exception as e:
                self.log("Got error '{}'.".format(e))
                
    def treat_requests(self, n_requests):

        for i in range(n_requests):

            self.log("I'm treating the request no {}.".format(i))

            should_be_reply, response = self.queue.get()

            if should_be_reply == "reply":

                data = {
                    "demand_type": "writing",
                    "table": "response",
                    "gameId": response["game_id"],
                    "response": response["response"]
                }

                response = rq.get(self.server_address, params=data)

                self.log("Response from distant server is: '{}'.".format(response.text))

            else:
                raise Exception("Something went wrong...")

    def shutdown(self):
        self.wait_event.set()

    def end(self):
        self.shutdown_event.set()
        self.queue.put("break")
