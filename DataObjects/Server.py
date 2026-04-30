from enum import Enum, auto


class Server:
    class ServerState(Enum):
        IDLE = auto()
        BUSY = auto()

    def __init__(self, server_id, server_rate):
        self.server_id = server_id
        self.server_rate = server_rate
        self.state = Server.ServerState.IDLE
        self.busy_start_time = None
        self.total_busy_time = 0.0
        self.current_passenger_id = None

    def is_busy(self):
        return self.state == Server.ServerState.BUSY

    def start_service(self, current_time, passenger_id):
        self.state = Server.ServerState.BUSY
        self.busy_start_time = current_time
        self.current_passenger_id = passenger_id

    def finish_service(self, current_time):
        if self.state == Server.ServerState.BUSY and self.busy_start_time is not None:
            self.total_busy_time += current_time - self.busy_start_time

        finished_passenger_id = self.current_passenger_id

        self.state = Server.ServerState.IDLE
        self.current_passenger_id = None
        self.busy_start_time = None

        return finished_passenger_id