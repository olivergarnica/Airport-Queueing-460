import matplotlib.pyplot as plt


def minutes_to_hour_label(minutes):
    hour = int(minutes // 60) % 24
    minute = int(minutes % 60)
    return f"{hour:02d}:{minute:02d}"


def plot_passengers_in_airport(time_series):
    times = [row["time"] for row in time_series]
    values = [row["passengers_in_airport"] for row in time_series]

    plt.figure()
    plt.plot(times, values)
    plt.xlabel("Time of day, minutes after midnight")
    plt.ylabel("Passengers in airport")
    plt.title("Passengers in Airport Over Time")
    plt.grid(True)
    plt.show()


def plot_id_queues(time_series):
    times = [row["time"] for row in time_series]

    plt.figure()
    plt.plot(times, [row["regular_id_queue"] for row in time_series], label="Regular ID")
    plt.plot(times, [row["precheck_id_queue"] for row in time_series], label="PreCheck ID")
    plt.plot(times, [row["clear_id_queue"] for row in time_series], label="CLEAR ID")

    plt.xlabel("Time of day, minutes after midnight")
    plt.ylabel("Queue length")
    plt.title("ID Queue Lengths Over Time")
    plt.legend()
    plt.grid(True)
    plt.show()


def plot_security_congestion(time_series):
    times = [row["time"] for row in time_series]

    plt.figure()
    plt.plot(times, [row["regular_security_overflow"] for row in time_series], label="Regular Overflow")
    plt.plot(times, [row["precheck_security_overflow"] for row in time_series], label="PreCheck Overflow")

    plt.xlabel("Time of day, minutes after midnight")
    plt.ylabel("Overflow queue length")
    plt.title("Security Overflow Queues Over Time")
    plt.legend()
    plt.grid(True)
    plt.show()


def plot_boarding_queue(time_series):
    times = [row["time"] for row in time_series]
    values = [row["boarding_queue_total"] for row in time_series]

    plt.figure()
    plt.plot(times, values)
    plt.xlabel("Time of day, minutes after midnight")
    plt.ylabel("Passengers waiting to board")
    plt.title("Total Boarding Queue Over Time")
    plt.grid(True)
    plt.show()