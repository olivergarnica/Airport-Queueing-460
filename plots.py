import random
import matplotlib.pyplot as plt
from queue import (
    lambda_time,
    mms_avg_time_in_system,
    mms_avg_wait_queue,
    mms_queue_simulation,
    summarize_simulation,
    required_servers_by_window,
)

random.seed(42)

# Setup 
target_W = 20 / 60
max_time = 72

time_windows = [
    ("Late night  (0-6)",    6),
    ("Morning rush (6-9)",  22),
    ("Mid-morning (9-12)",  18),
    ("Afternoon  (12-16)",  14),
    ("Evening rush(16-19)", 20),
    ("Evening     (19-22)", 12),
]

scenarios = [
    {"mu": 10.0, "label": "μ=10 (slow)",   "color": "tomato"},
    {"mu": 15.0, "label": "μ=15 (medium)", "color": "steelblue"},
    {"mu": 20.0, "label": "μ=20 (fast)",   "color": "seagreen"},
]

# Run all three scenarios 
for scenario in scenarios:
    mu = scenario["mu"]

    # find minimum s for this mu
    staffing = required_servers_by_window(time_windows, mu, target_W)
    s_opt = max(row["s"] for row in staffing if row["s"] is not None)
    scenario["s_opt"] = s_opt

    # run simulation
    sim = mms_queue_simulation(s_opt, mu, max_time)
    summary = summarize_simulation(sim)

    scenario["times"]         = sim["times"]
    scenario["system_sizes"]  = sim["system_sizes"]
    scenario["queue_sizes"]   = sim["queue_sizes"]
    scenario["avg_W"]         = summary["avg_time_in_system_min"]
    scenario["avg_Wq"]        = summary["avg_wait_in_queue_min"]
    scenario["peak_Q"]        = summary["peak_system_size"]
    scenario["served"]        = summary["customers_served"]

# Figure 1: Queue length over 3 days 
fig1, axes1 = plt.subplots(3, 1, figsize=(13, 10))

for i, scenario in enumerate(scenarios):
    s_opt  = scenario["s_opt"]
    times  = scenario["times"]
    sizes  = scenario["system_sizes"]
    color  = scenario["color"]
    label  = scenario["label"]
    avg_W  = scenario["avg_W"]
    avg_Wq = scenario["avg_Wq"]

    axes1[i].step(times, sizes, where="post", linewidth=0.7, color=color)
    axes1[i].axhline(s_opt, color="tomato", linestyle="--", linewidth=1,
                     label=f"s={s_opt} agents (queue forming above line)")
    axes1[i].set_xlabel("Time (hours)")
    axes1[i].set_ylabel("Passengers in system")
    axes1[i].set_title(
        f"{label} — s={s_opt}, avg W={avg_W:.2f} min, avg Wq={avg_Wq:.2f} min"
    )
    axes1[i].legend(fontsize=9)
    axes1[i].set_ylim(0, 13)

fig1.suptitle("M/M/s TSA Queue — Queue length over 3 days (μ = 10, 15, 20)",
              fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig("tsa_queue_lengths.png", dpi=150)
plt.show()

# Figure 2: Summary bar chart 
fig2, axes2 = plt.subplots(1, 3, figsize=(13, 5))

labels  = [s["label"]  for s in scenarios]
avg_Ws  = [s["avg_W"]  for s in scenarios]
avg_Wqs = [s["avg_Wq"] for s in scenarios]
s_opts  = [s["s_opt"]  for s in scenarios]
colors  = [s["color"]  for s in scenarios]

axes2[0].bar(labels, avg_Ws, color=colors, edgecolor="black", linewidth=0.5)
axes2[0].axhline(20, color="red", linestyle="--", linewidth=1, label="20 min target")
axes2[0].set_ylabel("Minutes")
axes2[0].set_title("Avg time in system (W)")
axes2[0].legend(fontsize=8)

axes2[1].bar(labels, avg_Wqs, color=colors, edgecolor="black", linewidth=0.5)
axes2[1].set_ylabel("Minutes")
axes2[1].set_title("Avg wait in queue (Wq)")

axes2[2].bar(labels, s_opts, color=colors, edgecolor="black", linewidth=0.5)
axes2[2].set_ylabel("Number of agents")
axes2[2].set_title("Agents required (s)")
axes2[2].set_yticks([1, 2, 3])

fig2.suptitle("Scenario comparison — μ = 10, 15, 20",
              fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig("tsa_scenario_comparison.png", dpi=150)
plt.show()
