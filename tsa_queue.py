import random
import math
import matplotlib.pyplot as plt
from collections import deque

"""
Airport TSA queueing model
This script does two things:

1. Uses steady-state M/M/s formulas to estimate the minimum number
   of TSA agents needed in each time window to keep average total
   time in system below a target threshold.

2. Simulates an M/M/s queue with time-varying arrival rate lambda(t)
   to see how the queue evolves over multiple days.

Notation:
    lambda = arrival rate (passengers/hour)
    mu     = service rate per server (passengers/hour)
    s      = number of servers (agents)

Queue discipline:
    First-come, first-served (FCFS)
"""


# Random variable generation

def exponential(rate):
    """Generate an exponential random variable with parameter 'rate'."""
    if rate <= 0:
        raise ValueError("Rate must be positive.")
    return random.expovariate(rate)


# Time-varying arrival rate

def lambda_time(t):
    """
    Time-varying arrival rate lambda(t), measured in passengers/hour.
    t is measured in hours.
    We interpret t mod 24 as hour-of-day.
    """
    hour = t % 24

    if 6 <= hour < 9:
        return 22   # morning rush
    elif 9 <= hour < 12:
        return 18
    elif 12 <= hour < 16:
        return 14
    elif 16 <= hour < 19:
        return 20   # evening rush
    elif 19 <= hour < 22:
        return 12
    else:
        return 6    # late night


# Steady-state M/M/s analytic quantities

def utilization(lamb, mu, s):
    """
    Traffic intensity per server: rho = lambda / (s*mu)
    For stability in M/M/s, we need rho < 1.

    """
    return lamb / (s * mu)


def mms_pi0(lamb, mu, s):
    """
    Compute p0 = probability the M/M/s system is empty.
    Returns None if the system is unstable.
    """
    if lamb >= s * mu:
        return None

    a = lamb / mu

    total = sum((a ** n) / math.factorial(n) for n in range(s))
    total += (a ** s) / math.factorial(s) * (1 / (1 - a / s))

    return 1.0 / total


def mms_Lq(lamb, mu, s):
    """
    Average number of customers waiting in queue, Lq, for M/M/s.
    Returns infinity if unstable.
    """
    p0 = mms_pi0(lamb, mu, s)
    if p0 is None:
        return float("inf")

    a = lamb / mu
    rho = a / s

    return p0 * ((a ** s) / math.factorial(s)) * (rho / (1 - rho) ** 2)


def mms_avg_wait_queue(lamb, mu, s):
    """
    Average waiting time in queue, Wq, in hours.
    Returns infinity if unstable.
    """
    if lamb >= s * mu:
        return float("inf")

    Lq = mms_Lq(lamb, mu, s)
    return Lq / lamb


def mms_avg_time_in_system(lamb, mu, s):
    """
    Average total time in system, W, in hours.
    W = Wq + 1/mu
    """
    Wq = mms_avg_wait_queue(lamb, mu, s)
    if Wq == float("inf"):
        return float("inf")
    return Wq + 1 / mu


# Staffing calculation by time window

def required_servers_by_window(time_windows, mu, target_W, max_servers=50):
    """
    For each time window, find the minimum number of servers s
    such that average total time in system W < target_W.

    Returns a list of dictionaries.
    """
    results = []

    for label, lamb in time_windows:
        chosen = None

        for s in range(1, max_servers + 1):
            W = mms_avg_time_in_system(lamb, mu, s)
            if W < target_W:
                chosen = {
                    "label": label,
                    "lambda": lamb,
                    "s": s,
                    "W_hours": W,
                    "Wq_hours": mms_avg_wait_queue(lamb, mu, s),
                    "rho": utilization(lamb, mu, s),
                }
                break

        if chosen is None:
            chosen = {
                "label": label,
                "lambda": lamb,
                "s": None,
                "W_hours": float("inf"),
                "Wq_hours": float("inf"),
                "rho": None,
            }

        results.append(chosen)

    return results


# M/M/s simulation with time-varying λ(t)

def mms_queue_simulation(s, mu, max_time):
    """
    Simulate an M/M/s queue with time-varying arrival rate lambda_time(t).

    Parameters
    s : int Number of servers
    mu : float Service rate per server
    max_time : float Total simulation time in hours

    Returns
    dict containing:
        times              : event times
        system_sizes       : number in system after each event
        queue_sizes        : number waiting in queue after each event
        wait_in_queue      : waiting times in queue of completed customers
        time_in_system     : total times in system of completed customers
    """
    t = 0.0
    num_in_system = 0

    # Histories for plotting
    times = [0.0]
    system_sizes = [0]
    queue_sizes = [0]

    # Completed-customer statistics
    wait_in_queue = []
    time_in_system = []

    # FCFS waiting line: store arrival times of customers waiting for service
    queue = deque()

    # For each server:
    #   server_departure[i] = scheduled departure time if busy, else inf
    #   server_arrival[i]   = arrival time of customer currently being served
    #   service_start[i]    = time service started for that customer
    server_departure = [float("inf")] * s
    server_arrival = [None] * s
    service_start = [None] * s

    # First arrival
    next_arrival = exponential(lambda_time(0))

    def find_idle_server():
        """Return index of an idle server, or None if all are busy."""
        for i in range(s):
            if server_departure[i] == float("inf"):
                return i
        return None

    def next_departure_time():
        """Return the earliest scheduled departure time."""
        return min(server_departure)

    def departing_server():
        """Return the server index with the next departure."""
        return min(range(s), key=lambda i: server_departure[i])

    while True:
        next_departure = next_departure_time()
        next_event_time = min(next_arrival, next_departure)

        if next_event_time > max_time:
            break

        # Arrival event
        if next_arrival < next_departure:
            t = next_arrival
            num_in_system += 1

            idle = find_idle_server()

            if idle is not None:
                # Customer starts service immediately
                server_arrival[idle] = t
                service_start[idle] = t
                server_departure[idle] = t + exponential(mu)
            else:
                # Customer joins queue
                queue.append(t)

            # Schedule next arrival using current time-of-day rate
            next_arrival = t + exponential(lambda_time(t))

        # Departure event
        else:
            t = next_departure
            num_in_system -= 1

            i = departing_server()

            arrival_time = server_arrival[i]
            start_time = service_start[i]

            wait_in_queue.append(start_time - arrival_time)
            time_in_system.append(t - arrival_time)

            if queue:
                # Next waiting customer enters service immediately
                next_customer_arrival = queue.popleft()
                server_arrival[i] = next_customer_arrival
                service_start[i] = t
                server_departure[i] = t + exponential(mu)
            else:
                # Server becomes idle
                server_arrival[i] = None
                service_start[i] = None
                server_departure[i] = float("inf")

        times.append(t)
        system_sizes.append(num_in_system)
        queue_sizes.append(len(queue))

    return {
        "times": times,
        "system_sizes": system_sizes,
        "queue_sizes": queue_sizes,
        "wait_in_queue": wait_in_queue,
        "time_in_system": time_in_system,
    }


# Simulation summary

def summarize_simulation(results):
    """
    Compute summary statistics from simulation output.
    Times are reported in minutes where relevant.
    """
    system_sizes = results["system_sizes"]
    queue_sizes = results["queue_sizes"]
    wait_in_queue = results["wait_in_queue"]
    time_in_system = results["time_in_system"]

    avg_num_in_system = sum(system_sizes) / len(system_sizes) if system_sizes else 0.0
    avg_queue_length = sum(queue_sizes) / len(queue_sizes) if queue_sizes else 0.0
    avg_wait_queue = (sum(wait_in_queue) / len(wait_in_queue) * 60) if wait_in_queue else 0.0
    avg_time_system = (sum(time_in_system) / len(time_in_system) * 60) if time_in_system else 0.0

    return {
        "avg_num_in_system": avg_num_in_system,
        "avg_queue_length": avg_queue_length,
        "avg_wait_in_queue_min": avg_wait_queue,
        "avg_time_in_system_min": avg_time_system,
        "peak_system_size": max(system_sizes) if system_sizes else 0,
        "peak_queue_size": max(queue_sizes) if queue_sizes else 0,
        "customers_served": len(time_in_system),
    }


# Plotting
# Used claude because don't know matplotlib that well
def plot_results(sim_results, s, mu, max_time):
    """Plot system size and arrival-rate schedule."""
    times = sim_results["times"]
    system_sizes = sim_results["system_sizes"]

    fig, axes = plt.subplots(2, 1, figsize=(13, 8))

    # Top plot: number in system
    axes[0].step(times, system_sizes, where="post", linewidth=0.8, color="steelblue")
    axes[0].axhline(
        s,
        color="tomato",
        linestyle="--",
        linewidth=1.2,
        label=f"s = {s} servers"
    )
    axes[0].set_xlabel("Time (hours)")
    axes[0].set_ylabel("Passengers in system")
    axes[0].set_title(f"M/M/s TSA Queue Simulation (s={s}, μ={mu}/hr)")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Bottom plot: lambda(t) vs capacity
    hours = list(range(int(max_time) + 1))
    rates = [lambda_time(h) for h in hours]

    axes[1].step(hours, rates, where="post", linewidth=1.5, color="coral")
    axes[1].axhline(
        s * mu,
        color="green",
        linestyle="--",
        linewidth=1.2,
        label=f"Capacity = sμ = {s*mu}/hr"
    )
    axes[1].set_xlabel("Time (hours)")
    axes[1].set_ylabel("Arrival rate λ(t)")
    axes[1].set_title("Arrival rate schedule vs service capacity")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()


# Main script

def main():
    random.seed(460)

    mu = 10.0                    # passengers/hour/server
    target_W = 20 / 60           # target total time in system, in hours
    max_time = 72                # simulate 3 days

    time_windows = [
        ("Late night  (0-6)", 6),
        ("Morning rush (6-9)", 22),
        ("Mid-morning (9-12)", 18),
        ("Afternoon   (12-16)", 14),
        ("Evening rush(16-19)", 20),
        ("Evening     (19-22)", 12),
    ]

    # Analytic staffing estimates
    print(f"Service rate μ = {mu:.1f} passengers/hour per agent")
    print(f"Target total time in system W < {target_W*60:.0f} minutes\n")
    print(f"{'Period':<25} {'λ':>4} {'min s':>6} {'Wq (min)':>10} {'W (min)':>10} {'ρ':>8}")
    print("-" * 72)

    staffing_results = required_servers_by_window(time_windows, mu, target_W)
    required_s = []

    for row in staffing_results:
        label = row["label"]
        lamb = row["lambda"]
        s = row["s"]

        if s is None:
            print(f"{label:<25} {lamb:>4} {'--':>6} {'inf':>10} {'inf':>10} {'--':>8}")
        else:
            required_s.append(s)
            print(
                f"{label:<25} {lamb:>4} {s:>6} "
                f"{row['Wq_hours']*60:>9.2f}m "
                f"{row['W_hours']*60:>9.2f}m "
                f"{row['rho']:>8.3f}"
            )

    print("-" * 72)

    s_opt = max(required_s)
    print(f"\nPeak demand requires s = {s_opt} agents.")
    print("This is the smallest staffing level that keeps the")
    print("steady-state M/M/s average time in system below the target")
    print("in every time window.\n")

    # Simulation
    sim_results = mms_queue_simulation(s_opt, mu, max_time)
    summary = summarize_simulation(sim_results)

    print(f"Simulation results over {max_time:.0f} hours:")
    print(f"  Average number in system : {summary['avg_num_in_system']:.2f}")
    print(f"  Average queue length     : {summary['avg_queue_length']:.2f}")
    print(f"  Average wait in queue    : {summary['avg_wait_in_queue_min']:.2f} minutes")
    print(f"  Average time in system   : {summary['avg_time_in_system_min']:.2f} minutes")
    print(f"  Peak system size         : {summary['peak_system_size']}")
    print(f"  Peak queue size          : {summary['peak_queue_size']}")
    print(f"  Customers served         : {summary['customers_served']}")

    # Plot
    plot_results(sim_results, s_opt, mu, max_time)


if __name__ == "__main__":
    main()
