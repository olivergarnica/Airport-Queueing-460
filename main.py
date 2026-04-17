import random
import math
import matplotlib.pyplot as plt

def exponential(rate):
# Generates an exponential random variable with parameter "rate"
    return random.expovariate(rate)

def lambda_time(t):
    """
    Time-varying arrival rate based on hour of day (airport schedule).
    Values estimated from TSA national data scaled to a single airport lane.
    """
    hour = t % 24
    if   6 <= hour <  9: return 22   # morning rush
    elif 9 <= hour < 12: return 18
    elif 12 <= hour < 16: return 14
    elif 16 <= hour < 19: return 20   # evening rush
    elif 19 <= hour < 22: return 12
    else:                 return 6    # late night

# Analytical M/M/s steady-state solution

def mms_pi0(lamb, mu, s):
    """Compute pi_0 for M/M/s queue. Returns None if unstable."""
    rho = lamb / mu
    if lamb >= s * mu:
        return None  # unstable
    # sum_{i=0}^{s-1} (rho^i / i!) + (rho^s / s!) * 1/(1 - rho/s)
    total = sum((rho**i) / math.factorial(i) for i in range(s))
    total += (rho**s / math.factorial(s)) * (1 / (1 - rho / s))
    return 1.0 / total

def mms_avg_wait(lamb, mu, s):
    """
    Returns average total time in system W (hours) for M/M/s queue.
    Uses textbook stationary distribution formulas.
    Returns float('inf') if unstable.
    """
    pi0 = mms_pi0(lamb, mu, s)
    if pi0 is None:
        return float('inf')

    rho = lamb / mu

    # Lq = average number of passengers WAITING (not yet being served). 
    # From Adeke (2018) eq. 25
    Lq = pi0 * (rho**s / math.factorial(s)) * (rho / s) / (1 - rho / s)**2
    
    # C = average TOTAL number of passengers in system
    # (waiting + being served). From Adeke (2018) eq. 26
    C  = Lq + rho
    
    # Compute W = average total time in system via Little's Law
    # From Allen & Allen p.260:
    W  = C / lamb
    return W

mu          = 10.0          # agents process ~10 passengers/hour each
target_W    = 20 / 60       # 20 minutes in hours
time_windows = [
    ("Late night  (0-6)",   6),
    ("Morning rush (6-9)",  22),
    ("Mid-morning (9-12)",  18),
    ("Afternoon  (12-16)",  14),
    ("Evening rush(16-19)", 20),
    ("Evening     (19-22)", 12),
]

print(f"Service rate μ = {mu} passengers/hour per agent")
print(f"Target W < {target_W*60:.0f} minutes\n")
print(f"{'Period':<25} {'λ':>4}  {'min s':>6}  {'W (min)':>9}  {'ρ per agent':>12}")
print("─" * 65)

required_s = []
for label, lamb in time_windows:
    for s in range(1, 50):
        W = mms_avg_wait(lamb, mu, s)
        if W < target_W:
            required_s.append(s)
            print(f"{label:<25} {lamb:>4}  {s:>6}  {W*60:>8.2f}m  {lamb/(s*mu):>11.3f}")
            break

print("─" * 65)
print(f"\n Peak demand requires s = {max(required_s)} agents (morning rush, λ=22)")
print(f" This keeps W < 20 min in ALL time windows.")

def mms_queue(s, mu, max_time): 
    """
    M/M/s simulation with time-varying lambda_time(t).
    s   = number of servers
    mu  = per-server service rate
    """
    t = 0.0   # current simulation time
    num_in_system = 0   # number of customers currently in the system
    arrival_times_in_queue = []   # stores the arrival times of customers currently in the system the first person in this list is the one who has been waiting longest
    waiting_times = [] # this will store each customer's total time in system: from arrival until departure
    times = [0.0]   # list of event times (for plotting)
    queue_lengths = [0]   # records how many people are in the system after each event
    next_arrival = exponential(lambda_time(0))

    # Each server tracks when it becomes free (float('inf') = idle)
    # Create a list of s agents, all starting idle (free at t=0)
    server_free_at = [0.0] * s
    # Next departure = min over busy servers
    def next_dep_time():
        busy = [ft for ft in server_free_at if ft > t]
        return min(busy) if busy else float('inf')
    next_departure = next_dep_time()
    while t < max_time:
        if next_arrival < next_departure:   # the next event is an arrival, since it happens before the next departure
            t = next_arrival   # move the simulation clock forward to the arrival time
            num_in_system += 1   # one more customer is now in the system
            arrival_times_in_queue.append(t)   # record this customer's arrival time         
            # Assign to the earliest-free server if one is idle
            idle = [i for i, ft in enumerate(server_free_at) if ft <= t]
            if idle:
                agent = min(idle, key=lambda i: server_free_at[i])
                server_free_at[agent] = t + exponential(mu)

            next_arrival    = t + exponential(lambda_time(t))
            next_departure  = next_dep_time()         
        else: # the next event is a departure
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
            # Find which server just finished
            finishing = min(range(s), key=lambda i: abs(server_free_at[i] - t))
            # If queue has waiting customers, assign the freed server
            if num_in_system >= s:
                server_free_at[finishing] = t + exponential(mu)
            else:
                server_free_at[finishing] = 0.0   # mark idle

            next_departure = next_dep_time()                
        times.append(t)
        # record the time of this event
        queue_lengths.append(num_in_system)
        # record the number in system after this event
    return times, queue_lengths, waiting_times

# Run simulation with the recommended number of agents
s_opt   = max(required_s)
max_time = 72   # 3 days

times, queue_lengths, waiting_times = mms_queue(s_opt, mu, max_time)

avg_W   = sum(waiting_times) / len(waiting_times) * 60
avg_C   = sum(queue_lengths) / len(queue_lengths)
peak_Q  = max(queue_lengths)

print(f"\n── Simulation results (s={s_opt} agents, 3 days) ──")
print(f"  Avg time in system : {avg_W:.2f} minutes")
print(f"  Avg queue length   : {avg_C:.2f}")
print(f"  Peak queue length  : {peak_Q}")
print(f"  Customers served   : {len(waiting_times)}")

# Plot
fig, axes = plt.subplots(2, 1, figsize=(13, 7))

axes[0].step(times, queue_lengths, where="post", linewidth=0.7, color="steelblue")
axes[0].axhline(s_opt, color="tomato", linestyle="--", linewidth=1,
                label=f"s={s_opt} agents (all busy = queue forming)")
axes[0].set_xlabel("Time (hours)")
axes[0].set_ylabel("Passengers in system")
axes[0].set_title(f"M/M/s TSA Queue — s={s_opt} agents, μ={mu}/hr, time-varying λ(t)")
axes[0].legend()

# Arrival rate schedule
hours = list(range(73))
rates = [lambda_time(h) for h in hours]
axes[1].step(hours, rates, where="post", color="coral", linewidth=1.5)
axes[1].axhline(s_opt * mu, color="green", linestyle="--", linewidth=1,
                label=f"Max throughput = s·μ = {s_opt*mu}/hr")
axes[1].set_xlabel("Hour")
axes[1].set_ylabel("λ(t) — arrivals/hour")
axes[1].set_title("Arrival rate schedule vs total service capacity")
axes[1].legend()

plt.tight_layout()
plt.show()