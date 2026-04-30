import heapq

class Schedule:
    def __init__(self):
        self.event_queue = []

    def add_event(self, event):
        heapq.heappush(self.event_queue, event)

    def next_event(self):
        return heapq.heappop(self.event_queue)

    def has_events(self):
        return len(self.event_queue) > 0

    def __len__(self):
        return len(self.event_queue)  