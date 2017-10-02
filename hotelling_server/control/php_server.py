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
        self.treated_requests = 0

        self.shutdown_event = Event()
        self.wait_event = Event()

        self.timer = Timer(self, 1, self.check_all_client_time_since_last_request)
        self.timer.start()

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

    def authorize_participants(self, participants, roles):

        names = json.dumps(participants)
        game_ids = json.dumps(list(range(len(participants))))
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

    def ask_for_erasing_tables(self):

        data = {"demand_type": "empty_tables"}

        while True:

            self.log("I will ask the distant server to erase tables.")
            response = rq.get(self.server_address, params=data)
            self.log("I got the response '{}' from the distant server.".format(response.text))

            if response.text == "Tables 'waiting_list', 'participants', 'request', 'response' have been erased.":
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

        # while self.treated_requests != n_requests:  # Why a while and not a for loop ?
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

    def check_client_connection(self, ip, response):

        if ip not in self.clients.keys() and "reply_init" in response:
            self.clients[ip] = {}
            self.clients[ip]["time"] = time.time()
            self.clients[ip]["game_id"] = int(response.split("/")[2])
        else:
            self.clients[ip]["time"] = time.time()

    def check_all_client_time_since_last_request(self):

        for client_ip in self.clients.keys():

            client_time = self.clients[client_ip]["time"]
            time_now = time.time()
            time_since_last_request = int(time_now - client_time)

            self.update_client_time_on_interface(ip=client_ip, time_diff=time_since_last_request)

    def update_client_time_on_interface(self, ip, time_diff):

        game_id = self.clients[ip]["game_id"]
        role = self.cont.data.roles[game_id]
        role_id = None

        if role == "customer":
            if game_id in self.cont.data.customers_id.keys():
                role_id = self.cont.data.customers_id[game_id]

        elif role == "firm":
            if game_id in self.cont.data.firms_id.keys():
                role_id = self.cont.data.firms_id[game_id]

        if role_id is not None:
            self.update_time(role=role, role_id=role_id, time_diff=time_diff)
    
    # This method should be moved elsewhere
    def update_time(self, role, role_id, time_diff):
        self.cont.data.current_state["time_since_last_request_{}s".format(role)][role_id] = str(time_diff)


class Timer(Thread):
    def __init__(self, parent, wait, func):
        super().__init__()
        self.parent = parent
        self.func = func
        self.wait = wait

    def run(self):

        while not self.parent.shutdown_event.is_set():
            if not self.parent.wait_event.is_set():
                self.func()
            Event().wait(self.wait)
