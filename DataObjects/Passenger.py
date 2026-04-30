class Passenger:
    def __init__(self, passenger_id, flight_id, gate_id, boarding_group, airport_arrival_time, has_precheck=False, has_clear=False):
        self.passenger_id = passenger_id
        self.flight_id = flight_id
        self.gate_id = gate_id
        self.boarding_group = boarding_group
        self.airport_arrival_time = airport_arrival_time
        self.has_precheck = has_precheck
        self.has_clear = has_clear

        self.tsa_queue_enter_time = None
        self.tsa_service_start_time = None
        self.tsa_service_end_time = None

        self.security_queue_enter_time = None
        self.security_service_start_time = None
        self.security_service_end_time = None
        self.security_blocked_time = 0.0
        self.security_overflow_enter_time = None

        self.gate_arrival_time = None

        self.boarding_queue_enter_time = None
        self.boarding_start_time = None
        self.boarding_end_time = None

        self.system_done_time = None
        self.missed_flight = False

        self.status = "not_arrived"