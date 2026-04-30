class Flight:
    def __init__(self, flight_id, gate_id, departure_time, capacity, num_groups):
        self.flight_id = flight_id
        self.gate_id = gate_id
        self.departure_time = departure_time
        self.capacity = capacity
        self.num_groups = num_groups

        self.boarding_open_time = departure_time - 40

        self.passengers = []
        self.boarded_passengers = []

        self.current_boarding_group = None
        self.status = "scheduled"