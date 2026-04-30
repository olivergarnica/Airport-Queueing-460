from collections import deque
import random

from DataObjects.Event import Event
from DataObjects.Server import Server


class MultiServerQueue:
    def __init__(self, name, num_servers, service_rate, completion_event_type):
        self.name = name
        self.servers = [
            Server(server_id=i, server_rate=service_rate)
            for i in range(num_servers)
        ]
        self.queue = deque()
        self.service_rate = service_rate
        self.completion_event_type = completion_event_type

        self.wait_times = []
        self.queue_length_log = []

    def idle_server(self):
        for server in self.servers:
            if not server.is_busy():
                return server
        return None

    def enter_queue(self, passenger_id, current_time, schedule, passengers):
        self.queue.append(passenger_id)
        self.queue_length_log.append((current_time, len(self.queue)))
        self.try_start_service(current_time, schedule, passengers)

    def try_start_service(self, current_time, schedule, passengers):
        while self.queue:
            server = self.idle_server()

            if server is None:
                return

            passenger_id = self.queue.popleft()
            passenger = passengers[passenger_id]

            passenger.tsa_service_start_time = current_time

            if passenger.tsa_queue_enter_time is not None:
                self.wait_times.append(current_time - passenger.tsa_queue_enter_time)

            server.start_service(current_time, passenger_id)

            service_time = random.expovariate(server.server_rate)

            schedule.add_event(Event(
                time=current_time + service_time,
                event_type=self.completion_event_type,
                entity_id=server.server_id,
                data={
                    "passenger_id": passenger_id,
                    "queue_name": self.name
                }
            ))

    def complete_service(self, server_id, current_time):
        server = self.servers[server_id]
        passenger_id = server.finish_service(current_time)
        return passenger_id