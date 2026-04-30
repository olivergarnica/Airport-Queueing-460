from Airport import Airport
import random
import matplotlib.pyplot as plt


def run_one_day(seed=None):
    if seed is not None:
        random.seed(seed)

    airport_gates = 10

    airport = Airport(
        num_gates=airport_gates,

        regular_id_servers=6,
        precheck_id_servers=1,
        clear_id_servers=1,

        id_service_rate=1 / 0.5,
        precheck_service_rate=1 / 0.50,
        clear_service_rate=1 / 0.35,

        num_regular_security_lanes=5,
        regular_security_service_rate=1 / 0.5,
        regular_security_capacity=12,

        num_precheck_security_lanes=2,
        precheck_security_service_rate=1 / 0.5,
        precheck_security_capacity=10,

        boarding_service_rate=1 / 0.20
    )

    airport.seed_flights(
        num_flights=random.randint(airport_gates * 6, airport_gates * 8),
        start_time=180,
        end_time=1440
    )

    airport.run(max_time=1500)

    return airport.compute_metrics()


def main():
    num_days = 50
    results = []

    for seed in range(num_days):
        metrics = run_one_day(seed=seed)
        results.append(metrics)

    missed_values = [r["missed"] for r in results]
    missed_rates = [r["missed_rate"] for r in results]
    security_waits = [r["average_security_wait"] for r in results]
    boarding_waits = [r["average_boarding_wait"] for r in results]
    id_waits = [r["average_id_wait"] for r in results]

    def avg(xs):
        return sum(xs) / len(xs)

    def std(xs):
        mean = avg(xs)
        return (sum((x - mean) ** 2 for x in xs) / (len(xs) - 1)) ** 0.5

    print("\nMonte Carlo Airport Results")
    print("---------------------------")
    print(f"days simulated: {num_days}")
    print(f"average missed: {avg(missed_values)}")
    print(f"std missed: {std(missed_values)}")
    print(f"min missed: {min(missed_values)}")
    print(f"max missed: {max(missed_values)}")
    print(f"average missed rate: {avg(missed_rates)}")
    print(f"average ID wait: {avg(id_waits)}")
    print(f"average security wait: {avg(security_waits)}")
    print(f"average boarding wait: {avg(boarding_waits)}")

    plt.figure()
    plt.hist(missed_values, bins=15)
    plt.xlabel("Missed passengers per day")
    plt.ylabel("Frequency")
    plt.title("Distribution of Missed Passengers Across Simulated Days")
    plt.grid(True)
    plt.show()

    plt.figure()
    plt.scatter(security_waits, missed_values)
    plt.xlabel("Average security wait")
    plt.ylabel("Missed passengers")
    plt.title("Security Wait vs Missed Passengers")
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    main()