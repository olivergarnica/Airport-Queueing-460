from collections import deque
import random

from DataObjects.Event import Event
from DataObjects.Server import Server


class Gate:
    def __init__(self, gate_id, boarding_service_rate):
        self.gate_id = gate_id
        self.boarding_server = Server(server_id=gate_id, server_rate=boarding_service_rate)

        self.waiting_pool = []
        self.boarding_queue = deque()

    def passenger_arrives(self, passenger_id, current_time, passengers):
        passenger = passengers[passenger_id]
        passenger.gate_arrival_time = current_time
        passenger.status = "at_gate"

        self.waiting_pool.append(passenger_id)

    def release_group(self, flight, group_number, current_time, schedule, passengers):
        eligible = []

        for passenger_id in self.waiting_pool:
            passenger = passengers[passenger_id]

            if (
                passenger.flight_id == flight.flight_id
                and passenger.boarding_group <= group_number
            ):
                eligible.append(passenger_id)

        random.shuffle(eligible)

        for passenger_id in eligible:
            self.waiting_pool.remove(passenger_id)

            passenger = passengers[passenger_id]
            passenger.boarding_queue_enter_time = current_time
            passenger.status = "boarding_queue"

            self.boarding_queue.append(passenger_id)

        self.try_start_boarding(current_time, schedule, passengers)

    def try_start_boarding(self, current_time, schedule, passengers):
        if self.boarding_server.is_busy() or not self.boarding_queue:
            return

        passenger_id = self.boarding_queue.popleft()
        passenger = passengers[passenger_id]

        passenger.boarding_start_time = current_time
        passenger.status = "boarding"

        self.boarding_server.start_service(current_time, passenger_id)

        service_time = random.expovariate(self.boarding_server.server_rate)

        schedule.add_event(Event(
            time=current_time + service_time,
            event_type="BOARDING_SERVICE_COMPLETE",
            entity_id=self.gate_id,
            data={"passenger_id": passenger_id}
        ))

    def complete_boarding(self, current_time, schedule, passengers):
        passenger_id = self.boarding_server.finish_service(current_time)

        passenger = passengers[passenger_id]
        passenger.boarding_end_time = current_time
        passenger.system_done_time = current_time
        passenger.status = "boarded"

        self.try_start_boarding(current_time, schedule, passengers)

        return passenger_id