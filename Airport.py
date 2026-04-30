from collections import deque
import random

from DataObjects.Event import Event
from DataObjects.Flight import Flight
from DataObjects.Passenger import Passenger
from DataObjects.Schedule import Schedule
from QueueSystem import MultiServerQueue
from Security import SecurityArea
from Gate import Gate

class Airport:
    def __init__(
        self,
        num_gates,
        regular_id_servers,
        precheck_id_servers,
        clear_id_servers,
        id_service_rate,
        precheck_service_rate,
        clear_service_rate,
        num_regular_security_lanes,
        regular_security_service_rate,
        regular_security_capacity,
        num_precheck_security_lanes,
        precheck_security_service_rate,
        precheck_security_capacity,
        boarding_service_rate
    ):
        self.schedule = Schedule()
        self.passengers = {}
        self.flights = {}

        self.next_passenger_id = 0
        self.next_flight_id = 0
        self.time_series = []

        self.regular_id_queue = MultiServerQueue(
            name="regular",
            num_servers=regular_id_servers,
            service_rate=id_service_rate,
            completion_event_type="ID_SERVICE_COMPLETE"
        )

        self.precheck_id_queue = MultiServerQueue(
            name="precheck",
            num_servers=precheck_id_servers,
            service_rate=precheck_service_rate,
            completion_event_type="ID_SERVICE_COMPLETE"
        )

        self.clear_id_queue = MultiServerQueue(
            name="clear",
            num_servers=clear_id_servers,
            service_rate=clear_service_rate,
            completion_event_type="ID_SERVICE_COMPLETE"
        )

        self.regular_security_area = SecurityArea(
            num_lanes=num_regular_security_lanes,
            service_rate=regular_security_service_rate,
            capacity=regular_security_capacity,
            area_name="regular"
        )

        self.precheck_security_area = SecurityArea(
            num_lanes=num_precheck_security_lanes,
            service_rate=precheck_security_service_rate,
            capacity=precheck_security_capacity,
            area_name="precheck"
        )

        self.gates = {
            gate_id: Gate(gate_id, boarding_service_rate)
            for gate_id in range(num_gates)
        }

        self.current_time = 0.0    
    
    def airport_busy_weight(self, time):
        t = time % 1440  # handles times beyond one day

        # 2:00-6:00 Late night: least busy
        if 120 <= t < 360:
            return 1

        # 6:00-9:00 Morning rush: busiest
        elif 360 <= t < 540:
            return 6

        # 9:00-12:00 Mid-morning: 3rd busiest
        elif 540 <= t < 720:
            return 4

        # 12:00-16:00 Afternoon: 4th busiest
        elif 720 <= t < 960:
            return 3

        # 16:00-19:00 Evening rush: 2nd busiest
        elif 960 <= t < 1140:
            return 5

        # 19:00-22:00 Evening: 5th busiest
        elif 1140 <= t < 1320:
            return 2

        # 22:00-2:00 Late night: 6th busiest
        else:
            return 1.5
    
    def sample_departure_time(self, start_time, end_time):
        max_weight = 6

        while True:
            candidate_time = random.uniform(start_time, end_time)
            weight = self.airport_busy_weight(candidate_time)

            if random.random() < weight / max_weight:
                return candidate_time    
    
    def gate_is_available_for_departure(self, gate_id, departure_time, boarding_duration=30, post_departure_buffer=10):

        new_start = departure_time - boarding_duration
        new_end = departure_time + post_departure_buffer

        for existing_flight in self.flights.values():
            if existing_flight.gate_id != gate_id:
                continue

            existing_start = existing_flight.departure_time - boarding_duration
            existing_end = existing_flight.departure_time + post_departure_buffer

            overlap = new_start < existing_end and existing_start < new_end

            if overlap:
                return False

        return True
    
    def generate_poisson_arrival_times(self, start_time, end_time, num_passengers):
        """
        Generates exactly num_passengers arrival times inside [start_time, end_time]
        with Poisson-process-like spacing.
        True Poisson process has a random number of arrivals.
        Here, the num of passengers is fixed by flight capacity/load factor.
        Conditional on having exactly N arrivals in a time window, the arrival
        times of a homogeneous Poisson process are distributed like sorted
        uniform points. This exponential-spacing construction gives that behavior.
        """

        if num_passengers <= 0:
            return []

        window_length = end_time - start_time

        # num_passengers arrivals creates num_passengers + 1 gaps:
        # before first arrival, between arrivals, and after last arrival.
        spacings = [
            random.expovariate(1.0)
            for _ in range(num_passengers + 1)
        ]

        total_spacing = sum(spacings)

        arrival_times = []
        cumulative = 0.0

        for i in range(num_passengers):
            cumulative += spacings[i]
            arrival_time = start_time + (cumulative / total_spacing) * window_length
            arrival_times.append(arrival_time)

        return arrival_times

    def seed_flights(self, num_flights, start_time, end_time):

        flights_created = 0
        attempts = 0
        max_attempts = num_flights * 200

        while flights_created < num_flights and attempts < max_attempts:
            attempts += 1

            departure_time = self.sample_departure_time(start_time, end_time)

            candidate_gates = list(self.gates.keys())
            random.shuffle(candidate_gates)

            chosen_gate = None

            for gate_id in candidate_gates:
                if self.gate_is_available_for_departure(gate_id, departure_time):
                    chosen_gate = gate_id
                    break

            if chosen_gate is None:
                continue

            flight_id = self.next_flight_id
            self.next_flight_id += 1

            capacity = random.choice([140, 180, 200])
            num_groups = random.randint(3, 5)

            flight = Flight(
                flight_id=flight_id,
                gate_id=chosen_gate,
                departure_time=departure_time,
                capacity=capacity,
                num_groups=num_groups
            )

            self.flights[flight_id] = flight

            self.seed_passengers_for_flight(flight)

            self.schedule.add_event(Event(
                time=flight.boarding_open_time,
                event_type="BOARDING_OPEN",
                entity_id=flight_id
            ))

            self.schedule.add_event(Event(
                time=flight.departure_time,
                event_type="FLIGHT_DEPARTURE",
                entity_id=flight_id
            ))

            flights_created += 1

        if flights_created < num_flights:
            print(
                f"Only created {flights_created} out of {num_flights} flights. "
                "Try increasing the number of gates, widening the time window, or reducing num_flights."
            )
    
    def seed_passengers_for_flight(self, flight, load_factor=0.85):
        """
        Passenger arrivals occur between: 180 minutes 75 minutes before departure
        The arrival times are Poisson-process-like, conditioned on the number
        of passengers for the flight.
        """

        num_passengers = int(flight.capacity * load_factor)

        arrival_start_time = flight.departure_time - 180
        arrival_end_time = flight.departure_time - 75

        arrival_times = self.generate_poisson_arrival_times(
            start_time=arrival_start_time,
            end_time=arrival_end_time,
            num_passengers=num_passengers
        )

        for airport_arrival_time in arrival_times:
            passenger_id = self.next_passenger_id
            self.next_passenger_id += 1

            boarding_group = random.randint(1, flight.num_groups)

            has_precheck, has_clear = self.sample_passenger_programs()

            passenger = Passenger(
                passenger_id=passenger_id,
                flight_id=flight.flight_id,
                gate_id=flight.gate_id,
                boarding_group=boarding_group,
                airport_arrival_time=airport_arrival_time,
                has_precheck=has_precheck,
                has_clear=has_clear
            )

            self.passengers[passenger_id] = passenger
            flight.passengers.append(passenger_id)

            self.schedule.add_event(Event(
                time=airport_arrival_time,
                event_type="PASSENGER_ARRIVAL",
                entity_id=passenger_id
            ))

    # Randomly assigns regular, precheck or clear
    # Off the data we found roughly:
    # 4.935% = 4.9% have clear
    # 12.99% = 13% have TSAPre
    def sample_passenger_programs(self):
        has_clear = random.random() < 0.049
        has_precheck = random.random() < 0.129
        return has_precheck, has_clear

    # Logic for going through all the events in the schedule
    def run(self, max_time):
        while self.schedule.has_events():
            event = self.schedule.next_event()
            self.current_time = event.time

            if self.current_time > max_time:
                break

            if event.event_type == "PASSENGER_ARRIVAL":
                self.handle_passenger_arrival(event)

            elif event.event_type == "ID_SERVICE_COMPLETE":
                self.handle_id_service_complete(event)

            elif event.event_type == "SECURITY_SERVICE_COMPLETE":
                self.handle_security_service_complete(event)

            elif event.event_type == "GATE_ARRIVAL":
                self.handle_gate_arrival(event)

            elif event.event_type == "BOARDING_OPEN":
                self.handle_boarding_open(event)

            elif event.event_type == "BOARDING_GROUP_CALL":
                self.handle_boarding_group_call(event)

            elif event.event_type == "BOARDING_SERVICE_COMPLETE":
                self.handle_boarding_service_complete(event)

            elif event.event_type == "FLIGHT_DEPARTURE":
                self.handle_flight_departure(event)
            
            self.log_system_state()
            

    def handle_passenger_arrival(self, event):
        passenger_id = event.entity_id
        passenger = self.passengers[passenger_id]

        passenger.status = "id_queue"
        passenger.tsa_queue_enter_time = self.current_time

        # If a passenger has CLEAR, they go through CLEAR identity verification first.
        if passenger.has_clear:
            self.clear_id_queue.enter_queue(
                passenger_id,
                self.current_time,
                self.schedule,
                self.passengers
            )

        # If no CLEAR but has PreCheck, they go through PreCheck ID.
        elif passenger.has_precheck:
            self.precheck_id_queue.enter_queue(
                passenger_id,
                self.current_time,
                self.schedule,
                self.passengers
            )

        # regular ID check.
        else:
            self.regular_id_queue.enter_queue(
                passenger_id,
                self.current_time,
                self.schedule,
                self.passengers
            )

    def handle_id_service_complete(self, event):
        passenger_id = event.data["passenger_id"]
        queue_name = event.data["queue_name"]
        server_id = event.entity_id

        passenger = self.passengers[passenger_id]
        passenger.tsa_service_end_time = self.current_time
        passenger.status = "security_queue"

        if queue_name == "regular":
            self.regular_id_queue.complete_service(server_id, self.current_time)
            self.regular_id_queue.try_start_service(
                self.current_time,
                self.schedule,
                self.passengers
            )
        elif queue_name == "precheck":
            self.precheck_id_queue.complete_service(server_id, self.current_time)
            self.precheck_id_queue.try_start_service(
                self.current_time,
                self.schedule,
                self.passengers
            )
        elif queue_name == "clear":
            self.clear_id_queue.complete_service(server_id, self.current_time)
            self.clear_id_queue.try_start_service(
                self.current_time,
                self.schedule,
                self.passengers
            )

        self.route_to_security(passenger_id)
      
    def handle_security_service_complete(self, event):
        lane_id = event.entity_id
        area_name = event.data["area_name"]

        if area_name == "precheck":
            passenger_id = self.precheck_security_area.complete_service(
                lane_id,
                self.current_time,
                self.schedule,
                self.passengers
            )
        else:
            passenger_id = self.regular_security_area.complete_service(
                lane_id,
                self.current_time,
                self.schedule,
                self.passengers
            )

        passenger = self.passengers[passenger_id]
        passenger.status = "walking_to_gate"

        walking_time = random.uniform(3, 12)

        self.schedule.add_event(Event(
            time=self.current_time + walking_time,
            event_type="GATE_ARRIVAL",
            entity_id=passenger_id
        ))
        
    def handle_gate_arrival(self, event):
        passenger_id = event.entity_id
        passenger = self.passengers[passenger_id]

        flight = self.flights[passenger.flight_id]

        # If the passenger gets to the gate after departure, they missed the flight.
        if self.current_time >= flight.departure_time:
            passenger.missed_flight = True
            passenger.status = "missed_flight"
            return

        gate = self.gates[passenger.gate_id]
        gate.passenger_arrives(passenger_id, self.current_time, self.passengers)

        if flight.current_boarding_group is not None:
            if passenger.boarding_group <= flight.current_boarding_group:
                gate.release_group(
                    flight,
                    flight.current_boarding_group,
                    self.current_time,
                    self.schedule,
                    self.passengers
                )

    def handle_boarding_open(self, event):
        flight_id = event.entity_id
        flight = self.flights[flight_id]

        flight.status = "boarding"
        flight.current_boarding_group = 1

        self.schedule.add_event(Event(
            time=self.current_time,
            event_type="BOARDING_GROUP_CALL",
            entity_id=flight_id,
            data={"group": 1}
        ))

    def handle_boarding_group_call(self, event):
        flight_id = event.entity_id
        group = event.data["group"]

        flight = self.flights[flight_id]

        if flight.status != "boarding":
            return

        if self.current_time >= flight.departure_time:
            return

        flight.current_boarding_group = group

        gate = self.gates[flight.gate_id]

        gate.release_group(
            flight,
            group,
            self.current_time,
            self.schedule,
            self.passengers
        )

        if group < flight.num_groups:
            group_interval = 3  # minutes between boarding group calls

            next_call_time = self.current_time + group_interval

            if next_call_time < flight.departure_time:
                self.schedule.add_event(Event(
                    time=next_call_time,
                    event_type="BOARDING_GROUP_CALL",
                    entity_id=flight_id,
                    data={"group": group + 1}
                ))

    def handle_boarding_service_complete(self, event):
        passenger_id = event.data["passenger_id"]
        passenger = self.passengers[passenger_id]
        flight = self.flights[passenger.flight_id]
        gate = self.gates[event.entity_id]

        finished_passenger_id = gate.boarding_server.finish_service(self.current_time)

        if self.current_time >= flight.departure_time:
            passenger.missed_flight = True
            passenger.status = "missed_flight"
            return

        passenger.boarding_end_time = self.current_time
        passenger.system_done_time = self.current_time
        passenger.status = "boarded"

        flight.boarded_passengers.append(finished_passenger_id)

        gate.try_start_boarding(
            self.current_time,
            self.schedule,
            self.passengers
        )

    def handle_flight_departure(self, event):
        flight_id = event.entity_id
        flight = self.flights[flight_id]

        flight.status = "departed"

        for passenger_id in flight.passengers:
            passenger = self.passengers[passenger_id]

            if passenger.status != "boarded":
                passenger.missed_flight = True
                passenger.status = "missed_flight"

        gate = self.gates[flight.gate_id]

        remaining_queue = deque()

        while gate.boarding_queue:
            pid = gate.boarding_queue.popleft()
            p = self.passengers[pid]

            if p.flight_id == flight_id:
                p.missed_flight = True
                p.status = "missed_flight"
            else:
                remaining_queue.append(pid)

        gate.boarding_queue = remaining_queue

    def compute_metrics(self):
        total_passengers = len(self.passengers)
        boarded = sum(1 for p in self.passengers.values() if p.status == "boarded")
        missed = sum(1 for p in self.passengers.values() if p.missed_flight)

        id_waits = (
            self.regular_id_queue.wait_times
            + self.precheck_id_queue.wait_times
            + self.clear_id_queue.wait_times
        )

        security_waits = []
        for lane in self.regular_security_area.lanes:
            security_waits.extend(lane.wait_times)

        for lane in self.precheck_security_area.lanes:
            security_waits.extend(lane.wait_times)

        boarding_waits = []
        total_system_times = []

        for passenger in self.passengers.values():
            if (
                passenger.boarding_queue_enter_time is not None
                and passenger.boarding_start_time is not None
            ):
                boarding_waits.append(
                    passenger.boarding_start_time - passenger.boarding_queue_enter_time
                )

            if (
                passenger.system_done_time is not None
                and passenger.airport_arrival_time is not None
            ):
                total_system_times.append(
                    passenger.system_done_time - passenger.airport_arrival_time
                )

        def avg(values):
            return sum(values) / len(values) if values else 0.0

        total_blocked_attempts = (self.regular_security_area.blocked_attempts + self.precheck_security_area.blocked_attempts)

        total_security_attempts = (self.regular_security_area.total_attempts + self.precheck_security_area.total_attempts)

        blocking_probability = (
            total_blocked_attempts / total_security_attempts
            if total_security_attempts > 0
            else 0.0
        )

        security_blocked_times = [
            p.security_blocked_time
            for p in self.passengers.values()
            if p.security_blocked_time > 0
        ]

        gate_arrival_buffers = []

        for passenger in self.passengers.values():
            if passenger.gate_arrival_time is not None:
                flight = self.flights[passenger.flight_id]
                gate_arrival_buffers.append(
                    flight.departure_time - passenger.gate_arrival_time
                )
        
        missed_status_counts = {}

        for passenger in self.passengers.values():
            if passenger.missed_flight:
                missed_status_counts[passenger.status] = missed_status_counts.get(passenger.status, 0) + 1

        return {
            "total_passengers": total_passengers,
            "boarded": boarded,
            "missed": missed,
            "average_id_wait": avg(id_waits),
            "average_security_wait": avg(security_waits),
            "average_boarding_wait": avg(boarding_waits),
            "average_total_system_time": avg(total_system_times),
            "security_blocking_probability": blocking_probability,
            "missed_rate": missed / total_passengers if total_passengers > 0 else 0.0,
            "average_security_blocked_time": avg(security_blocked_times),
            "max_security_blocked_time": max(security_blocked_times) if security_blocked_times else 0.0,
            "average_gate_arrival_buffer": avg(gate_arrival_buffers),
            "min_gate_arrival_buffer": min(gate_arrival_buffers) if gate_arrival_buffers else 0.0,
            "missed_status_counts": missed_status_counts,
        }


    def route_to_security(self, passenger_id):
        passenger = self.passengers[passenger_id]
        passenger.status = "security_queue"

        if passenger.has_precheck:
            self.precheck_security_area.enter_security(
                passenger_id,
                self.current_time,
                self.schedule,
                self.passengers
            )
        else:
            self.regular_security_area.enter_security(
                passenger_id,
                self.current_time,
                self.schedule,
                self.passengers
            )
    def log_system_state(self):
        regular_id_len = len(self.regular_id_queue.queue)
        precheck_id_len = len(self.precheck_id_queue.queue)
        clear_id_len = len(self.clear_id_queue.queue)

        regular_security_overflow = len(self.regular_security_area.overflow_queue)
        precheck_security_overflow = len(self.precheck_security_area.overflow_queue)

        regular_security_in_system = sum(
            lane.total_in_system()
            for lane in self.regular_security_area.lanes
        )

        precheck_security_in_system = sum(
            lane.total_in_system()
            for lane in self.precheck_security_area.lanes
        )

        boarding_queue_total = sum(
            len(gate.boarding_queue)
            for gate in self.gates.values()
        )

        passengers_in_airport = sum(
            1 for p in self.passengers.values()
            if p.status not in {"not_arrived", "boarded", "missed_flight"}
            and p.airport_arrival_time <= self.current_time
        )

        self.time_series.append({
            "time": self.current_time,
            "regular_id_queue": regular_id_len,
            "precheck_id_queue": precheck_id_len,
            "clear_id_queue": clear_id_len,
            "regular_security_overflow": regular_security_overflow,
            "precheck_security_overflow": precheck_security_overflow,
            "regular_security_in_system": regular_security_in_system,
            "precheck_security_in_system": precheck_security_in_system,
            "boarding_queue_total": boarding_queue_total,
            "passengers_in_airport": passengers_in_airport,
        })