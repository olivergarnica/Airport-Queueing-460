from collections import deque
import random

from DataObjects.Event import Event
from DataObjects.Server import Server

class SecurityLane:
    def __init__(self, lane_id, service_rate, capacity, area_name):
        self.lane_id = lane_id
        self.area_name = area_name
        self.server = Server(server_id=lane_id, server_rate=service_rate)
        self.capacity = capacity
        self.queue = deque()

        self.wait_times = []
        self.blocked_count = 0
        self.queue_length_log = []

    def total_in_system(self):
        return len(self.queue) + int(self.server.is_busy())

    def has_space(self):
        return self.total_in_system() < self.capacity

    def enter_queue(self, passenger_id, current_time, schedule, passengers):
        if not self.has_space():
            self.blocked_count += 1
            return False

        passenger = passengers[passenger_id]
        passenger.security_queue_enter_time = current_time

        self.queue.append(passenger_id)
        self.queue_length_log.append((current_time, len(self.queue)))

        self.try_start_service(current_time, schedule, passengers)
        return True

    def try_start_service(self, current_time, schedule, passengers):
        if self.server.is_busy() or not self.queue:
            return

        passenger_id = self.queue.popleft()
        passenger = passengers[passenger_id]

        passenger.security_service_start_time = current_time
        self.wait_times.append(current_time - passenger.security_queue_enter_time)

        self.server.start_service(current_time, passenger_id)

        service_time = random.expovariate(self.server.server_rate)

        schedule.add_event(Event(
            time=current_time + service_time,
            event_type="SECURITY_SERVICE_COMPLETE",
            entity_id=self.lane_id,
            data={
                "passenger_id": passenger_id,
                "area_name": self.area_name
            }
        ))

    def complete_service(self, current_time):
        passenger_id = self.server.finish_service(current_time)
        return passenger_id

class SecurityArea:
    def __init__(self, num_lanes, service_rate, capacity, area_name):
        self.area_name = area_name
        self.lanes = [
            SecurityLane(
                lane_id=i,
                service_rate=service_rate,
                capacity=capacity,
                area_name=area_name
            )
            for i in range(num_lanes)
        ]

        self.overflow_queue = deque()
        self.overflow_wait_times = []

        self.blocked_attempts = 0
        self.total_attempts = 0

    def choose_lane(self):
        open_lanes = [lane for lane in self.lanes if lane.has_space()]

        if not open_lanes:
            return None

        return min(open_lanes, key=lambda lane: lane.total_in_system())

    def enter_security(self, passenger_id, current_time, schedule, passengers):
        self.total_attempts += 1

        lane = self.choose_lane()

        if lane is None:
            self.blocked_attempts += 1

            passenger = passengers[passenger_id]
            passenger.status = "security_overflow"
            passenger.security_overflow_enter_time = current_time

            self.overflow_queue.append(passenger_id)
            return False

        return lane.enter_queue(passenger_id, current_time, schedule, passengers)

    def try_drain_overflow(self, current_time, schedule, passengers):
        while self.overflow_queue:
            lane = self.choose_lane()

            if lane is None:
                return

            passenger_id = self.overflow_queue.popleft()
            passenger = passengers[passenger_id]

            if passenger.security_overflow_enter_time is not None:
                wait = current_time - passenger.security_overflow_enter_time
                passenger.security_blocked_time += wait
                self.overflow_wait_times.append(wait)
                passenger.security_overflow_enter_time = None

            passenger.status = "security_queue"

            lane.enter_queue(
                passenger_id,
                current_time,
                schedule,
                passengers
            )

    def complete_service(self, lane_id, current_time, schedule, passengers):
        lane = self.lanes[lane_id]

        passenger_id = lane.complete_service(current_time)
        passengers[passenger_id].security_service_end_time = current_time

        lane.try_start_service(current_time, schedule, passengers)

        self.try_drain_overflow(current_time, schedule, passengers)

        return passenger_id