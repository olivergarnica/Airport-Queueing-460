import random
import math
import matplotlib.pyplot as plt

random.seed(42)

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
        return float('inf'), float('inf')

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

    # Wq = time spent just waiting in line before service begins
    # From Adeke (2018) eq. 22: Wq = Lq / lamb
    Wq = Lq / lamb

    return W, Wq

def mms_queue(s, mu, max_time): 
    """
    M/M/s simulation with time-varying lambda_time(t).
    s   = number of servers
    mu  = per-server service rate
    """
    t = 0.0 
    num_in_system = 0 
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

scenarios = [
    {"mu": 10.0, "label": "mu=10 (slow)",   "color": "tomato"},
    {"mu": 15.0, "label": "mu=15 (medium)", "color": "steelblue"},
    {"mu": 20.0, "label": "mu=20 (fast)",   "color": "seagreen"},
]

target_W = 20 / 60
max_time = 72  # 3 days

time_windows = [
    ("Late night  (0-6)",    6),
    ("Morning rush (6-9)",  22),
    ("Mid-morning (9-12)",  18),
    ("Afternoon  (12-16)",  14),
    ("Evening rush(16-19)", 20),
    ("Evening     (19-22)", 12),
]

# Analytical tables for all three mu values
for scenario in scenarios:
    mu = scenario["mu"]
    print(f"Service rate mu = {mu} passengers/hour per agent")
    print(f"Target W < {target_W*60:.0f} minutes")
    print(f"{'Period':<25} {'λ':>4}  {'min s':>6}  {'W (min)':>9}  {'Wq (min)':>9}  {'ρ per agent':>12}")
    print("─" * 75)

    required_s = []
    for label, lamb in time_windows:
        for s in range(1, 50):
            W, Wq = mms_avg_wait(lamb, mu, s)
            if W < target_W:
                required_s.append(s)
                print(f"{label:<25} {lamb:>4}  {s:>6}  "
                      f"{W*60:>8.2f}m  {Wq*60:>8.2f}m  {lamb/(s*mu):>11.3f}")
                break
    s_opt = max(required_s)
    print(f"Peak demand requires s = {s_opt} agents (morning rush, λ=22)")
    print(f"   This keeps W < 20 min in ALL time windows.\n")

    scenario["s_opt"] = s_opt

# Simulation for all three scenarios

print("── Simulation results (3 days) ──────────────────────────────────")
print(f"{'Scenario':<15} {'s':>4}  {'Avg W':>10}  {'Avg Wq':>10}  {'Peak Q':>8}  {'Served':>8}")
print("─" * 65)

for scenario in scenarios:
    mu    = scenario["mu"]
    s_opt = scenario["s_opt"]

    times, queue_lengths, waiting_times = mms_queue(s_opt, mu, max_time)

    avg_W  = sum(waiting_times) / len(waiting_times) * 60
    # Wq from simulation = avg W - avg service time (1/mu in hours → minutes)
    avg_Wq = avg_W - (1/mu * 60)
    avg_C  = sum(queue_lengths) / len(queue_lengths)
    peak_Q = max(queue_lengths)

    print(f"{scenario['label']:<15} {s_opt:>4}  {avg_W:>9.2f}m  "
          f"{avg_Wq:>9.2f}m  {peak_Q:>8}  {len(waiting_times):>8}")

    # store for plotting
    scenario["times"]         = times
    scenario["queue_lengths"] = queue_lengths
    scenario["avg_W"]         = avg_W
    scenario["avg_Wq"]        = avg_Wq
    scenario["peak_Q"]        = peak_Q

# Plot 1: Queue lengths for all three scenarios

fig1, axes1 = plt.subplots(3, 1, figsize=(13, 10))

for i, scenario in enumerate(scenarios):
    mu            = scenario["mu"]
    s_opt         = scenario["s_opt"]
    times         = scenario["times"]
    queue_lengths = scenario["queue_lengths"]
    color         = scenario["color"]
    label         = scenario["label"]
    avg_W         = scenario["avg_W"]
    avg_Wq        = scenario["avg_Wq"]

    axes1[i].step(times, queue_lengths, where="post", linewidth=0.7, color=color)
    axes1[i].axhline(s_opt, color="tomato", linestyle="--", linewidth=1, 
                     label=f"s={s_opt} agents (queue forming above line)")
    axes1[i].set_xlabel("Time (hours)")
    axes1[i].set_ylabel("Passengers in system")
    axes1[i].set_title(f"{label} — s={s_opt}, avg W={avg_W:.2f} min, avg Wq={avg_Wq:.2f} min")
    axes1[i].legend(fontsize=9)
    axes1[i].set_ylim(0, 13)

fig1.suptitle("M/M/s TSA Queue — Queue length over 3 days (mu = 10, 15, 20)", 
              fontsize=13, fontweight="bold")
plt.tight_layout()
plt.show()

# Plot 2: Summary comparison bar chart

fig2, axes2 = plt.subplots(1, 3, figsize=(13, 5))

labels     = [s["label"] for s in scenarios]
avg_Ws     = [s["avg_W"] for s in scenarios]
avg_Wqs    = [s["avg_Wq"] for s in scenarios]
peak_Qs    = [s["peak_Q"] for s in scenarios]
s_opts     = [s["s_opt"] for s in scenarios]
colors     = [s["color"] for s in scenarios]

# Left: avg W comparison
axes2[0].bar(labels, avg_Ws, color=colors, edgecolor="black", linewidth=0.5)
axes2[0].axhline(20, color="red", linestyle="--", linewidth=1, label="20 min target")
axes2[0].set_ylabel("Minutes")
axes2[0].set_title("Avg time in system (W)")
axes2[0].legend(fontsize=8)

# Middle: avg Wq comparison
axes2[1].bar(labels, avg_Wqs, color=colors, edgecolor="black", linewidth=0.5)
axes2[1].set_ylabel("Minutes")
axes2[1].set_title("Avg wait in queue (Wq)")

# Right: agents required
axes2[2].bar(labels, s_opts, color=colors, edgecolor="black", linewidth=0.5)
axes2[2].set_ylabel("Number of agents")
axes2[2].set_title("Agents required (s)")
axes2[2].set_yticks([1, 2, 3])

fig2.suptitle("Scenario comparison — mu = 10, 15, 20",
              fontsize=13, fontweight="bold")
plt.tight_layout()
plt.show()