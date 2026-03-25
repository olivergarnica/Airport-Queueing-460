import random 
import matplotlib.pyplot as plt


def exponential(rate):
    # Generates an exponential random variable with parameter "rate"
    # In queueing:
    # if rate = lambda, this can model time between arrivals
    # if rate = mu, this can model a service time
    return random.expovariate(rate)

def mm1_queue(lamb, mu, max_time):
    # lamb = arrival rate (average number of arrivals per unit time)
    # mu   = service rate (average number served per unit time)
    # max_time = how long we run the simulation

    t = 0.0
    # current simulation time

    num_in_system = 0
    # number of customers currently in the system

    next_arrival = exponential(lamb)
    # first arrival happens after an exponential waiting time

    next_departure = float('inf')
    # initially there is nobody being served

    times = [0.0]
    # list of event times (for plotting)

    queue_lengths = [0]
    # records how many people are in the system after each event

    arrival_times_in_queue = []
    # stores the arrival times of customers currently in the system
    # the first person in this list is the one who has been waiting longest

    waiting_times = []
    # this will store each customer's total time in system:
    # from arrival until departure

    while t < max_time:
        if next_arrival < next_departure:
            # the next event is an arrival, since it happens before the next departure

            t = next_arrival
            # move the simulation clock forward to the arrival time

            num_in_system += 1
            # one more customer is now in the system

            arrival_times_in_queue.append(t)
            # record this customer's arrival time

            if num_in_system == 1:
                # if the system was empty before this arrival,
                # this customer starts service immediately

                next_departure = t + exponential(mu)
                # schedule this customer's departure:
                # current time + random service time

            next_arrival = t + exponential(lamb)
            # schedule the next arrival:
            # current time + random interarrival time

        else:
            # the next event is a departure

            t = next_departure
            # move the simulation clock forward to the departure time

            num_in_system -= 1
            # one customer leaves the system

            arrival_time = arrival_times_in_queue.pop(0)
            # remove the customer who arrived earliest
            # this is FCFS = first come, first served

            waiting_times.append(t - arrival_time)
            # total time in system for this customer:
            # departure time - arrival time

            if num_in_system > 0:
                # if people are still in the system,
                # the next one starts service immediately

                next_departure = t + exponential(mu)
                # schedule the next departure

            else:
                # if the system is empty, there is no one to serve

                next_departure = float('inf')
                # so we set departure time to infinity again

        times.append(t)
        # record the time of this event

        queue_lengths.append(num_in_system)
        # record the number in system after this event

    return times, queue_lengths, waiting_times


lamb = 2.0
mu = 3.0
max_time = 50
times, queue_lengths, waiting_times = mm1_queue(lamb, mu, max_time)

print("Average number in system:", sum(queue_lengths) / len(queue_lengths))
# rough empirical average of number of customers in system
print("Average time in system:", sum(waiting_times) / len(waiting_times))
# rough empirical average of customer time in system
plt.step(times, queue_lengths, where="post")
plt.xlabel("Time")
plt.ylabel("Number in system")
plt.title("M/M/1 Check-in Counter Queue")
plt.show()