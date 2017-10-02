from utils.utils import Logger


class IDManager(Logger):

    name = "IDManager"

    def __init__(self, controller):

        self.controller = controller
        self.data = controller.data
        self.parameters = None
    
    def get_client_name_from_game_id(self, game_id):

        return self.data.param["map_php"][str(game_id)]

    def get_ids_from_android_id(self, android_id, max_n):

        self.log("Client with android id {} ask for information.".format(android_id))
        server_id = self.get_server_id(android_id)
        self.log("I associate server id '{}' to android id '{}'.".format(server_id, android_id))
        game_id = self.get_game_id(server_id, max_n)
        self.log("I associate game id '{}' to server id '{}'.".format(game_id, server_id))

        return server_id, game_id

    def get_server_id(self, android_id):

        server_id, new = self.get_mapping(android_id, self.data.param["map_android_id_server_id"])

        if new:
            self.data.save_param("map_android_id_server_id", self.data.param["map_android_id_server_id"])

        return server_id

    def get_game_id(self, server_id, max_n):

        game_id, new = self.get_mapping(server_id, self.data.map_server_id_game_id, max_n)

        if game_id != -1:

            if new:
                self.data.map_server_id_game_id.update({server_id: game_id})

            self.data.server_id_in_use[game_id] = server_id

        return game_id

    @staticmethod
    def get_mapping(input_id, mapping, max_n=-1):

        if input_id in mapping.keys():
            output_id = mapping[input_id]
            new = 0

        else:
            if len(mapping) == max_n:
                output_id = -1

            else:
                if len(mapping) > 0:
                    output_id = max(mapping.values()) + 1

                else:
                    output_id = 0

                mapping[input_id] = output_id

            new = 1

        return output_id, new

    def get_server_id_in_use(self):

        return self.data.server_id_in_use
