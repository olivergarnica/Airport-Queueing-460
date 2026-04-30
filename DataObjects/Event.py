class Event():
    def __init__(self, time, event_type, entity_id=None, data=None):
        self.time = time
        self.event_type = event_type
        self.entity_id = entity_id
        self.data = data or {}

    def __lt__(self, other):
        return self.time < other.time